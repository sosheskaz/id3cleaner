'''Common string formatting tools dealing with id3 information.'''
import eyed3


def fmt_dict(audio_file: eyed3.mp3.Mp3AudioFile) -> dict:
    '''Get a dict of substitutable fields from the audio file.'''
    fmt = {
        tag: getattr(audio_file.tag, tag)
        for tag in ('album', 'album_artist', 'album_type', 'artist',
                    'artist_origin', 'artist_url', 'audio_file_url',
                    'audio_source_url', 'best_release_date', 'bpm', 'cd_id',
                    'commercial_url', 'composer', 'copyright', 'copyright_url',
                    'disc_num', 'encoded_by', 'encoding_date',
                    'internet_radio_url', 'original_artist',
                    'original_release_date', 'payment_url', 'publisher',
                    'publisher_url', 'recording_date', 'release_date',
                    'tagging_date', 'title', 'track_num', 'version')
    }
    fmt['year'] = audio_file.tag.getBestDate().year
    return fmt


def id3_fmt(fmt: str, audio_file: eyed3.mp3.Mp3AudioFile) -> str:
    '''Perform a string format, dict-substituting fields from the given file.'''
    return fmt.format(**fmt_dict(audio_file))
