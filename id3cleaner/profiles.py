'''
Profiles, which are an ordered collection of changes to carry out.
'''
import copy
from id3cleaner.changes import ChangeProfile, SimpleID3Change, SimpleFrameID3Change


def strtrim(text):
    '''Trim whitespace from the string.'''
    if not isinstance(text, (str, bytes)):
        return text
    return f'{text.strip()}'


def lowercaselang(framedict):
    '''Convert language spec to lowercase'''
    framedict = copy.deepcopy(framedict)
    for item in framedict.values():
        item['lang'] = item['lang'].lower()
    return framedict


def framestrtrim(framedict):
    '''Trim excess whitespace from the framedict'''
    framedict = copy.deepcopy(framedict)
    for item in framedict.values():
        item['lang'] = item['lang'].strip()
        item['text'] = item['text'].strip()
    return framedict


def default_cleaner_profile(profile: ChangeProfile):
    '''Builds the default cleaner profile'''
    if profile is None:
        profile = ChangeProfile()

    profile.add_change(SimpleID3Change('album', strtrim))
    profile.add_change(SimpleID3Change('album_artist', strtrim))
    profile.add_change(SimpleID3Change('artist', strtrim))
    profile.add_change(SimpleID3Change('composer', strtrim))
    profile.add_change(SimpleID3Change('title', strtrim))

    profile.add_change(SimpleFrameID3Change('comments', lowercaselang))
    profile.add_change(SimpleFrameID3Change('comments', framestrtrim))
    profile.add_change(SimpleFrameID3Change('lyrics', lowercaselang))
    profile.add_change(SimpleFrameID3Change('lyrics', framestrtrim))

    return profile
