# common code between various roles

import os
import typing
import tomli
import tomli_w
import uptane.crypto.hash
import uptane.crypto.sign
import uptane.time
import uptane.error.general

URL = 'http://www.autosec.com/'


class AutoRole:
    '''
        Automatic Role Common Functions Class
            
            - Implements common functionality between non-human automatic roles (Snapshot, 
              Timestamp, Targets)
        
            - Common functions are - gen_cfg_metata, gen_signed_metadata_file

            - Meant to be run on server
    '''

    def __init__(self, cfg: str) -> None:
        '''
        Init Manual Role, configures the role

            Parameters:
                cfg (str): path to the role configuration toml file
                gen_img_metadata (bool) [Optional, Default: True]: default behaviour, generates 
                image metadata

            Raises:
                FileNotFoundError - when toml file is not found 
                tomli.TomlDecodeError - when toml has syntax error

            TODO:
                Come up with our own toml parsing library
        '''

        with open(cfg, "rb") as f:

            toml_dict = tomli.load(f)
            self.cfg_toml_dict = toml_dict
            self.private_key = toml_dict["private_key"]
            self.role = toml_dict["role"]
            self.public_key = toml_dict["public_key"]
            self.key_type = toml_dict["key_type"]

            self.hash_function = toml_dict["hash"]["function"]
            self.bufsize = toml_dict["hash"]["bufsize"]

            self.sig_algo = toml_dict["signature"]["algorithm"]

            self.signed_dict: typing.Dict = {}
            self.signature_dict: typing.Dict = {}

            self.cfg_toml_dict = toml_dict

    def auto__reinit(self, gen_img_metadata):
        '''
        Setup base metadataclass for new metadata file generation
        '''
        self.signed_dict: typing.Dict = {}
        self.signature_dict: typing.Dict = {}
        self.__gen_cfg_metadata(gen_img_metadata)

    def __gen_cfg_metadata(self, gen_img_metadata: bool = True) -> None:
        '''
        Generates the cfg metadata for the image metadata file
        '''
        self.signature_dict["keyid"] = self.public_key
        self.signature_dict["sig"] = ""
        self.signature_dict["key_type"] = self.key_type

        if gen_img_metadata:
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


class ManualRole:
    '''
        Manual Role Common Functions Class
        
            - Implements common functionality between human roles (Snapshot, Timestamp,
                Targets)

            - Common functions are - gen_cfg_metadata, gen_signed_metadata_file

            - This class is only meant to be used for a terminal program, not run on server

    '''

    def __init__(self, cfg: str, gen_img_metadata: bool = True) -> None:
        '''
        Init Manual Role, configures the role

            Parameters:
                cfg (str): path to the role configuration toml file
                gen_img_metadata (bool) [Optional, Default: True]: default behaviour, generates 
                image metadata

            Raises:
                FileNotFoundError - when toml file is not found 
                tomli.TomlDecodeError - when toml has syntax error

            TODO:
                Come up with our own toml parsing library
        '''

        with open(cfg, "rb") as f:

            toml_dict = tomli.load(f)
            self.cfg_toml_dict = toml_dict
            self.private_key = toml_dict["private_key"]
            self.role = toml_dict["role"]
            self.public_key = toml_dict["public_key"]
            self.key_type = toml_dict["key_type"]

            self.hash_function = toml_dict["hash"]["function"]
            self.bufsize = toml_dict["hash"]["bufsize"]

            self.sig_algo = toml_dict["signature"]["algorithm"]

            self.signed_dict: typing.Dict = {}
            self.signature_dict: typing.Dict = {}

            self.__gen_cfg_metadata(gen_img_metadata)
            self.cfg_toml_dict = toml_dict

    def __gen_cfg_metadata(self, gen_img_metadata: bool = True) -> None:
        '''
        Generates the cfg metadata for the image metadata file
        '''
        self.signature_dict["keyid"] = self.public_key
        self.signature_dict["sig"] = ""
        self.signature_dict["key_type"] = self.key_type
        if gen_img_metadata:
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
        self.signed_dict["expires"] = f'{uptane.time.get_fut365y_epoch_time()}'
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

    def __init__(self, cfg, image_cfg: str = 'None') -> None:
        '''
        Inits the common metadata between Targets and Snapshot
        Common Metadata:
            - image_name
            - image_url
            - image_version
            - image_size 
            - image_hash 
        '''
        ManualRole.__init__(self, cfg, False if image_cfg == 'None' else True)
        self.image_cfg_toml_dict: typing.Dict[str, typing.Any] = {}

        if image_cfg != 'None':
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


class TarSnapAutoRole(AutoRole):
    '''
    Implements the common functionality between both such as:
        - generate image file hashes
        - generate metadata file signature
    '''

    def __init__(self, cfg) -> None:
        '''
        Inits the common metadata between Targets and Snapshot
        Common Metadata:
            - image_name
            - image_url
            - image_version
            - image_size 
            - image_hash 
        '''
        AutoRole.__init__(self, cfg)
        self.image_cfg_toml_dict: typing.Dict[str, typing.Any] = {}

    def tarsnapauto_reinit(self, image_cfg: typing.Any):

        if image_cfg is not None:

            self.auto__reinit(True)
            self.signed_dict["image_name"] = image_cfg["image_name"]
            self.signed_dict["image_url"] = image_cfg["image_url"]
            self.signed_dict["image_version"] = image_cfg["image_version"]
            self.signed_dict["image_size"] = image_cfg["image_size"]
            self.signed_dict["image_hash"] = image_cfg["image_hash"]
            self.image_cfg_toml_dict = image_cfg

        else:

            self.auto__reinit(False)
            self.image_cfg_toml_dict = {}

            if self.signed_dict.get('image_name'):
                del self.signed_dict['image_name']

            if self.signed_dict.get('image_url'):
                del self.signed_dict['image_url']

            if self.signed_dict.get('image_version'):
                del self.signed_dict['image_version']

            if self.signed_dict.get('image_size'):
                del self.signed_dict['image_size']

            if self.signed_dict.get('image_hash'):
                del self.signed_dict['image_hash']
