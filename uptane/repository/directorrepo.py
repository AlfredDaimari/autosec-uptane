import flask
import os
import json
import uptane.verify
import uptane.roles.targets
import uptane.roles.snapshot
import uptane.roles.timestamp
import typing
import uuid
import shutil

directorrepo = flask.Flask(__name__)
directorrepo.config["MANIFEST_JSON"] = "manifest.json"
# read json file -> dict
MANIFEST_DICT:typing.Dict[str, typing.Any]

with open(directorrepo.config["MANIFEST_JSON"], "r") as f:
        MANIFEST_DICT = json.loads(f.read())

def get_update_manifest(manifest: typing.Any) -> bool:
    '''
    Function that returns the next manifest by reading the manifest.json file
        - if no new update is present, returns False, else true
        - updates manifest in place
    '''
    # manifest return structure
    #   {
    #       ecu1-image-hash:{
    #       image_name:
    #       image_url: http://ip:port/repo/reponame/image
    #       image_size:
    #       image_hash:
    #       image_hash_func:
    #       image_buf_size:
    #       image_sig_algo:
    #       image_version:
    #       },
    #       ecu2-image-hash:{}
    #
    #   }
    for ecu_hash in manifest:
        if not MANIFEST_DICT.get(ecu_hash, False):
            return False
        manifest[ecu_hash] = MANIFEST_DICT[ecu_hash]

    return True

# setting up the various roles
TARGETS: uptane.roles.targets.TargetsOnline
SNAPSHOT: uptane.roles.snapshot.SnapshotOnline
TIMESTAMP: uptane.roles.timestamp.TimestampOnline
AUTH_PUB_ED25519_KEY: str

# the car should send a json in the format
# {
#   ecu1: {
#   signed: { image_hash: "hash",},
#   signature: "dafkljlj"
#   },
#   ecu2: {
#   signed: {image_hash: "hash"},
#   signature: "dafkljlj"
#   }
#   vin: "id number"
# }
#


# -- this is an ad-hoc implementation [need to change it]
@directorrepo.route('/manifest/', methods=["POST"])
def manifest():
    try:
        request_json = flask.request.json
        vehicle_manifest_json_dict = json.load(request_json)
        vin = vehicle_manifest_json_dict["vin"]
        verifier = uptane.verify.ECUVerification(vehicle_manifest_json_dict)
        verifier.verify_ecus()

        if not get_update_manifest(vehicle_manifest_json_dict):
            raise Exception("up-to-date")

        # make a temporary directory to put all the metadata files
        temp_dir = str(uuid.uuid4())

        if not os.path.exists(f'director_met_repo/{temp_dir}'):
            os.mkdir(f'director_met_repo/{temp_dir}')
        else:
            os.rmdir(f'director_met_repo/{temp_dir}')
            os.mkdir(f'director_met_repo/{temp_dir}')

        # creating the metadata

        #TARGETS
        target_files = []
        for key in vehicle_manifest_json_dict:
            TARGETS.targetsoneline_reinit(vehicle_manifest_json_dict[key])
            imn = vehicle_manifest_json_dict[key]["image_name"]
            imv = vehicle_manifest_json_dict[key]["image_version"]
            metadata_file_name = f'director_met_repo/{temp_dir}/{imv}.{imn}.targets.toml'
            TARGETS.gen_signed_metadata_file(metadata_file_name)
            target_files.append(metadata_file_name)

        # SNAPSHOT
        SNAPSHOT.snapshotonline_reinit(target_files)
        snp_metadata_file_name = f'director_met_repo/{temp_dir}/0-0-1.{vin}.snapshot.toml'
        SNAPSHOT.gen_signed_metadata_file(snp_metadata_file_name)

        # TIMESTAMP
        TIMESTAMP.timestamponline_reinit(snp_metadata_file_name, vin)
        tms_metadata_file_name = f'director_met_repo/{temp_dir}/0-0-1.{vin}.timestamp.toml'
        TIMESTAMP.gen_signed_metadata_file(tms_metadata_file_name)

        # create the zip file
        shutil.make_archive(f'director_met_repo/{temp_dir}-zip', 'zip',
                            f'director_met_repo/{temp_dir}')

        # send the file
        flask.send_from_directory('director_met_repo', f'{temp_dir}-zip.zip')

    except Exception as e:
        return json.dumps({"error": {"type": str(e)}})


def setup_server(root_metadata_file: str, timestamp_cfg: str, snapshot_cfg: str,
                 targets_cfg: str, authpubkey: str):
    global TARGETS, SNAPSHOT, TIMESTAMP, AUTH_PUB_ED25519_KEY

    # make python open up a specific directory in the filesystem
    # the temporary repo will be used to generate metadata files
    if not os.path.exists('director_met_repo'):
        os.mkdir('director_met_repo')

    # setting up the various roles
    TARGETS = uptane.roles.targets.TargetsOnline(targets_cfg)
    SNAPSHOT = uptane.roles.snapshot.SnapshotOnline(snapshot_cfg)
    TIMESTAMP = uptane.roles.timestamp.TimestampOnline(timestamp_cfg)
    AUTH_PUB_ED25519_KEY = authpubkey
