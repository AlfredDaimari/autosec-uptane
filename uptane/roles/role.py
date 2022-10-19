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
            self.toml_dict = tomli.load(f)
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

            self.signed_dict: typing.Dict[str, typing.Any] = {}
            self.signature_dict: typing.Dict[str, typing.Any] = {}

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


class Verification:
    '''
    This is the verification class of uptane, for verification, you would need access to 
    unexpired root metadata file:
    The various verification it performs are:
        Target Verification:
            Checks hash of File 
            Checks signature of File 

        Snapshot Verification 
            Checks hash of image file 
            Checks signature of file 
            Checks hash of Targets metadata file against Snapshot hash 

        Timestamp Verification 
            Checks signature of file 
            Checks hash of Snapshot metadata file against hash in Timestamp metadata file 
    '''

    def __init__(self, root_metadata: str) -> None:
        '''
        Inits the verification class with the root metadata file
            Parameters:
                root_metadata (str):

            Raises:
                FileNotFoundError - file not found
                tomli.TomlDecodeError - error in decoding toml file
                uptane.error.general.MetadataFileHasExpired

            Note:
                As of now only configured to handle only one timestamp, snapshot, targets
                key and key type ed25519
        '''
        with open(root_metadata, 'rb') as f:
            toml_dict = tomli.load(f)
            self.root_dt = toml_dict["signed"]["keys"][0]
            self.root_signed = toml_dict["signed"]
            self.targets_dt = toml_dict["signed"]["roles"]["targets"]["keys"][0]
            self.snapshot_dt = toml_dict["signed"]["roles"]["snapshot"]["keys"][
                0]
            self.timestamp_dt = toml_dict["signed"]["roles"]["timestamp"][
                "keys"][0]

        if uptane.time.fut24_is_expired(int(toml_dict["signed"]["expires"])):
            raise uptane.error.general.MetadataFileHasExpired

    def __verify_root(self):
        '''
        Verifies whether the root has signed with his key or not

            Raises:
                uptane.error.general.MetadataFileHasExpired
                uptane.error.general.MetadataFileInvalidSignature
        '''
        sig = self.root_signed["signatures"]["sig"]

        if uptane.time.fut24_is_expired(self.root_signed["expires"]):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(self.root_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, self.root_dt, sig):
            raise uptane.error.general.MetadataFileInvalidSignature

    def __verify_targets(self, path: str) -> None:
        '''
        Verifies whether target file came from trusted source or not

            Parameters:
                path (str): path to targets metadata file
            
            Raises:
                uptane.error.general.MetadataFileHasExpired 
                uptane.error.general.MetadataFileInvalidSignature
                FileNotFoundError - when file is not found
                toml.TOMLDecodeError
                uptane.error.general.PublicKeysNoMatch
        '''
        targets_metadata_file: str = path + '/targets.toml'
        image_file: str = path + '/image'
        sig: str = ''
        public_key: str = ''
        image_hash: str = ''
        metadata_signed: typing.Dict[str, typing.Any] = {}
        buf_size: int = 0

        with open(targets_metadata_file, 'rb') as f:
            toml_dict = tomli.load(f)
            sig = toml_dict["signatures"]["sig"]
            public_key = toml_dict['signatures']['keyid']
            image_hash = toml_dict['signed']['image_hash']
            metadata_signed = toml_dict['signed']
            buf_size = int(toml_dict["signed"]["image_buf_size"])

        if self.targets_dt["keyid"] != public_key:
            raise uptane.error.general.PublicKeysNoMatch

        if uptane.time.fut24_is_expired(toml_dict["signed"]["expires"]):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(metadata_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, public_key, sig):
            raise uptane.error.general.MetadataFileInvalidSignature

        if uptane.crypto.hash.get_file_hash(image_file, uptane.crypto.hash.HashFunc.sha256, \
                                            buf_size) != image_hash:
            raise uptane.error.general.FileHashNoMatch

    def __verify_snapshot(self, path: str) -> None:
        '''
        Verifies whether target file came from trusted source or not

            Parameters:
                path (str): path to targets metadata file
            
            Throws:
                uptane.error.general.MetadataFileHasExpired 
                uptane.error.general.MetadataFileInvalidSignature
                FileNotFoundError - when file is not found
                toml.TOMLDecodeError
                uptane.error.general.PublicKeysNoMatch 
        '''
        targets_metadata_file: str = path + '/targets.toml'
        snapshot_metadata_file: str = path + '/snapshot.toml'
        image_file: str = path + '/image'
        sig: str = ''
        public_key: str = ''
        image_hash: str = ''
        targets_metadata_file_hash: str = ''
        metadata_signed: typing.Dict[str, typing.Any] = {}
        buf_size: int = 0

        with open(snapshot_metadata_file, 'rb') as f:
            toml_dict = tomli.load(f)
            sig = toml_dict["signatures"]["sig"]
            public_key = toml_dict['signatures']['keyid']

            image_hash = toml_dict['signed']['image_hash']
            targets_metadata_file_hash = toml_dict["signed"][
                "targets_metadata_file_hash"]

            metadata_signed = toml_dict['signed']
            buf_size = int(toml_dict["signed"]["image_buf_size"])

        if self.snapshot_dt["keyid"] != public_key:
            raise uptane.error.general.PublicKeysNoMatch

        if uptane.time.fut24_is_expired(toml_dict["signed"]["expires"]):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(metadata_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, public_key, sig):
            raise uptane.error.general.MetadataFileInvalidSignature

        if uptane.crypto.hash.get_file_hash(image_file, uptane.crypto.hash.HashFunc.sha256, \
                                            buf_size) != image_hash:
            raise uptane.error.general.FileHashNoMatch

        if uptane.crypto.hash.get_file_hash(targets_metadata_file, \
                uptane.crypto.hash.HashFunc.sha256, buf_size) != targets_metadata_file_hash:
            raise uptane.error.general.FileHashNoMatch

    def __verify_timestamp(self, path: str) -> None:
        '''
        Verifies whether target file came from trusted source or not

            Parameters:
                path (str): path to targets metadata file
            
            Throws:
                    FileNotFoundError
                    tomli.TOMLDecodeError
                    uptane.error.general.FileHashNoMatch
                    uptane.error.general.PublicKeysNoMatch
                    uptane.error.general.MetadataFileHasExpired
                    uptane.error.general.MetadataFileInvalidSignature
       '''
        snapshot_metadata_file: str = path + '/snapshot.toml'
        timestamp_metadata_file: str = path + '/timestamp.toml'
        sig: str = ''
        public_key: str = ''
        image_hash: str = ''
        snapshot_metadata_file_hash: str = ''
        metadata_signed: typing.Dict[str, typing.Any] = {}
        buf_size: int = 0

        with open(timestamp_metadata_file, 'rb') as f:
            toml_dict = tomli.load(f)
            sig = toml_dict["signatures"]["sig"]
            public_key = toml_dict['signatures']['keyid']

            image_hash = toml_dict['signed']['image_hash']
            snapshot_metadata_file_hash = toml_dict["signed"][
                "snapshot_metadata_file_hash"]

            metadata_signed = toml_dict['signed']
            buf_size = int(toml_dict["signed"]["image_buf_size"])

        if self.timestamp_dt["keyid"] != public_key:
            raise uptane.error.general.PublicKeysNoMatch

        if uptane.time.fut24_is_expired(toml_dict["signed"]["expires"]):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(metadata_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, public_key, sig):
            raise uptane.error.general.MetadataFileInvalidSignature

        if uptane.crypto.hash.get_file_hash(snapshot_metadata_file, \
                uptane.crypto.hash.HashFunc.sha256, buf_size) != snapshot_metadata_file_hash:
            raise uptane.error.general.FileHashNoMatch

    def verify(self, url: str) -> None:
        '''
            Verifies metadata for an image file 
                Parameters:
                   url (str): path to the file

                Raises:
                    FileNotFoundError
                    tomli.TOMLDecodeError
                    uptane.error.general.FileHashNoMatch
                    uptane.error.general.PublicKeysNoMatch
                    uptane.error.general.MetadataFileHasExpired
                    uptane.error.general.MetadataFileInvalidSignature
        '''
        path = 'public/' + url.replace(URL, '')

        self.__verify_root()
        self.__verify_targets(path)
        self.__verify_snapshot(path)
        self.__verify_timestamp(path)
