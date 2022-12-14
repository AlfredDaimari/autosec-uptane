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
        self.signed_dict["bufsize"] = self.bufsize
        self.snapshot_metadata_file = None
        self.snapshot_metadata_file_dict = {}

    def timestamponline_reinit(self, snapshot_metadata_file: str,
                               id: str) -> None:
        self.auto__reinit(False)
        self.snapshot_metadata_file = snapshot_metadata_file

        with open(snapshot_metadata_file, "rb") as f:
            self.snapshot_metadata_file_dict = tomli.load(f)

        self.__generate_metadata()
        self.signed_dict["vin"] = id

    def __generate_metadata(self):

        self.signed_dict["bufsize"] = self.bufsize
        self.signed_dict["_type"] = "timestamp"

        self.signed_dict["snapshot_metadata_file_hash"] = \
        uptane.crypto.hash.get_file_hash(self.snapshot_metadata_file, \
        uptane.crypto.hash.HashFunc.sha256, self.bufsize)

        if uptane.time.fut_is_expired(
                int(self.snapshot_metadata_file_dict["signed"]["expires"])):
            raise MetadataFileHasExpired


class TimestampOffline(ManualRole):

    def __init__(self, cfg: str, snapshot_metadata_file: str) -> None:
        '''
        Init Timestamp Role, generates metadata for Snapshot metadata file

            Parameters:
                cfg (str): path to role configuration file
                image_cfg (str): path to image configuration file
                snapshot_metadata_file (str): path to snapshot metadata file

            Raises:
                tomli.TOMLDecodeError
        '''
        ManualRole.__init__(self, cfg, gen_img_metadata=False)
        self.snapshot_metadata_file = snapshot_metadata_file

        with open(snapshot_metadata_file, "rb") as f:
            self.snapshot_metadata_file_dict = tomli.load(f)

        self.signed_dict["bufsize"] = self.bufsize
        self.signed_dict["_type"] = "timestamp"
        self.__generate_metadata()

    def __generate_metadata(self) -> None:
        '''
        Populate the signed dict that will be converted to a toml file

        NOTE: Important - for now it verfies the targets image hash with only sha256 hash 
        using anyother func will ultimately make it fail
        '''
        self.signed_dict["snapshot_metadata_file_hash"] = \
        uptane.crypto.hash.get_file_hash(self.snapshot_metadata_file, \
        uptane.crypto.hash.HashFunc.sha256, self.bufsize)

        if uptane.time.fut_is_expired(
                int(self.snapshot_metadata_file_dict["signed"]["expires"])):
            raise MetadataFileHasExpired
