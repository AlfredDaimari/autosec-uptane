# file for implementing targets role

import pathlib
from uptane.roles.role import AutoRole, ManualRole, TarSnapManualRole
from typing import Dict, Any

ONLINE_TARGETS_SPEC_VERSION = "0.0.1"
OFFLINE_TARGETS_SPEC_VERSION = "0.0.1"


class TargetsOnline(AutoRole):
    '''
    Targets roles 
    This role will sign the image metadata on demand on the server
    '''

    def __init__(self, cfg: str) -> None:
        AutoRole.__init__(self, cfg)

    def sign_image_metadata(self, image_metadata_file) -> None:
        '''
        Sign image metadata
        '''
        self.sign_metadata(image_metadata_file)


# verification function to verify the image toml file
class TargetsOffline(TarSnapManualRole):
    '''
    Targets Offline Role 
    This role will generate targe image metadata for the toml file
    '''

    def __init__(self, cfg, image_cfg) -> None:
        TarSnapManualRole.__init__(self, cfg, image_cfg)

        self.signed_dict["spec_version"] = str(OFFLINE_TARGETS_SPEC_VERSION)
        self.signed_dict["_type"] = "targets"
        self.signed_dict["imetadata"] = {}

        self.__generate_metadata()

    def __generate_metadata(self) -> None:
        '''
        Populate the signed_dict that will be converted to a toml file
        '''
        # adding vendor specific metadata to signed metadata
        reserved_metadata_keys = {'local_path', '_name', '_url', '_version'}

        for key in self.image_cfg_toml_dict:
            if not key in reserved_metadata_keys:
                self.signed_dict["imetadata"][key] = self.image_cfg_toml_dict[key]
