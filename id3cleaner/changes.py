'''ID3 Change Types'''
from pathlib import Path
import hashlib
import re
from eyed3.mp3 import Mp3AudioFile
import humanize
from id3cleaner import id3_fmt
from id3cleaner.errors import ID3CleanerArgumentContradictionError, ID3CleanerError


class ID3Change():
    '''Superclass for all ID3 Changes.'''
    _field = None

    @property
    def field(self):
        '''The name of the field being manipulated.'''
        return self._field

    def __init__(self, field: str):
        self._field = field

    def get_current_value(self, id3file: Mp3AudioFile) -> object:
        '''Returns the field this value currently has.'''
        return getattr(id3file.tag, self.field)

    def get_new_value(self, id3file: Mp3AudioFile) -> object:
        '''Returns the new value this field will have.'''
        raise NotImplementedError()

    def needs_change(self, id3file: Mp3AudioFile) -> bool:
        '''
        Returns Whether or not this change spec will perform a change on the
        file.
        '''
        current = self.get_current_value(id3file)
        new = self.get_new_value(id3file)
        return current != new

    def change_str(self, id3file: Mp3AudioFile) -> str:
        '''
        String representing the change to be made.
        Returns an empty string if there is no change.
        '''
        if not self.needs_change(id3file):
            return ''
        old_value = self.get_current_value(id3file)
        new_value = self.get_new_value(id3file)
        return f'{self.field}: "{old_value}" -> "{new_value}"'

    def apply_change(self, id3file: Mp3AudioFile) -> str:
        '''Apply the given change.'''
        change_repr = self.change_str(id3file)
        if change_repr:
            new_value = self.get_new_value(id3file)
            setattr(id3file.tag, self._field, new_value)
        return change_repr


class SimpleID3Change(ID3Change):
    '''This handles changes for most id3 tags use cases.'''

    def __init__(self, field: str, transformer: object, needs_change=None):
        super().__init__(field)
        self.transformer = transformer
        if needs_change:
            self.needs_change = needs_change

    def get_new_value(self, id3file):
        return self.transformer(self.get_current_value(id3file))


class ComplexID3Change(ID3Change):
    '''An id3 change defined by arbitrary logic.'''

    def __init__(self, field: str, transformer: object, needs_change=None):
        super().__init__(field)
        self.transformer = transformer
        if needs_change:
            self.needs_change = needs_change

    def get_new_value(self, id3file):
        return self.transformer(id3file)


class SimpleFrameID3Change(SimpleID3Change):
    '''
    An ID3 frame change which can be expressed purely as string replacement.
    '''

    def get_current_value(self, id3file):
        return self.get_frame_repr(id3file)

    def get_frame_repr(self, id3file: Mp3AudioFile):
        '''Get the current frames'''
        rep = {
            frame.description:
            {
                item: getattr(frame, item)
                for item in ('lang', 'text')
            }
            for frame in getattr(id3file.tag, self.field)
        }
        return rep

    def put_frames(self, id3file: Mp3AudioFile, frame_repr: dict):
        '''Create the configured frames.'''
        frame_ctrl = getattr(id3file.tag, self.field)
        for desc, frame in frame_repr.items():
            found_frame = frame_ctrl.get(desc)
            if not found_frame:
                frame_ctrl.set(frame['text'], desc)
                found_frame = frame_ctrl.get(desc)
            for key, value in frame.items():
                setattr(found_frame, key, value)

    def apply_change(self, id3file):
        change_repr = self.change_str(id3file)
        if change_repr:
            self.put_frames(id3file, self.get_new_value(id3file))
        return change_repr


class ComplexFrameID3Change(SimpleFrameID3Change):
    '''
    A ComplexID3Change which is special-purpose for dealing with frame objects
    like comments and lyrics.
    '''

    def __init__(self, field: str, transformer: object):
        super().__init__(field, transformer)
        self.transformer = transformer

    def get_current_value(self, id3file):
        return self.get_frame_repr(id3file)

    def get_new_value(self, id3file):
        return self.transformer(id3file)


class ImageID3Change(ID3Change):
    '''A change to the associated image.'''

    def __init__(self, field: str, transformer: object):
        super().__init__(field if field else 'images')
        self.transformer = transformer

    def get_current_value(self, id3file):
        return id3file.tag.images[0].image_data

    def get_new_value(self, id3file):
        return self.transformer(id3file)

    def change_str(self, id3file: Mp3AudioFile) -> str:
        if not self.needs_change(id3file):
            return ''

        current_picture = self.get_current_value(id3file)
        new_picture = self.get_new_value(id3file)

        old_size = humanize.naturalsize(len(current_picture))
        old_hash = hashlib.sha1(current_picture).hexdigest()
        new_size = humanize.naturalsize(len(new_picture))
        new_hash = hashlib.sha1(new_picture).hexdigest()

        return f'{self.field}: "{old_hash} ({old_size})" -> "{new_hash} ({new_size})"'

    def apply_change(self, id3file):
        change_repr = self.change_str(id3file)
        if change_repr:
            new_value = self.get_new_value(id3file)
            id3file.tag.images[0].image_data = new_value
        return change_repr


