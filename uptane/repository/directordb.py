import flask 
import os 
import json
import uptane.verify
import typing
import uuid

directordb = flask.Flask(__name__)
directordb.config["MANIFEST_JSON"] = "manifest.json"
# read json file -> dict

def get_update_manifest(manifest:typing.Any)->bool:
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
#   vin: "id-number"
# }
#

# -- this is an ad-hoc implementation [need to change it]
@directordb.route('/manifest/', methods=["POST"])
def manifest():
    try:
        request_json = flask.request.json
        manifest_json_dict = json.load(request_json)
        verifier = uptane.verify.ECUVerification(manifest_json_dict)
        verifier.verify_ecus()

        if not get_update_manifest(manifest_json_dict):
            raise Exception("upto-date")
        
        # make a temporary directory to put all the metadata files
        temp_dir = str(uuid.uuid4())

        if not os.path.exists(f'./temp_met_dir/{temp_dir}'):
            os.mkdir(temp_dir)

    except Exception as e:
        return json.dumps({"error":{"type":str(e)}})
