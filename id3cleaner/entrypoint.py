#!/usr/bin/env python3
import argparse
import logging
import os
import re
import time
import eyed3
import eyed3.id3
from id3cleaner import profiles, changes, id3_fmt


def _setuplogger(loglevel):
    if isinstance(loglevel, str):
        loglevel = getattr(logging, loglevel)
    logging.basicConfig(level=loglevel)


LOG = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--title')
    parser.add_argument('--artist')
    parser.add_argument('--album')
    parser.add_argument('--album-artist')
    parser.add_argument('--track-num', type=int)
    parser.add_argument('--genre', type=eyed3.id3.Genre)
    parser.add_argument('--picture-file')
    parser.add_argument('--rename')
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--loglevel', default='INFO',
                        choices=('ERROR', 'WARN', 'INFO', 'DEBUG'))
    args = parser.parse_args()
    _setuplogger(args.loglevel)

    filenames = args.filenames
    files_not_found = [fn for fn in filenames
                       if (not os.path.isfile(fn) and not os.path.islink(fn))]
    if files_not_found:
        LOG.error(f'The following files were not found: {files_not_found}')


    try:
        # force load of everything up front to make sure it works, then load
        # lazily later to save cycles
        _ = all(eyed3.load(filename) for filename in filenames)
    except Exception as e:
        LOG.fatal(e)
    audio_files = (eyed3.load(filename) for filename in filenames)

    profile = changes.ChangeProfile()
    for optfield in ('title', 'artist', 'album', 'album_artist', 'track_num', 'genre'):
        arg = getattr(args, optfield)
        if arg is not None:
            arg2 = arg  # Make a copy to pass into lambda statically
            change = changes.ComplexID3Change(
                optfield, lambda f: id3_fmt.format(arg2, f))
            profile.add_change(change)

    profiles.default_cleaner_profile(profile)

    if args.picture_file:
        def get_picture(af):
            with open(id3_fmt.format(args.picture_file, af), 'rb') as pf:
                picture_file_bytes = pf.read()
            return picture_file_bytes
        picture_change = changes.ImageID3Change('images', get_picture)
        profile.add_change(picture_change)

    try:
        for af in audio_files:
            _handle_audio_file(af, profile, args)
    except BaseException as e:
        print(e)
        return -1

    return 0

def _handle_audio_file(af: eyed3.core.AudioFile, profile: changes.ChangeProfile, args):
    rename_diff = False
    _, ext = os.path.splitext(os.path.basename(af.path))
    if args.rename:
        rename_to = id3_fmt.format(args.rename, af)
        rename_to = re.sub(r'[/\\;#%{}<>*?+`|=]', '_', rename_to)
        new_name = f'{rename_to}{ext}'
        rename_diff = new_name != os.path.basename(af.path)

    if profile.needs_change(af) or rename_diff:
        if profile.needs_change(af):
            plan_lines = (f'{af.path}: PLAN {i}' for i in profile.whatif(af))
            LOG.info('\n'.join(plan_lines))
        new_name = f'{rename_to}{ext}'
        if args.rename and rename_diff:
            LOG.info(f'"{af.path}" RENAME => "{new_name}"')
        if args.dry_run:
            return
        else:
            LOG.info('\n'.join(f'{af.path}: {i}' for i in profile.apply(af)))
            LOG.info(f'{af.path}: Saving...')
            af.tag.save()
            LOG.debug(f'{af.path}: Saved!')
            if rename_to:
                old_path = af.path
                if os.path.basename(old_path) != f'{new_name}' and not args.dry_run:
                    LOG.info(f'{af.path}: Renaming to "{new_name}"')
                    af.rename(rename_to)
                    new_path = af.path
                    LOG.debug(f'{old_path}: Renamed to "{new_path}"')
                if args.dry_run:
                    return
    else:
        LOG.warn(f'{af.path}: No change.')
