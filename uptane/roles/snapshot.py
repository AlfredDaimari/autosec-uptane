# snapshot role

from uptane.roles.role import Role


class Snapshot(Role):
    '''
        Class inheriting the Snapshot role of Uptane

    '''

    def __init__(self) -> None:
        Role.__init__(self)

    def sign_targets_metadata(self, metadata_file) -> None:
        self.sign_metadata(metadata_file)
