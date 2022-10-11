# Code related to generating signatures
from enum import Enum
from typing import Any, Dict
import json
from uptane.crypto.hash import HashFunc
from Crypto.Signature import eddsa
import hashlib
import base64
from Crypto.PublicKey import ECC


class KeyType(Enum):
    ed25519 = 1


def sign_metadata(metadata: Dict[str, Any], hashf: HashFunc, ktype: KeyType,
                  key: str) -> str:
    '''
    Sign metadata that is given in the form of a dictionary
        Parameters:
            metadata (Dict[str, Any]): metadata in the form of python dict
            hashf (uptane.crypto.hash.HashFunc): hash function to be used
            ktype (uptane.crypto.KeyType): the ktype, this would determine the signing algo
            key (str): the private key in pem format

        Returns:
            str: signature in base64
    '''
    json_payload = json.dumps(metadata)
    signature = b''

    hashed_payload: str = ''
    if hashf == HashFunc.sha256:
        s256 = hashlib.sha256()
        s256.update(bytes(json_payload, 'utf-8'))
        hashed_payload = s256.hexdigest()

    if hashf == HashFunc.md5:
        hmd5 = hashlib.md5()
        hmd5.update(bytes(json_payload, 'utf-8'))
        hashed_payload = hmd5.hexdigest()

    if ktype == KeyType.ed25519:
        private_key = ECC.import_key(key)
        signor = eddsa.new(private_key, b'rfc8032')
        signature = signor.sign(bytes(hashed_payload, 'utf-8'))

    signature = base64.b64encode(signature)
    return signature.decode('utf-8')
