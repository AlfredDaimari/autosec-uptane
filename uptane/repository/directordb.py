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

directordb = flask.Flask(__name__)
directordb.config["MANIFEST_JSON"] = "manifest.json"
# read json file -> dict


def get_update_manifest(manifest: typing.Any) -> bool:
    '''
    Function that returns the next manifest by reading the manifest.json file
        - if no new update is present, returns False, else true
        - updates manifest in place
    '''
    # manifest return structure
    #   {
    #       ecu1:{
    #       image_name:
    #       image_url: http://ip:port/repo/reponame/image
    #       image_size:
    #       image_hash:
    #       image_hash_func:
    #       image_buf_size:
    #       image_sig_algo:
    #       image_version:
    #       },
    #       ecu2:{}
    #
    #   }
    return False


# make python open up a specific directory in the filesystem
# the temporary repo will be used to generate metadata files
if not os.path.exists('./temp_met_dir'):
    os.mkdir('./temp_met_dir')

# setting up the various roles
TARGETS = uptane.roles.targets.TargetsOnline('online_targets.cfg')
SNAPSHOT = uptane.roles.snapshot.SnapshotOnline('online_snapshot.cfg')
TIMESTAMP = uptane.roles.timestamp.TimestampOnline('online_timestamp.cfg')

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
@directordb.route('/manifest/', methods=["POST"])
def manifest():
    try:
        request_json = flask.request.json
        manifest_json_dict = json.load(request_json)
        vin = manifest_json_dict["vin"]
        verifier = uptane.verify.ECUVerification(manifest_json_dict)
        verifier.verify_ecus()

        if not get_update_manifest(manifest_json_dict):
            raise Exception("up-to-date")

        # make a temporary directory to put all the metadata files
        temp_dir = str(uuid.uuid4())

        if not os.path.exists(f'./temp_met_dir/{temp_dir}'):
            os.mkdir(f'./temp_met_dir/{temp_dir}')
        else:
            os.rmdir(f'./temp_met_dir/{temp_dir}')
            os.mkdir(f'./temp_met_dir/{temp_dir}')

        # creating the metadata

        #TARGETS
        target_files = []
        for key in manifest_json_dict:
            TARGETS.targetsoneline_reinit(manifest_json_dict[key])
            imn = manifest_json_dict[key]["image_name"]
            imv = manifest_json_dict[key]["image_version"]
            metadata_file_name = f'temp_met_dir/{temp_dir}/{imv}.{imn}.targets.toml'
            TARGETS.gen_signed_metadata_file(metadata_file_name)
            target_files.append(metadata_file_name)

        # SNAPSHOT
        SNAPSHOT.snapshotonline_reinit(target_files)
        snp_metadata_file_name = f'temp_met_dir/{temp_dir}/0-0-1.{vin}.snapshot.toml'
        SNAPSHOT.gen_signed_metadata_file(snp_metadata_file_name)

        # TIMESTAMP
        TIMESTAMP.timestamponline_reinit(snp_metadata_file_name, vin)
        tms_metadata_file_name = f'temp_met_dir/{temp_dir}/0-0-1.{vin}.timestamp.toml'
        TIMESTAMP.gen_signed_metadata_file(tms_metadata_file_name)

        # create the zip file
        shutil.make_archive(f'temp_met_dir/{temp_dir}-zip', 'zip', f'temp_met_dir/{temp_dir}')
        
        # send the file
        flask.send_from_directory('temp_met_dir', f'{temp_dir}-zip.zip')

    except Exception as e:
        return json.dumps({"error": {"type": str(e)}})