class ID3ChangeChain(ID3Change):
    '''Manages a series of changes to a given field, made in order.'''

    def __init__(self, field):
        super().__init__(field)
        self.sub_changes = []

    def add(self, change: ID3Change):
        '''Add a change to the chain.'''
        if change.field != self.field:
            raise ID3CleanerArgumentContradictionError(
                f'Found mismatched change field {change.field} in change chain '
                f'of type {self.field}')
        # This feeds the output of each step of the chain into the next step as we build the chain.
        if self.sub_changes:
            prevchange = self.sub_changes[-1]
            change.get_current_value = prevchange.get_new_value
        self.sub_changes.append(change)

    def get_current_value(self, id3file):
        return self.sub_changes[0].get_current_value(id3file)

    def get_new_value(self, id3file):
        return self.sub_changes[-1].get_new_value(id3file)

    def change_str(self, id3file):
        return '\n'.join(item.change_str(id3file) for item in self.sub_changes)

    def apply_change(self, id3file):
        return '\n'.join(item.apply_change(id3file) for item in self.sub_changes)


class ChangeProfile():
    '''A group of changes to all be carried out.'''
    change_def: dict = {}

    def __init__(self, changes: 'list[ID3Change]' = None):
        changes = changes or []
        for change in changes:
            self.add_change(change)

    def add_change(self, change: ID3Change):
        '''Adds a change to the list of changes to be made.'''
        if change.field not in self.change_def:
            self.change_def[change.field] = ID3ChangeChain(change.field)
        self.change_def[change.field].add(change)

    def check(self):
        '''
        Checks for any invalid configurations, and raises an exception if there
        are any.
        '''
        contradictions = [
            f'Change registered under {key}, but change has field ID {value.field}'
            for key, value in self.change_def.items()
            if key != value.field
        ]
        if any(contradictions):
            raise ID3CleanerArgumentContradictionError(
                contradictions.join('\n'))

    def needs_change(self, id3file: Mp3AudioFile):
        '''Whether any changes would be made by this profile.'''
        return any(c.needs_change(id3file) for c in self.change_def.values())

    def whatif(self, id3file: Mp3AudioFile) -> list:
        '''
        Simulates applying all of the changes, returning a list of change
        strings.
        '''
        return [
            c.change_str(id3file)
            for c in self.change_def.values() if c.needs_change(id3file)
        ]

    def apply(self, id3file: Mp3AudioFile):
        '''Applies all of the specified changes.'''
        return [
            c.apply_change(id3file)
            for c in self.change_def.values() if c.needs_change(id3file)
        ]


class SimpleRenameChange(ID3Change):
    '''Rename the ID3 file'''
    _PATH_SANITIZATION_REGEX = re.compile(r'[/\\;#%{}<>*?+`|=]')

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        '''Remove illegal characters from the filename'''
        result = filename.strip().rstrip('.')
        result = SimpleRenameChange._PATH_SANITIZATION_REGEX.sub('_', filename)
        return result

    def __init__(self, rename_spec: str, force_rename: bool = False):
        self.rename_spec = rename_spec
        self.force_rename = force_rename

        super().__init__('path')

    def get_current_value(self, id3file: Mp3AudioFile) -> Path:
        return Path(id3file.path).resolve()

    def get_new_value(self, id3file: Mp3AudioFile) -> Path:
        current = self.get_current_value(id3file)
        ext = current.suffix
        parent_directory = current.parent

        target_stem = id3_fmt.id3_fmt(self.rename_spec, id3file)
        target_stem = self.sanitize_filename(target_stem)
        if not target_stem:
            raise ID3CleanerError(
                f"Error: Tried to build rename target for {current} using "
                f"format string {self.rename_spec}, but got no result!"
            )
        target_name = f'{target_stem}{ext}'

        target_path = parent_directory.joinpath(target_name)
        return target_path.resolve()

    def apply_change(self, id3file: Mp3AudioFile) -> str:
        change_str = self.change_str(id3file)
        if change_str:
            current = self.get_current_value(id3file)
            target = self.get_new_value(id3file)
            if target.exists() and not self.force_rename:
                raise ID3CleanerError(
                    f'Tried to rename {current} to {target}, but {target} already exists!')
            current.rename(target)
        return change_str
