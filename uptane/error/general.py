class Error(Exception):
    pass


class PublicKeysNoMatch(Error):
    '''
    Raised when public keys do not match
    '''


class FileHashNoMatch(Error):
    '''
    Raised when Local File Hash does not match with given Metadata File Hash
    '''


class MetadataFileHasExpired(Error):
    '''
    Raised when MetadataFile has expired
    '''


class MetadataFileInvalidSignature(Error):
    '''
    Raised when signature of metadata file is invalid
    '''
