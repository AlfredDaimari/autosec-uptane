#
# Root service
#   - root service keys need to be updated and used the least amongst all services
#   - will generate root.toml file (using toml files to make it human readable)
#
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
        pass
