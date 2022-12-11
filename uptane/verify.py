import os
import tomli
import uptane.time
import uptane.error.general
import uptane.crypto.hash
import uptane.crypto.sign
import typing
import json
from Crypto.Cipher import AES
from Crypto.Cipher._mode_eax import EaxMode
from typing import Any


class Verification:
    '''
    This is the verification class of uptane, for verification, you would need access to 
    unexpired root metadata file:
    The various verification it performs are:
        Target Verification:
            Checks hash of File 
            Checks signature of File 

        Snapshot Verification  
            Checks signature of file 
            Checks hash of all targets metadata file against all snapshot hash 

        Timestamp Verification 
            Checks signature of file 
            Checks hash of Snapshot metadata file against hash in Timestamp metadata file 
    '''

    def __init__(self, root_metadata_file_path: str,
                 targets_files_dir_path: str, snapshot_metadata_file_path,
                 timestamp_metadata_file_path: str) -> None:
        '''
        Inits the verification class with the root metadata file
            Parameters:
                root_metadata_file_path (str): DUH!?
                image_file_path (str):
                targets_files_dir_path (str): directory where all target files exist
                snapshot_metadata_file_path (str):
                timestamp_metadata_file_path (str):

            Raises:
                FileNotFoundError - file not found
                tomli.TomlDecodeError - error in decoding toml file
                uptane.error.general.MetadataFileHasExpired

            Note:
                As of now only configured to handle key type ed25519 (only one key)
        '''
        with open(root_metadata_file_path, 'rb') as f:
            toml_dict = tomli.load(f)

            self.root_pub_key: str = toml_dict["signed"]["keys"][0]["keyid"]
            self.root_signed = toml_dict["signed"]
            self.root_signature: str = toml_dict["signature"]["sig"]

            self.targets_pub_key: str = toml_dict["signed"]["roles"]["targets"][
                "keys"][0]["keyid"]

            self.snapshot_pub_key: str = toml_dict["signed"]["roles"][
                "snapshot"]["keys"][0]["keyid"]

            self.timestamp_pub_key: str = toml_dict["signed"]["roles"][
                "timestamp"]["keys"][0]["keyid"]

        self.targets_files_dir_path = targets_files_dir_path
        self.snapshot_metadata_file_path = snapshot_metadata_file_path
        self.timestamp_metadata_file_path = timestamp_metadata_file_path

    def __verify_root(self):
        '''
        Verifies whether the root has signed with his key or not

            Raises:
                uptane.error.general.MetadataFileHasExpired
                uptane.error.general.MetadataFileInvalidSignature
        '''

        if uptane.time.fut_is_expired(int(self.root_signed["expires"])):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(self.root_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, \
            self.root_pub_key, self.root_signature):
            raise uptane.error.general.MetadataFileInvalidSignature

    def __targets_metadata_file_filter(self, value) -> bool:
        '''
        Keeps only targets metadata files in a list
        '''
        return "targets" in value

    def __verify_all_targets_files(self) -> None:
        '''
        Verifies whether target files came from trusted source or not

            Raises:
                uptane.error.general.MetadataFileHasExpired 
                uptane.error.general.MetadataFileInvalidSignature
                FileNotFoundError - when file is not found
                toml.TOMLDecodeError
                uptane.error.general.PublicKeysNoMatch
        '''

        targets_metadata_files = os.listdir(self.targets_files_dir_path)
        targets_metadata_files = filter(self.__targets_metadata_file_filter,
                                        targets_metadata_files)

        for targets_metadata_file in targets_metadata_files:

            with open(f'{self.targets_files_dir_path}/'+targets_metadata_file, 'rb') as f:
                toml_dict = tomli.load(f)
                cur_sig = toml_dict["signature"]["sig"]
                cur_public_key = toml_dict['signature']['keyid']
                cur_image_hash = toml_dict['signed']['image_hash']
                cur_signed = toml_dict['signed']
                buf_size = int(toml_dict["signed"]["image_buf_size"])
                cur_image_file = toml_dict["signed"]["image_name"]

            if self.targets_pub_key != cur_public_key:
                raise uptane.error.general.PublicKeysNoMatch

            if uptane.time.fut_is_expired(int(toml_dict["signed"]["expires"])):
                raise uptane.error.general.MetadataFileHasExpired

            if not uptane.crypto.sign.verify_sig_metadata(cur_signed, \
                uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, \
                cur_public_key, cur_sig):
                raise uptane.error.general.MetadataFileInvalidSignature

            if uptane.crypto.hash.get_file_hash(cur_image_file, uptane.crypto.hash.HashFunc.sha256, \
                                            buf_size) != cur_image_hash:
                raise uptane.error.general.FileHashNoMatch

    def __verify_snapshot(self) -> None:
        '''
        Verifies whether target file came from trusted source or not
            Throws:
                uptane.error.general.MetadataFileHasExpired 
                uptane.error.general.MetadataFileInvalidSignature
                FileNotFoundError - when file is not found
                toml.TOMLDecodeError
                uptane.error.general.PublicKeysNoMatch 
        '''
        cur_sig: str = ''
        cur_public_key: str = ''
        cur_signed: typing.Dict[str, typing.Any] = {}
        bufsize: int = 0

        with open(self.snapshot_metadata_file_path, 'rb') as f:
            toml_dict = tomli.load(f)
            cur_sig = toml_dict["signature"]["sig"]
            cur_public_key = toml_dict['signature']['keyid']
            cur_signed = toml_dict['signed']
            bufsize = int(toml_dict["signed"]["bufsize"])

        if self.snapshot_pub_key != cur_public_key:
            raise uptane.error.general.PublicKeysNoMatch

        if uptane.time.fut_is_expired(int(toml_dict["signed"]["expires"])):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(cur_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, cur_public_key, cur_sig):
            raise uptane.error.general.MetadataFileInvalidSignature

        # check hash of each metadata file
        for targets_metadata_file_k in cur_signed["targets"]:

            targets_metadata_file = self.targets_files_dir_path + '/' + targets_metadata_file_k
            targets_metadata_file_hash = cur_signed["targets"][
                targets_metadata_file_k]["hash"]

            if uptane.crypto.hash.get_file_hash(targets_metadata_file, \
                uptane.crypto.hash.HashFunc.sha256, bufsize) != targets_metadata_file_hash:
                raise uptane.error.general.FileHashNoMatch

    def __verify_timestamp(self) -> None:
        '''
        Verifies whether target file came from trusted source or not Parameters:
                path (str): path to targets metadata file
            
            Throws:
                    FileNotFoundError
                    tomli.TOMLDecodeError
                    uptane.error.general.FileHashNoMatch
                    uptane.error.general.PublicKeysNoMatch
                    uptane.error.general.MetadataFileHasExpired
                    uptane.error.general.MetadataFileInvalidSignature
       '''
        cur_sig: str = ''
        cur_public_key: str = ''
        cur_signed: typing.Dict[str, typing.Any] = {}
        bufsize: int = 0

        with open(self.timestamp_metadata_file_path, 'rb') as f:
            toml_dict = tomli.load(f)
            cur_sig = toml_dict["signature"]["sig"]
            cur_public_key = toml_dict['signature']['keyid']

            snapshot_metadata_file_hash = toml_dict["signed"][
                "snapshot_metadata_file_hash"]

            cur_signed = toml_dict['signed']
            bufsize = int(toml_dict["signed"]["bufsize"])

        if self.timestamp_pub_key != cur_public_key:
            raise uptane.error.general.PublicKeysNoMatch

        if uptane.time.fut_is_expired(int(toml_dict["signed"]["expires"])):
            raise uptane.error.general.MetadataFileHasExpired

        if not uptane.crypto.sign.verify_sig_metadata(cur_signed, \
            uptane.crypto.hash.HashFunc.sha256, uptane.crypto.sign.KeyType.ed25519, \
            cur_public_key, cur_sig):
            raise uptane.error.general.MetadataFileInvalidSignature

        if uptane.crypto.hash.get_file_hash(self.snapshot_metadata_file_path, \
                uptane.crypto.hash.HashFunc.sha256, bufsize) != snapshot_metadata_file_hash:
            raise uptane.error.general.FileHashNoMatch

    def verify(self) -> None:
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

        self.__verify_root()
        self.__verify_all_targets_files()
        self.__verify_snapshot()
        self.__verify_timestamp()


