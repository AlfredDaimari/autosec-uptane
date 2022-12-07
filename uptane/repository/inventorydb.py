import flask
import os
import json

inventorydb = flask.Flask(__name__)
inventorydb.config["UPLOAD_FOLDER"] = "public_repo"

# make python open up a specific directory in the filesystem

if not os.path.exists('./public_repo'):
    os.mkdir("./public_repo")


# setting up different routes
@inventorydb.route('/repo/<reponame>/<filename>/', methods=["GET", "POST"])
def repo(reponame, filename):
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
            # make it take a zip folder
            file.save('public_repo/{}/{}'.format(reponame, filename))
            # perform verification - create a python sub-process for verification
            return '{"status":"success"}'

    except Exception as e:
        return json.dumps({"error": {"type": str(e)}})
