class Error(Exception):
    pass


class FileHashNoMatch(Error):
    '''
    Raised when Local File Hash does not match with given Metadata File Hash
    '''
    pass


class MetadataFileHasExpired(Error):
    '''
    Raised when MetadataFile has expired
    '''
