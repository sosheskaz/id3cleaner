'''ID3 Cleaner Errors'''


class ID3CleanerError(Exception):
    '''Generic ID3Cleaner Error.'''


class ID3CleanerFormatError(Exception):
    '''This indicates that arguments given to this function are improperly formatted.'''


class ID3CleanerArgumentContradictionError(Exception):
    '''This indicates that arguments given to this exception constitute a logical contradiction.'''
