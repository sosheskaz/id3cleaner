# ID3Clean

I find myself downloading podcasts with podget.

I find that they often have malformed id3 tags.

This is a quick-and-dirty solution that autocleans ID3 tags, removing whitespace, improving conformity with id3 standards, and also allowing overwrites of common metadata from the command line (similar to how eyed3 does).

Basic usage: id3clean.py my_file.mp3. id3clean.py -h lists the fields available for override. `--dry-run` will print what it would do, but not actually save the changes.

* Supplying multiple files is supported and dramatically improves performance.
* Manipulating comments is not supported.
* Renaming the file automatically is supported via `--rename`.
* Fields that support overriding on the command line also support tag interpolation via python formatting syntax: ex `--rename '{title}'`
