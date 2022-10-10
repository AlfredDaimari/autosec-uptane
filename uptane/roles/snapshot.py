# snapshot role

from uptane.roles.role import AutoRole


class Snapshot(AutoRole):
    '''
        Class inheriting the Snapshot role of Uptane

    '''

    def __init__(self, cfg: str) -> None:
        AutoRole.__init__(self, cfg)

    def sign_targets_metadata(self, metadata_file) -> None:
        '''
        Sign the metadata file received from Target Role
        '''
        self.sign_metadata(metadata_file)
