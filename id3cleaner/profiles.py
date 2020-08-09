import copy
from id3cleaner.changes import ChangeProfile, SimpleID3Change, SimpleFrameID3Change


def strtrim(s):
    if not isinstance(s, (str, bytes)):
        return s
    return f'{s.strip()}'

def lowercaselang(framedict):
    framedict = copy.deepcopy(framedict)
    for item in framedict.values():
        item['lang'] = item['lang'].lower()
    return framedict

def framestrtrim(framedict):
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
