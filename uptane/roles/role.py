# common code between various roles

import os
import typing
import time
import tomli
import tomli_w
import uptane.crypto.hash
import uptane.crypto.sign
import uptane.time


class AutoRole:
    '''
        Automatic Role Common Functions Class
            
            - Implements common functionality between non-human automatic roles (Snapshot, 
              Timestamp, Targets)
        
            - Common functions are - revoke_key, get_time_to_expr, generate_signature,
              replace_online_key, add_online_key, sign_metadata
    '''

    def __init__(self, cfg: str) -> None:
        '''
        Init the Role with a link to a configuration toml file, this will be the starting
        config
            
            Parameters:
                cfg (str): path to the configuration file
            
            Raises:
                tomli.TomlDecodeError
                FileNotFoundError
        '''
        with open(cfg, "rb") as f:
            toml_dict = tomli.load(f)
            self.online_key = toml_dict["key"]
            self.role = toml_dict["role"]
            # TODO - comeup with cfg file structure

    def get_expr_time(self,
                      metadata_file: str) -> None:  # return type should be date
        '''
        Returns the expiration time for the current metadata file

            Parameters:
                metadata_file (str): name of metadata file

            Returns:
                date object: a future time where time will expire

            Raises:
                MetadataSignatureExpired: when signature of a metadata file has already
                expired
        '''
        pass

    def generate_metadata_file(self) -> None:
        pass

    def replace_online_key(self, new_key: str, key_id_to_replace: str) -> None:
        pass

    def add_online_key(self, new_key: str) -> None:
        pass

    def sign_metadata(self, metadata_file) -> None:
        pass


class ManualRole:
    '''
        Manual Role Common Functions Class
        
            - Implements common functionality between human roles (Snapshot, Timestamp,
                Targets)

            - Common functions are - gen_cfg_metadata, gen_signed_metadata_file

            - This class is only meant to be used for a terminal program, not run on server

    '''

    def __init__(self, cfg: str) -> None:
        '''
        Init Manual Role, configures the role

            Parameters:
                cfg (str): path to the role configuration toml file

            Raises:
                FileNotFoundError - when toml file is not found 
                tomli.TomlDecodeError - when toml has syntax error

            TODO:
                Come up with our own toml parsing library
        '''

        with open(cfg, "rb") as f:

            toml_dict = tomli.load(f)
            self.private_key = toml_dict["private_key"]
            self.role = toml_dict["role"]
            self.public_key = toml_dict["public_key"]
            self.key_type = toml_dict["key_type"]

            self.hash_function = toml_dict["hash"]["function"]
            self.bufsize = toml_dict["hash"]["bufsize"]

            self.sig_algo = toml_dict["signature"]["algorithm"]

            self.signed_dict: typing.Dict[str, typing.Any] = {}
            self.signature_dict: typing.Dict[str, typing.Any] = {}

            self.__gen_cfg_metadata()

    def __gen_cfg_metadata(self) -> None:
        '''
        Generates the cfg metadata for the image metadata file
        '''
        self.signature_dict["keyid"] = self.public_key
        self.signature_dict["sig"] = ""
        self.signature_dict["key_type"] = self.key_type
        self.signed_dict["image_hash_func"] = self.hash_function
        self.signed_dict["image_buf_size"] = self.bufsize
        self.signed_dict["image_sig_algo"] = self.sig_algo

    def gen_signed_metadata_file(self, metadata_file: str) -> None:
        '''
        Generates the signed toml metadata file using self.signed_dict, self.signature_dict
        Generates the signature using self.signed_dict and populates self.signature_dict
        
            Paramters:
                meta_file (str): name of the file to push to, creates new one if it does
                not exist

            Raises:
                tomli.TomlDecodeError - when toml has syntax error
        '''
        self.signed_dict["expires"] = f'{uptane.time.get_fut24_epoch_time()}'
        self.signature_dict["sig"] = uptane.crypto.sign.sign_metadata(self.signed_dict, \
        uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, \
        self.private_key)

        with open(metadata_file, "wb") as f:
            tomli_w.dump(
                {
                    "signature": self.signature_dict,
                    "signed": self.signed_dict
                }, f)


class TarSnapManualRole(ManualRole):
    '''
    Implements the common functionality between both such as:
        - generate image file hashes
        - generate metadata file signature
    '''

    def __init__(self, cfg, image_cfg: str) -> None:
        '''
        Inits the common metadata between Targets and Snapshot
        Common Metadata:
            - image_name
            - image_url
            - image_version
            - image_size 
            - image_hash 
        '''
        ManualRole.__init__(self, cfg)
        self.image_cfg_toml_dict: typing.Dict[str, typing.Any] = {}

        with open(image_cfg, "rb") as f:
            toml_dict = tomli.load(f)
            self.local_image_path: str = toml_dict['local_path']
            self.signed_dict["image_name"] = toml_dict["_name"]
            self.signed_dict["image_url"] = toml_dict["_url"]
            self.signed_dict["image_version"] = toml_dict["_version"]
            self.signed_dict["image_size"] = self.__get_file_size()
            self.signed_dict["image_hash"] = \
            uptane.crypto.hash.get_file_hash(self.local_image_path, \
            uptane.crypto.hash.HashFunc.sha256, self.bufsize)
            self.image_cfg_toml_dict = toml_dict  # for latter use

    def __get_file_size(self) -> int:
        return os.path.getsize(self.local_image_path)
