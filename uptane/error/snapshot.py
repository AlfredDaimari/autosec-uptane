class Error(Exception):
    pass

class SnapshotTargetsFileHashNoMatch(Error):
    '''
    Raised when Shapshot Local File Hash does not match with Targets Metadata File Hash
    '''
    pass
