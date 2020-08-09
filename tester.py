import json
import eyed3

from id3cleaner import id3cleaning

profile = id3cleaning.default_cleaner_profile()

f = eyed3.load('HSW1111650016.mp3')

print(json.dumps(profile.whatif(f), indent=4))
