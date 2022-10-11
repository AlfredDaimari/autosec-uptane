import enum
import hashlib


class HashFunc(enum.Enum):
    sha256 = 1
    md5 = 2


def get_file_hash(file_path: str, hashf: HashFunc, bufsize: int) -> str:
    '''
        Get hash of a file
            Parameters:
                file_path (str): the path of the file to hash
                hashf (HashFunc): the hash function to be used
                bufsize (int): buffer read sizes
            Retures:
                str: the hash of the file 
        '''
    hashfunc = hashlib.sha256()  # using sha256 as default

    if hashf == HashFunc.sha256:
        hashfunc = hashlib.sha256()

    if hashf == HashFunc.md5:
        hashfunc = hashlib.md5()

    # ? add more hash functions ??

    image_file = open(file_path, "rb")

    while True:
        data = image_file.read(bufsize)
        if not data:
            break
        hashfunc.update(data)

    return hashfunc.hexdigest()
