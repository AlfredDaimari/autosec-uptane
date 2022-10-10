# file for implementing targets role

import pathlib
from uptane.roles.role import AutoRole, ManualRole
from typing import Dict, Any
import os
import toml
import uptane.crypto.hash
import uptane.crypto.sign

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
class TargetsOffline(ManualRole):
    '''
    Targets Offline Role 
    This role will generate image metadata in a toml file and sign it
    '''

    def __init__(self, role_cfg, metadata_cfg) -> None:
        ManualRole.__init__(self, role_cfg)
        self.metadata_cfg_dict:Dict[str, Any] = {}

        metadata_cfg_pth = pathlib.Path(metadata_cfg)
        if not pathlib.Path.exists(metadata_cfg_pth):
            raise FileNotFoundError
        else:
            metadata_cfg_f = open(metadata_cfg, "r")

            try:
                self.metadata_cfg_dict = toml.load(metadata_cfg_f)

            except toml.TomlDecodeError:
                print( "CFG error: The metadata config file consists of errors")
                exit(1)

            except:
                print("Unknown error generated at TargetsOffline.__init__(self,..,..)")
                exit(1)

        self.new_metadata_signed_dict:Dict[str, Any] = {
            "spec_version": OFFLINE_TARGETS_SPEC_VERSION,
            "_type": "targets",
            "imetadata":{}
        }
        self.new_metadata_signature_dict:Dict[str, str] = {
            "signature": "",
            "public_key": self.public_key,
        }

    def __get_file_size(self) -> int:
        return os.path.getsize(self.metadata_cfg_dict["limage_path"]) 
        
    def __generate_metadata(self) -> None:
        '''
        Populate the new metadata dict that will be converted to a toml file
        '''
        meta_to_newmeta_map = {
            "name": "image_name",
            "url": "image_url",
            "version": "image_version"
        }

        self.new_metadata_signed_dict["image_size"] = self.__get_file_size()

        bufsize = 65536 # make this a commandline input
        self.new_metadata_signed_dict["image_buf_size"] = f'{bufsize}'

        # TODO add a correct hash function option
        self.new_metadata_signed_dict["hash_function"] = "sha256"
        self.new_metadata_signed_dict["image_hash"] = \
        uptane.crypto.hash.get_file_hash(self.metadata_cfg_dict["limage_path"], \
                                         uptane.crypto.hash.HashFunc.sha256, bufsize)

        for metakey in meta_to_newmeta_map:
            self.new_metadata_signed_dict[meta_to_newmeta_map[metakey]] = \
            self.metadata_cfg_dict[metakey]

        # adding vendor specific metadata to signed metadata
        for key in self.metadata_cfg_dict:
            if not key in meta_to_newmeta_map:
                self.new_metadata_signed_dict["imetadata"][key] = \
                self.metadata_cfg_dict[key]

        # TODO add support for more key types
        # adding signature for metadata after all metadata has been generated
        self.new_metadata_signed_dict["signature_algo"] = "ed25519"
        self.new_metadata_signature_dict["signature"] = \
        uptane.crypto.sign.sign_metadata(self.new_metadata_signed_dict, \
        uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, \
        self.private_key)

    def generate_metadata_file(self, metadata_file: str) -> None:
        self.__generate_metadata()
        toml_file = open(metadata_file, "w")
        toml.dump({"signature": self.new_metadata_signature_dict, \
        "signed": self.new_metadata_signed_dict}, toml_file)