# RITUL
class ECUVerification:
    '''
        Class for verifying ECU manifest (signed by ECUs with their private key)
        vvm = {
            ecu1: {
            signed: { image_hash: "hash"},
            ecu_name: "",
            nonce: nonce,
            tag: tag,
            cipher_text: cipher_text
            },
            ecu2: {
            signed: {image_hash: "hash"},
            nonce: nonce,
            tag: tag,
            cipher_text: cipher_text
            }
            vin: "id-number"
        }
    '''

    def __init__(self, vehicle_manifest_json: typing.Any):
        pass

    def verify_ecus(self) -> bool:
        '''
        checks if ecus signatures are valid or not
        '''
        # get ecu_keys file
        ecu_keys = json.load(open('ecu_keys.json'))

        # vvm(dictionary format) received from Primary ECU

        for i in vvm:
            if i != "vin":
                sym_key = ecu_keys[i][sym_key]

                # run verification using sym_key over vvm[i]["signature"]
                cipher: Any = AES.new(sym_key,
                                      AES.MODE_EAX,
                                      nonce=vvm[i]["nonce"])

                if isinstance(cipher, EaxMode):
                    try:
                        cipher.decrypt_and_verify(
                            vvm[i]["cipher_text"],
                            received_mac_tag=vvm[i]["tag"])
                    except:
                        print(
                            "MAC does not match. The message has been tampered with or the key is incorrect."
                        )

                else:
                    print("Manifest signature verification failed")

        return True
