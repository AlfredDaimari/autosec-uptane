import flask 
import os 
import json

directordb = flask.Flask(__name__)
directordb.config["MANIFEST_JSON"] = "manifest.json"
