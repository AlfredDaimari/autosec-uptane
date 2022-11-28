#
# Root service
#   - root service keys need to be updated and used the least amongst all services
#   - will generate root.toml file (using toml files to make it human readable)
# NOTE: only accepts one key currenlty
import uptane.roles.role


class Root(uptane.roles.role.ManualRole):

    def __init__(self, cfg: str) -> None:
        '''
        Init root class for generating metadata file
            
            Parameters:
                cfg (str): path to root node configuration file

            Raises:
                FileNotFoundError - when toml file is not found
                tomli.TOMLDecodeError - when toml has syntax error
        '''
        uptane.roles.role.ManualRole.__init__(self, cfg, False)

        self.__gen_metadata()

    def __gen_metadata(self):
        '''
        Generate metadata for the different roles using cfg file
        '''
        self.signed_dict["keys"] = []
        self.signed_dict["keys"].append({
            "keytype": "ed25519",
            "keyid": self.public_key
        })

        # inserting keys for various roles
        self.signed_dict["roles"] = {}
        self.signed_dict["roles"]["targets"] = {}
        self.signed_dict["roles"]["targets"]["keys"] = []
        self.signed_dict["roles"]["targets"]["keys"].append({"keytype":     \
        self.cfg_toml_dict["targets"]["keytype"], "keyid":     \
        self.cfg_toml_dict["targets"]["public_key"]})
        self.signed_dict["roles"]["targets"]["threshold"] = 1

        self.signed_dict["roles"]["snapshot"] = {}
        self.signed_dict["roles"]["snapshot"]["keys"] = []
        self.signed_dict["roles"]["snapshot"]["keys"].append({"keytype":    \
        self.cfg_toml_dict["snapshot"]["keytype"], "keyid":     \
        self.cfg_toml_dict["snapshot"]["public_key"]})
        self.signed_dict["roles"]["snapshot"]["threshold"] = 1

        self.signed_dict["roles"]["timestamp"] = {}
        self.signed_dict["roles"]["timestamp"]["keys"] = []
        self.signed_dict["roles"]["timestamp"]["keys"].append({"keytype":    \
        self.cfg_toml_dict["timestamp"]["keytype"], "keyid":     \
        self.cfg_toml_dict["timestamp"]["public_key"]})
        self.signed_dict["roles"]["timestamp"]["threshold"] = 1
