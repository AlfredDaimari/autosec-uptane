# this file will implement the timestamp role for uptane

from uptane.roles.role import AutoRole


class Timestamp(AutoRole):
    '''
    Timestamp class 
    This will sign metadata received from Snapshot Role
    '''

    def __init__(self, cfg: str) -> None:
        AutoRole.__init__(self, cfg)

    def sign_snapshot_metadata(self, snapshot_metadata_file) -> None:
        '''
        Sign metadata file received from Snapshot
        '''
        self.sign_metadata(snapshot_metadata_file)
