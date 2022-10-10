# file for implementing targets role

from uptane.roles.role import AutoRole


class Targets(AutoRole):
    '''
    Targets roles 
    This role will sign the image metadata
    '''

    def __init__(self, cfg: str) -> None:
        AutoRole.__init__(self, cfg)

    def sign_image_metadata(self, image_metadata_file) -> None:
        '''
        Sign image metadata
        '''
        self.sign_metadata(image_metadata_file)
