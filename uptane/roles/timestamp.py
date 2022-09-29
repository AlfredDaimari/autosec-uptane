# this file will implement the timestamp role for uptane

from uptane.roles.role import Role


class Timestamp(Role):

    '''
    Timestamp class

        Will sign metadata of snapshot role 

    '''

    def __init__(self) -> None:
        Role.__init__(self)

    def sign_snapshot_metadata(self, snapshot_metadata_file) -> None:
        self.sign_metadata(snapshot_metadata_file)


