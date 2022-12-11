import flask
import os
import json
import zipfile
import uptane.verify

inventorydb = flask.Flask(__name__)
inventorydb.config["UPLOAD_FOLDER"] = "public_repo"

ROOT_METADATA_FILE_PATH:str

def __snapshot_metadata_file_filter(value) -> bool:
    '''
    Keeps only snapshot metadata file in list
    '''
    return "snapshot" in value

def __timestamp_metadata_file_filter(value) -> bool:
    '''
    filter for keeping only timestamp metadata file in list
    '''
    return "snapshot" in value

def get_snapshot_file_from_dirlist(file_list:list)->str:
    '''
    gets the path of the snapshot file from the directory using uptane naming convention
    '''
    snapshot_files:list[str] = list(filter(__snapshot_metadata_file_filter, file_list))
    if len(snapshot_files) == 0:
        raise Exception("no snaphot metadata file found")

    if len(snapshot_files) > 1:
        raise Exception("more than one snapshot metadata file found")

    return snapshot_files[0]

def get_timestamp_file_from_dirlist(file_list:list)->str:
    '''
    gets the path of the snapshot file from the directory using uptane naming convention
    '''
    timestamp_files:list[str] = list(filter(__timestamp_metadata_file_filter, file_list))
    if len(timestamp_files) == 0:
        raise Exception("no timstamp metadata file found")

    if len(timestamp_files) > 1:
        raise Exception("more than one timestamp metadata file found")
    
    return timestamp_files[0]
 
def remove_timestamp_file_from_repo(reponame:str)->None:
    '''
    removes latest timestamp file from repo for the new latest timestamp file
    '''
    try:
        os.remove('public_repo/{}/timestamp.toml'.format(reponame))
    except FileNotFoundError:
        pass

# setting up different routes
@inventorydb.route('/repo/<reponame>/<filename>/', methods=["GET", "POST"])
def repo(reponame:str, filename:str):
    global ROOT_METADATA_FILE_PATH
    try:
        if not os.path.exists('./public_repo/{}'.format(reponame)):
            os.mkdir("./public_repo/{}".format(reponame))

        if flask.request.method == "GET":

            if not os.path.isfile(f'./public_repo/{reponame}/{filename}'):
                return '{"error":{"type":"file_not_found"}}'
            else:
                return flask.send_from_directory(
                    inventorydb.config["UPLOAD_FOLDER"],
                    '{}/{}'.format(reponame, filename))
        else:
            file = flask.request.files["file"]
            # the file sent has to be a folder that has been zipped, not a files that have been zipped

            file.save('public_repo/{}/{}'.format(reponame, filename))
            
            # unzipping the file
            with zipfile.ZipFile('public_repo/{}/{}'.format(reponame, filename)) as zipO:
                zipO.extractall('public_repo/{}'.format(reponame))

            # running the verification mechanism
            os.remove('public_repo/{}/{}'.format(reponame, filename))
            
            # rewrite this ad-hoc code, as it forces to take .zip file name
            verify_dir = 'public_repo/{}/{}'.format(reponame, filename.split('.')[0])           
            recv_file_list = os.listdir(verify_dir)
            snapshot_file = get_snapshot_file_from_dirlist(recv_file_list)
            timestamp_file = get_timestamp_file_from_dirlist(recv_file_list)
            
            timestamp_file_path = '{}/{}'.format(verify_dir, timestamp_file) 
            snapshot_file_path = '{}/{}'.format(verify_dir, snapshot_file)
            
            # perform verification
            verifier = uptane.verify.Verification(root_metadata_file_path=ROOT_METADATA_FILE_PATH, \
                       timestamp_metadata_file_path=timestamp_file_path, \
                       snapshot_metadata_file_path=snapshot_file_path, \
                       targets_files_dir_path=verify_dir)
            
            # move files to downloadable repo
            remove_timestamp_file_from_repo(reponame)
            os.rename(timestamp_file_path, 'public_repo/{}/timestamp.toml'.format(reponame))
            for file in os.listdir(verify_dir):
                os.rename(verify_dir+'/'+file, 'public_repo/{}/{}'.format(reponame, file))

            return '{"status":"success"}'

    except Exception as e:
        return json.dumps({"error": {"type": str(e)}})


def setup_server(root_metadata_file_path):
    global inventorydb
    global ROOT_METADATA_FILE_PATH
    # make python open up a specific directory in the filesystem
    if not os.path.exists('./public_repo'):
        os.mkdir("./public_repo")
   
    ROOT_METADATA_FILE_PATH = root_metadata_file_path
    inventorydb.run(port=8080, debug=True)


