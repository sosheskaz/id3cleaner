class ID3CleanerError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ID3CleanerFormatError(Exception):
    '''This indicates that arguments given to this function are improperly formatted.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ID3CleanerArgumentContradictionError(Exception):
    '''This indicates that arguments given to this exception constitute a logical contradiction.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
