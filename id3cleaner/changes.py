from eyed3.mp3 import Mp3AudioFile
from id3cleaner.errors import ID3CleanerArgumentContradictionError


class ID3Change():
    _field = None

    @property
    def field(self):
        return self._field

    def __init__(self, field: str):
        self._field = field

    def get_current_value(self, id3file: Mp3AudioFile) -> object:
        return getattr(id3file.tag, self.field)

    def get_new_value(self, id3file: Mp3AudioFile) -> object:
        raise NotImplementedError()

    def needs_change(self, id3file: Mp3AudioFile) -> bool:
        current = self.get_current_value(id3file)
        new = self.get_new_value(id3file)
        return current != new

    def change_str(self, id3file: Mp3AudioFile) -> str:
        if not self.needs_change(id3file):
            return ''
        old_value = self.get_current_value(id3file)
        new_value = self.get_new_value(id3file)
        return f'{self.field}: "{old_value}" -> "{new_value}"'

    def apply_change(self, id3file: Mp3AudioFile) -> str:
        change_str = self.change_str(id3file)
        if self.change_str:
            new_value = self.get_new_value(id3file)
            setattr(id3file.tag, self._field, new_value)
        return change_str


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
    def __init__(self, field: str, transformer: object, needs_change=None):
        super().__init__(field)
        self.transformer = transformer
        if needs_change:
            self.needs_change = needs_change

    def get_new_value(self, id3file):
        return self.transformer(id3file)


class SimpleFrameID3Change(SimpleID3Change):
    def get_current_value(self, id3file):
        return self.get_frame_repr(id3file)

    def get_frame_repr(self, id3file: Mp3AudioFile):
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
        frame_ctrl = getattr(id3file.tag, self.field)
        for desc, frame in frame_repr.items():
            found_frame = frame_ctrl.get(desc)
            if not found_frame:
                frame_ctrl.set(frame['text'], desc)
                found_frame = frame_ctrl.get(desc)
            for key, value in frame.items():
                setattr(found_frame, key, value)

    def apply_change(self, id3file):
        change_str = self.change_str(id3file)

        if self.change_str:
            self.put_frames(id3file, self.get_new_value(id3file))
        return change_str


class ComplexFrameID3Change(SimpleFrameID3Change):
    '''A ComplexID3Change which is special-purpose for dealing with frame objects like comments and lyrics.'''

    def __init__(self, field: str, transformer: object):
        super().__init__(field, transformer)
        self.transformer = transformer

    def get_current_value(self, id3file):
        return self.get_frame_repr(id3file)

    def get_new_value(self, id3file):
        return self.transformer(id3file)


class ImageID3Change(ID3Change):
    def __init__(self, field: str, transformer: object):
        self._field = 'images'
        self.transformer = transformer

    def get_current_value(self, id3file):
        return id3file.tag.images[0].image_data

    def get_new_value(self, id3file):
        return self.transformer(id3file)

    def change_str(self, id3file: Mp3AudioFile) -> str:
        if not self.needs_change(id3file):
            return ''
        old_value = len(self.get_current_value(id3file))
        new_value = len(self.get_new_value(id3file))
        return f'{self.field}: "{old_value} bytes" -> "{new_value} bytes"'

    def apply_change(self, id3file):
        change_str = self.change_str(id3file)
        if self.change_str:
            new_value = self.get_new_value(id3file)
            id3file.tag.images[0].image_data = new_value
        return change_str


class ID3ChangeChain(ID3Change):
    def __init__(self, field):
        super().__init__(field)
        self.sub_changes = []

    def add(self, change: ID3Change):
        if change.field != self.field:
            raise ID3CleanerArgumentContradictionError(
                f'Found mismatched change field {self.field} in change chain of type {self.field}')
        # This feeds the output of each step of the chain into the next step as we build the chain.
        if self.sub_changes:
            prevchange = self.sub_changes[-1]
            change.get_current_value = lambda x: prevchange.get_new_value(x)
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
    change_def: dict = {}

    def __init__(self, changes=[]):
        for change in changes:
            self.add_change(change)

    def add_change(self, change: SimpleID3Change):
        if change.field not in self.change_def:
            self.change_def[change.field] = ID3ChangeChain(change.field)
        self.change_def[change.field].add(change)

    def check(self):
        contradictions = [
            f'Change registered under {key}, but change has field ID {value.field}'
            for key, value in self.change_def.items()
            if key != value.field
        ]
        if any(contradictions):
            raise ID3CleanerArgumentContradictionError(
                contradictions.join('\n'))

    def needs_change(self, id3file: Mp3AudioFile):
        return any(c.needs_change(id3file) for c in self.change_def.values())

    def whatif(self, id3file: Mp3AudioFile) -> list:
        return [
            c.change_str(id3file)
            for c in self.change_def.values() if c.needs_change(id3file)
        ]

    def apply(self, id3file: Mp3AudioFile):
        return [
            c.apply_change(id3file)
            for c in self.change_def.values() if c.needs_change(id3file)
        ]
