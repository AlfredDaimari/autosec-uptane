# This file will contain all the common code for all the automatic roles



class Uptane:
    """
        Uptane class
            
            - Implements common functionality between non-human automatic roles (Snapshot, 
            Timestamp,Targets)
        
            - Common functions are - revoke_key, get_time_to_expr, update_signature
    """

    def __init__(self) -> None:
        pass


    def revoke_key(self, key_id):
        pass

    def get_time_to_expr(self, key_id:str):
        pass

    def update_signature(self, salt:str ,key_id:str):
        pass

    def replace_online_key(self, new_key:str, key_id_to_replace:str):
        pass
    
    def add_online_key(self, new_key:str):
        pass
