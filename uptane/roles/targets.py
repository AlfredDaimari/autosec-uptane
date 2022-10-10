# file for implementing targets role

from uptane.roles.role import AutoRole, ManualRole
from typing import Dict, Any
import cryptography
import hashlib
import os
import toml
from uptane.crypto.hash import HashFunc


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
        self.metadata_cfg_dict = {}
        self.new_metadata_signed_dict:Dict[str, Any] = {
            "spec_version": OFFLINE_TARGETS_SPEC_VERSION,
            "_type": "targets",
            "imetadata":{}
        }

    def __get_file_size(self) -> int:
        return os.path.getsize(self.metadata_cfg_dict["local_file_path"])

    def __get_file_hash(self, hashf: HashFunc, bufsize:int) -> str:
        '''
        Hash the file, path to file is given in metadata_cfg
            Parameters:
                hashf (HashFunc): the hash function to be used
            Retures:
                str: the hash of the file 
        '''
        hashfunc = hashlib.sha256() # using sha256 as default

        if hashf == HashFunc.sha256:
            hashfunc = hashlib.sha256() 

        if hashf == HashFunc.md5:
            hashfunc = hashlib.md5()
            
        # ? add more hash functions ??

        image_file = open(self.metadata_cfg_dict["local_file_path"], "rb")

        while True:
            data = image_file.read(bufsize)
            if not data:
                break
            hashfunc.update(data)

        return hashfunc.hexdigest()

        
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
        self.new_metadata_signed_dict["image_hash"] = \
        self.__get_file_hash(HashFunc.sha256, bufsize)

        for metakey in meta_to_newmeta_map:
            self.new_metadata_signed_dict[meta_to_newmeta_map[metakey]] = \
            self.metadata_cfg_dict[metakey]

        # adding vendor specific metadata to signed metadata
        for key in self.metadata_cfg_dict:
            if not key in meta_to_newmeta_map:
                self.new_metadata_signed_dict["imetadata"][key] = \
                self.metadata_cfg_dict[key]

    def generate_metadata_file(self, metadata_file: str) -> None:
        self.__generate_metadata()
        toml_file = open(metadata_file, "w")
        toml.dump(self.new_metadata_signed_dict, toml_file)


