import flask
import os
import json
import zipfile
import uptane.verify
import uptane.crypto.sign
import uptane.crypto.hash
import tomli
import typing

imagerepo = flask.Flask(__name__)
imagerepo.config["UPLOAD_FOLDER"] = "image_repo"

ROOT_METADATA_FILE_PATH: str
AUTH_PUB_ED25519_KEY: str

def __compare_latest_timestamp_to_verified(reponame:str, latest_timestamp_file_path:str)->bool:
    '''
    Checks if the latest timestamp received, has been signed at greater time than current
        Parameters:
            reponame: name of the sub repo to store in
            latest_timestamp_file_path (str):
    '''
    latest_timestamp_file_dict:typing.Dict[str,typing.Any]
    stored_timestamp_file_dict:typing.Dict[str, typing.Any]
    with open(latest_timestamp_file_path, "rb") as f:
        latest_timestamp_file_dict = tomli.load(f)
 
    # check if timestamp file exists
    if not os.path.exists('image_repo/{}/timestamp.toml'.format(reponame)):
        return True

    with open('image_repo/{}/timestamp.toml'.format(reponame), "rb") as f:
        stored_timestamp_file_dict = tomli.load(f)

    return int(latest_timestamp_file_dict["signed"]["expires"]) > int(stored_timestamp_file_dict["signed"]["expires"])
        

# metadatafile verification lib functions
def __snapshot_metadata_file_filter(value) -> bool:
    '''
    Keeps only snapshot metadata file in list
    '''
    return "snapshot" in value


def __timestamp_metadata_file_filter(value) -> bool:
    '''
    filter for keeping only timestamp metadata file in list
    '''
    return "timestamp" in value


def get_snapshot_file_from_dirlist(file_list: list) -> str:
    '''
    gets the path of the snapshot file from the directory using uptane naming convention
    '''
    snapshot_files: list[str] = list(
        filter(__snapshot_metadata_file_filter, file_list))
    if len(snapshot_files) == 0:
        raise Exception("no snaphot metadata file found")

    if len(snapshot_files) > 1:
        raise Exception("more than one snapshot metadata file found")

    return snapshot_files[0]


def get_timestamp_file_from_dirlist(file_list: list) -> str:
    '''
    gets the path of the snapshot file from the directory using uptane naming convention
    '''
    timestamp_files: list[str] = list(
        filter(__timestamp_metadata_file_filter, file_list))
    if len(timestamp_files) == 0:
        raise Exception("no timstamp metadata file found")

    if len(timestamp_files) > 1:
        raise Exception("more than one timestamp metadata file found")

    return timestamp_files[0]


def remove_timestamp_file_from_repo(reponame: str) -> None:
    '''
    removes latest timestamp file from repo for the new latest timestamp file
    '''
    try:
        os.remove('image_repo/{}/timestamp.toml'.format(reponame))
    except FileNotFoundError:
        pass


# setting up different routes
@imagerepo.route('/repo/<reponame>/<filename>/', methods=["GET", "POST"])
def repo(reponame: str, filename: str):
    global ROOT_METADATA_FILE_PATH
    try:
        if not os.path.exists('image_repo/{}'.format(reponame)):
            os.mkdir("image_repo/{}".format(reponame))

        if flask.request.method == "GET":

            if not os.path.isfile(f'image_repo/{reponame}/{filename}'):
                return '{"error":{"type":"file_not_found"}}'
            else:
                return flask.send_from_directory(
                    imagerepo.config["UPLOAD_FOLDER"],
                    '{}/{}'.format(reponame, filename))
        else:
            # auth json will be of the form
            # {"signed":{"hash":"hash of zip file", "bufsize":int, "repo":"name of the sub repo"}, "keyid":"KNaCaMgAlZnFePbHCuHgAgAuPt", "signature":"some_signature"}
            auth_recv_dict = json.loads(flask.request.form["auth_json"])
            print("auth recv: ", auth_recv_dict)
            
            # -----
            # authentication
            if auth_recv_dict["keyid"] != AUTH_PUB_ED25519_KEY:
                return "", 401

            if auth_recv_dict["signed"]["repo"] != reponame:
                return "", 401

            if not uptane.crypto.sign.verify_sig_metadata(metadata=auth_recv_dict["signed"], \
                hashf=uptane.crypto.hash.HashFunc.sha256, ktype=uptane.crypto.sign.KeyType.ed25519, \
                pub_key=AUTH_PUB_ED25519_KEY, signature=auth_recv_dict["signature"]):
                return "", 401

            file = flask.request.files["file"]
            # the file sent has to be a folder that has been zipped, not a files that have been zipped

            file.save('image_repo/{}/{}'.format(reponame, filename))
            # now checking the file hash
            if not uptane.crypto.hash.get_file_hash('image_repo/{}/{}'.format(reponame, filename), \
                hashf=uptane.crypto.hash.HashFunc.sha256, bufsize=auth_recv_dict["signed"]["bufsize"]):
                return "", 401
            
            # --- 
            # unzipping the file
            with zipfile.ZipFile('image_repo/{}/{}'.format(reponame,
                                                            filename)) as zipO:
                zipO.extractall('image_repo/{}'.format(reponame))

            # removing the zip file
            os.remove('image_repo/{}/{}'.format(reponame, filename))

            # the directory that contains all files
            verify_dir = 'image_repo/{}/{}'.format(reponame,
                                                    filename.split('.')[0])
            recv_file_list = os.listdir(verify_dir)
            
            snapshot_file = get_snapshot_file_from_dirlist(recv_file_list)
            timestamp_file = get_timestamp_file_from_dirlist(recv_file_list)
            timestamp_file_path = '{}/{}'.format(verify_dir, timestamp_file)
            snapshot_file_path = '{}/{}'.format(verify_dir, snapshot_file)

            # last authentication step (preventing rollback attack)
            if not __compare_latest_timestamp_to_verified(reponame, timestamp_file_path):
                return "", 401
            
            print(timestamp_file_path, snapshot_file_path, verify_dir)

            # perform verification
            verifier = uptane.verify.Verification(root_metadata_file_path=ROOT_METADATA_FILE_PATH, \
                       timestamp_metadata_file_path=timestamp_file_path, \
                       snapshot_metadata_file_path=snapshot_file_path, \
                       targets_files_dir_path=verify_dir)
            
            verifier.verify()
            # move files to downloadable repo
            remove_timestamp_file_from_repo(reponame)
            os.rename(timestamp_file_path,
                      'image_repo/{}/timestamp.toml'.format(reponame))
            for file in os.listdir(verify_dir):
                os.rename(verify_dir + '/' + file,
                          'image_repo/{}/{}'.format(reponame, file))

            return '{"status":"success"}'

    except Exception as e:
        return json.dumps({"error": {"type": str(e)}})


def setup_server(root_metadata_file_path: str, authpubkey: str):
    global imagerepo
    global ROOT_METADATA_FILE_PATH, AUTH_PUB_ED25519_KEY
    # make python open up a specific directory in the filesystem
    if not os.path.exists('image_repo'):
        os.mkdir("image_repo")

    ROOT_METADATA_FILE_PATH = root_metadata_file_path
    AUTH_PUB_ED25519_KEY = authpubkey
    imagerepo.run(port=8080, debug=True)
