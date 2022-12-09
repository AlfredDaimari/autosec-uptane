import flask 
import os 
import json

directordb = flask.Flask(__name__)
directordb.config["MANIFEST_JSON"] = "manifest.json"

# make python open up a specific directory in the filesystem

# the temporary repo will be used to generate metadata files
if not os.path.exists('./temporary_repo'):
    os.mkdir('./temporary_repo')


# the car should send a json in the format
# {
#   ecu1: {
#   signed: { image_hash: "hash"},
#   signature: "dafkljlj"
#   },
#   ecu2: {
#   signed: {image_hash: "hash"},
#   signature: "dafkljlj"
#   }
#   vin: "id-number"
# }
#
@directordb.route('/manifest/', methods=["POST"])
def manifest():
    try:
        return ''
    except Exception as e:
        return json.dumps({"error":{"type":str(e)}})
