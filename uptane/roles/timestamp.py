# this file will implement the timestamp role for uptane

from uptane.roles.role import AutoRole, ManualRole
from uptane.error.general import MetadataFileHasExpired
import uptane.crypto.hash
import tomli
import uptane.time

OFFLINE_TIMESTAMP_SPEC_VERSION = "0.0.1"
ONLINE_TIMESTAMP_SPEC_VERSION = "0.0.1"


class TimestampOnline(AutoRole):
    '''
    Timestamp class 
    This will sign metadata received from Snapshot Role
    '''

    def __init__(self, cfg: str) -> None:
        AutoRole.__init__(self, cfg)

    def sign_snapshot_metadata(self, snapshot_metadata_file) -> None:
        '''
        Sign metadata file received from Snapshot
        '''
        self.sign_metadata(snapshot_metadata_file)


class TimestampOffline(ManualRole):

    def __init__(self, cfg: str, image_cfg: str,
                 snapshot_metadata_file: str) -> None:
        '''
        Init Timestamp Role, generates metadata for Snapshot metadata file

            Parameters:
                cfg (str): path to role configuration file
                image_cfg (str): path to image configuration file
                snapshot_metadata_file (str): path to snapshot metadata file

            Raises:
                tomli.TOMLDecodeError
        '''
        ManualRole.__init__(self, cfg)
        self.snapshot_metadata_file = snapshot_metadata_file

        with open(snapshot_metadata_file, "rb") as f:
            self.snapshot_metadata_file_dict = tomli.load(f)

        with open(image_cfg, "rb") as f:
            toml_dict = tomli.load(f)
            self.signed_dict["image_name"] = toml_dict["_name"]
            self.signed_dict["image_url"] = toml_dict["_url"]
            self.signed_dict["image_version"] = toml_dict["_version"]
            self.signed_dict["spec_version"] = OFFLINE_TIMESTAMP_SPEC_VERSION
            self.signed_dict["_type"] = "timestamp"

            self.__gen_cfg_metadata()

    def __gen_cfg_metadata(self) -> None:
        '''
        Populate the signed dict that will be converted to a toml file

        NOTE: Important - for now it verfies the targets image hash with only sha256 hash 
        using anyother func will ultimately make it fail
        '''
        self.signed_dict["snapshot_metadata_file_hash"] = \
        uptane.crypto.hash.get_file_hash(self.snapshot_metadata_file, \
        uptane.crypto.hash.HashFunc.sha256, self.bufsize)

        if uptane.time.fut24_is_expired(
                int(self.snapshot_metadata_file_dict["signed"]["expires"])):
            raise MetadataFileHasExpired
