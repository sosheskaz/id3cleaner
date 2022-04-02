#!/usr/bin/env python3
'''
ID3 Cleaner CLI Entrypoint
'''
import argparse
import functools
import logging
import pathlib
import sys

import coloredlogs
import eyed3
import eyed3.id3
import humanize

import id3cleaner
from id3cleaner import changes, id3_fmt, profiles
from id3cleaner.errors import ID3CleanerError


def _setuplogger(loglevel):
    if isinstance(loglevel, str):
        loglevel = getattr(logging, loglevel)
    logging.basicConfig(level=loglevel)


LOG = logging.getLogger(__name__)
coloredlogs.install()


def main() -> int:
    '''Run the program.'''
    args = parse_args(sys.argv[1:])

    if args.version:
        print(id3cleaner.__version__)
        return 2

    _setuplogger(loglevel=args.loglevel)

    filenames = [pathlib.Path(fn) for fn in args.filenames]
    files_not_found = [fn for fn in filenames if not fn.exists()]
    if files_not_found:
        LOG.fatal('The following files were not found: %s',
                  repr(files_not_found))
        return 2

    # force load of everything up front to make sure it works, then load
    # lazily later to save cycles
    LOG.info("Pre-loading all target files...")
    for filename in filenames:
        LOG.debug('\tPre-loading %s...', filename)
        _ = eyed3.load(filename)
    LOG.info("Pre-load succeeded.")

    audio_files = (eyed3.load(filename) for filename in filenames)

    profile = changes.ChangeProfile()
    for optfield in ('title', 'artist', 'album', 'album_artist', 'track_num', 'genre'):
        arg = getattr(args, optfield)
        if arg is not None:
            formatter = functools.partial(id3_fmt.id3_fmt, arg)
            change = changes.ComplexID3Change(optfield, formatter)
            profile.add_change(change)

    if args.rename:
        change = changes.SimpleRenameChange(args.rename, args.force_rename)
        profile.add_change(change)

    profiles.default_cleaner_profile(profile)

    if args.rename:
        change = changes.SimpleRenameChange(args.rename, args.force_rename)
        profile.add_change(change)

    if args.picture_file:
        def get_picture(audio_file):
            resolved_picture_f = id3_fmt.id3_fmt(args.picture_file, audio_file)
            picture_file = pathlib.Path(resolved_picture_f)
            LOG.info('Loading picture file %s...', picture_file)
            with open(picture_file, 'rb') as picture_fd:
                picture_file_bytes = picture_fd.read()

            human_bytes = humanize.naturalsize(len(picture_file_bytes))
            LOG.info('Picture file %s loaded (%s).', picture_file, human_bytes)
            return picture_file_bytes
        picture_change = changes.ImageID3Change('images', get_picture)
        profile.add_change(picture_change)

    nosave_profile = changes.ChangeProfile()
    if args.rename:
        change = changes.SimpleRenameChange(args.rename, args.force_rename)
        nosave_profile.add_change(change)

    try:
        for audio_file in audio_files:
            _handle_audio_file(audio_file, profile, nosave_profile=nosave_profile, dry_run=args.dry_run)
    except ID3CleanerError as err:
        LOG.fatal(err)
        return 2

    return 0


def parse_args(argv: 'list[str]') -> argparse.Namespace:
    '''Creates argument parser and parses CLI Args.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--title')
    parser.add_argument('--artist')
    parser.add_argument('--album')
    parser.add_argument('--album-artist')
    parser.add_argument('--track-num', type=int)
    parser.add_argument('--genre', type=eyed3.id3.Genre)
    parser.add_argument(
        '--picture-file', help='Set the picture to the given file.')
    parser.add_argument(
        '--rename', help='Rename files using the given format string.')
    parser.add_argument('--force-rename', action='store_true',
                        help="When renaming, proceed with the rename even if "
                        "the target file already exists.")
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--loglevel', default='INFO',
                        choices=('ERROR', 'WARN', 'INFO', 'DEBUG'))
    parser.add_argument('--version', action='store_true',
                        help='Print the version and exit')
    args = parser.parse_args(argv)
    return args


def _handle_audio_file(audio_file: eyed3.core.AudioFile,
                       profile: changes.ChangeProfile,
                       nosave_profile: changes.ChangeProfile = None,
                       dry_run: bool = False):
    af_path = pathlib.Path(audio_file.path)

    if profile.needs_change(audio_file):
        plans = profile.whatif(audio_file) + nosave_profile.whatif(audio_file)
        for plan_line in plans:
            LOG.info('%s: PLAN %s', af_path, plan_line)

        if dry_run:
            return

        for i in profile.apply(audio_file):
            LOG.info('%s: %s', af_path, i)
        LOG.info('%s: Saving...', af_path)
        audio_file.tag.save()
        LOG.debug('%s: Saved.', af_path)

        for i in nosave_profile.apply(audio_file):
            LOG.info('%s: %s', af_path, i)
    else:
        LOG.warning('%s: No change.', af_path)
