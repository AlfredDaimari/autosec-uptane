# snapshot role
import uptane.crypto.hash
import uptane.time
from uptane.roles.role import AutoRole, TarSnapManualRole
import tomli
from uptane.error.general import FileHashNoMatch, MetadataFileHasExpired

ONLINE_SNAPSHOT_SPEC_VERSION = "0.0.1"
OFFLINE_SNAPSHOT_SPEC_VERSION = "0.0.1"


class SnapshotOnline(AutoRole):
    '''
        Class inheriting the Snapshot role of Uptane
    '''

    def __init__(self, cfg: str) -> None:
        AutoRole.__init__(self, cfg)

    def sign_targets_metadata(self, metadata_file) -> None:
        '''
        Sign the metadata file received from Target Role
        '''
        self.sign_metadata(metadata_file)


class SnapshotOffline(TarSnapManualRole):
    '''
    Snapshot Offline Role
    This will role will sign metadata file generated by targets and put in toml file
    '''

    def __init__(self, cfg: str, targets_metadata_files: list[str]) -> None:
        '''
        Generate the Snapshot metadata file for signing
            Parameters:
                cfg (str): path to role config 
                targets_metadata_files (str): list of a path to target metadata file

            Raises:
                FileNotFoundError
                tomli.TOMLDecodeError
        '''
        TarSnapManualRole.__init__(self, cfg)
        self.targets_metadata_files = targets_metadata_files
        self.targets = {}
        self.signed_dict["targets"] = {}

        for targets_metadata_file in targets_metadata_files:
            with open(targets_metadata_file, "rb") as f:

                # loading toml of all targets_metadata_file
                self.targets[targets_metadata_file] = tomli.load(f)

                self.signed_dict["spec_version"] = OFFLINE_SNAPSHOT_SPEC_VERSION
                self.signed_dict["_type"] = "snapshot"
                self.signed_dict["bufsize"] = self.bufsize

        self.__generate_metadata()

    def __generate_metadata(self) -> None:
        '''
        Populate the signed dict that will be converted to a toml file

        NOTE: Important - for now it verfies the targets image hash with only sha256 hash 
        using anyother func will ultimately make it fail
        '''
        for targets_metadata_file in self.targets_metadata_files:

            self.signed_dict["targets"][targets_metadata_file] = {}
            self.signed_dict["targets"][targets_metadata_file]["hash"] = \
            uptane.crypto.hash.get_file_hash(targets_metadata_file, \
            uptane.crypto.hash.HashFunc.sha256, self.bufsize)

            if uptane.time.fut_is_expired(
                    int(self.targets[targets_metadata_file]["signed"]
                        ["expires"])):
                raise MetadataFileHasExpired
