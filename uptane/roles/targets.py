# file for implementing targets role

from uptane.roles.role import Role

class Targets(Role):
    '''
    Targets role

        this role signs the image metadata
    '''

    def __init__(self) -> None:
        Role.__init__(self)


    def sign_image_metadata(self, image_metadata_file) -> None:
        self.sign_metadata(image_metadata_file)


