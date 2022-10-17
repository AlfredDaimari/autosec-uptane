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


def __sort_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    sorted_metadata = dict(sorted(metadata.items()))
    for key in sorted_metadata:
        if type(sorted_metadata[key]) == type(dict):
            sorted_metadata[key] = __sort_metadata(sorted_metadata[key])
    return sorted_metadata


def sign_metadata(metadata: Dict[str, Any], hashf: HashFunc, ktype: KeyType,
                  key: str) -> str:
    '''
    Sign metadata that is given in the form of a dictionary
        Parameters:
            metadata (Dict[str, Any]): metadata in the form of python dict
            hashf (uptane.crypto.hash.HashFunc): hash function to be used
            ktype (uptane.crypto.sign.KeyType): the ktype, this would determine the signing algo
            key (str): the private key in pem format

        Returns:
            str: signature in base64
    '''
    metadata = __sort_metadata(metadata)
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


def verify_sig_metadata(metadata: Dict[str, Any], hashf: HashFunc,
                        ktype: KeyType, pub_key: str, signature: str) -> bool:
    '''
    Verify signed metadata that is given in the form of a dictionary 
        Parameters:
            metadata (Dict[str, Any])" metadata in the form of a python dict 
            hashf (uptane.crypto.hash.HashFunc): hash function to be used
            ktype: (uptane.crypto.sign.Keytype): the ktype, determine signing algo used for verfication
            key (str): the public key in pem format
            signature (str): the signature received
    '''
    metadata = __sort_metadata(metadata)
    json_payload = json.dumps(metadata)

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
        public_key = ECC.import_key(pub_key)
        verifier = eddsa.new(public_key, b'rfc8032')
        try:
            verifier.verify(bytes(hashed_payload, 'utf-8'),
                            base64.b64decode(signature))
            return True
        except ValueError:
            return False

    return False
