# This file will contain all the common code for all the automatic roles

from datetime import date

class Role:
    '''
        Automatic Role Common Functions Class
            
            - Implements common functionality between non-human automatic roles (Snapshot, 
              Timestamp, Targets)
        
            - Common functions are - revoke_key, get_time_to_expr, generate_signature,
              replace_online_key, add_online_key, sign_metadata
    '''

    def __init__(self) -> None:
        pass


    def revoke_key(self, key_id) -> None:
        pass

    def get_time_to_expr(self, key_id:str) -> date:
        pass

    def generate_signature(self, key_id:str) -> None:
        pass

    def replace_online_key(self, new_key:str, key_id_to_replace:str) -> None:
        pass
    
    def add_online_key(self, new_key:str) -> None:
        pass

    def sign_metadata(self, metadata_file) -> None:
        pass
