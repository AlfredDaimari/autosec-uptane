# This file will contain all the common code for all the automatic roles

from datetime import date
import typings
import pathlib
import toml


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

        '''

        cfg_pth = pathlib.Path(cfg)

        if not pathlib.Path.exists(cfg_pth):
            raise FileNotFoundError
        else:
            try:
                toml_dict = toml.load(f=cfg, _dict=dict)
                self.online_key = toml_dict["private_key"]
                self.role = toml_dict["role"]
                # TODO - comeup with cfg file structure

            except toml.TomlDecodeError:
                print(
                    "CFG error: The toml config file consists of syntax errors")
            except:
                print("Unknow error generated at AutoRole.__init__(self, cfg)")

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

            - Common functions are - sign_metadata, generate_signature,

    '''

    def __init__(self, cfg) -> None:
        cfg_pth = pathlib.Path(cfg)

        if not pathlib.Path.exists(cfg_pth):
            raise FileNotFoundError
        else:
            try:
                toml_dict = toml.load(f=cfg, _dict=dict)
                self.private_key = toml_dict["private_key"]
                self.role = toml_dict["role"]
                # TODO - comeup with cfg file structure

            except toml.TomlDecodeError:
                print(
                    "CFG error: The toml config file consists of syntax errors")
            except:
                print("Unknow error generated at AutoRole.__init__(self, cfg)")

    def generate_metadata_file(self, metadata_file: str) -> None:
        pass

    def sign_metadata(self, metadata_file: str) -> None:
        pass
