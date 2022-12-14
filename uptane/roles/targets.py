# file for implementing targets role
from uptane.roles.role import TarSnapManualRole, TarSnapAutoRole
import typing

ONLINE_TARGETS_SPEC_VERSION = "0.0.1"
OFFLINE_TARGETS_SPEC_VERSION = "0.0.1"


class TargetsOnline(TarSnapAutoRole):
    '''
    Targets roles 
    This role will sign the image metadata on demand on the server
    '''

    def __init__(self, cfg: str) -> None:
        TarSnapAutoRole.__init__(self, cfg)
        self.signed_dict["spec_version"] = str(ONLINE_TARGETS_SPEC_VERSION)
        self.signed_dict["_type"] = "targets"

    def targetsoneline_reinit(self, image_cfg: typing.Any):
        self.signed_dict["spec_version"] = str(ONLINE_TARGETS_SPEC_VERSION)
        self.signed_dict["_type"] = "targets"
        self.tarsnapauto_reinit(image_cfg)


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
                self.signed_dict["imetadata"][key] = self.image_cfg_toml_dict[
                    key]
