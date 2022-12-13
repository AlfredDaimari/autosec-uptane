# parse command-line arguments
import argparse
import typing
import uptane.roles.root
import uptane.roles.targets
import uptane.roles.snapshot
import uptane.roles.timestamp
import uptane.repository.imagerepo
import uptane.repository.directorrepo
import uptane.verify 
import uptane.crypto.sign
import uptane.crypto.hash
import subprocess
import json
import typing

def exec_send_to_image_repo(args)->None:
    '''
    Send to image repo using curl
        Parameters:
            auth_pem_key: private key for basic authenticaion 
            zip_file_path: zip file to send to the uptane image repo
    '''
    if args["authpubkey"] is None:
        print("--authpubkey not given")
        exit(1)
    
    with open(args["authpubkey"]) as f:
        auth_pub_key = f.read()

    if args["zipfpath"] is None:
        print("--zipfpath not given")
        exit(1)
    zip_file_path = args["zipfpath"]

    if args["authpemkey"] is None:
        print("--authpemkey not given")
        exit(1)
    with open(args["authpemkey"], "r") as f:
        auth_pem_key = f.read()

    if args["url"] is None:
        print("--url is not given")
        exit(1)
    url = args["url"]

    if args["repo"] is None:
        print("--repo is not given")
        exit(1)

    bufsize = 65536 # 8kb
    zip_file_hash = uptane.crypto.hash.get_file_hash(file_path=zip_file_path, \
                    hashf=uptane.crypto.hash.HashFunc.sha256, bufsize=bufsize)
    signed_dict:typing.Dict[str,str | int] = {"bufsize":bufsize, "hash":zip_file_hash, "repo":args["repo"]}
    signature = uptane.crypto.sign.sign_metadata(signed_dict,\
                hashf=uptane.crypto.hash.HashFunc.sha256, ktype=uptane.crypto.sign.KeyType.ed25519,\
                key=auth_pem_key)
    auth_json = json.dumps({"signed":signed_dict, "keyid":auth_pub_key, "signature":signature})
    process = subprocess.Popen(['curl', '-X', 'POST', "-F", "file=@{}".format(zip_file_path), \
                "-F", "auth_json={}".format(json.dumps(auth_json)), url],stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE)
    stdout, _ = process.communicate()
    print(stdout)

def exec_offline_metadata_gen(args: typing.Dict[str, typing.Any]):
    '''
    Execute offline metadata program
    '''
    if args["rcfg"] is None:
        print("--rcfg command not given, role config file not given")
        exit(1)

    if args["name"] is None:
        print("--name argument not given")
        exit(1)

    if args["role"] == "root":
        rg = uptane.roles.root.Root(args["rcfg"])
        rg.gen_signed_metadata_file(args["name"])

    if args["role"] == "timestamp":

        if args.get("smetafile") is None:
            print("--smetafile argument not given")
            exit(1)

        tg = uptane.roles.timestamp.TimestampOffline(args["rcfg"],
                                                     args["smetafile"])
        tg.gen_signed_metadata_file(args["name"])

    if args["role"] == "snapshot":

        if args.get("tmetafile") is None:
            print("--tmetafile argument not given")
            exit(1)

        sg = uptane.roles.snapshot.SnapshotOffline(args["rcfg"],
                                                   args["tmetafile"])
        sg.gen_signed_metadata_file(args["name"])

    if args["role"] == "targets":

        if args["icfg"] is None:
            print("--icfg argument is not given")
            exit(1)

        tg = uptane.roles.targets.TargetsOffline(args["rcfg"], args["icfg"])
        tg.gen_signed_metadata_file(args["name"])


def exec_server_gen(args: typing.Dict[str, typing.Any]):
    '''
    Execute server generating program
    '''
    if args["stype"] is None:
        print("--stype argument is not given")
        exit(1)

    if args["rmetafile"] is None:
        print("--rmetafile argument is not given")
        exit(1)

    if args["authpubkey"] is None:
        print("--authpubkey argument is not given")
        exit(1)

    # getting public key
    authpubkey = open(args["authpubkey"], "r").read()
    if args["stype"] == "image":
        uptane.repository.imagerepo.setup_server(args["rmetafile"], authpubkey)

    if args["stype"] == "director":
        if (args["ontscfg"] is None) or (args["onsnapcfg"] is
                                         None) or (args["ontarcfg"] is None):
            print("--ontscfg --onsnapcfg --ontarcfg arguments not given")
            exit(1)

        uptane.repository.directorrepo.setup_server(root_metadata_file=args["rmetafile"], \
                timestamp_cfg=args["ontscfg"], snapshot_cfg=args["onsnapcfg"], \
                targets_cfg=args["ontarcfg"], authpubkey=authpubkey)


def exec_verify_metadata(args: typing.Dict[str, typing.Any]):
    '''
    Execute verification program
    '''
    if args.get("smetafile") is None:
        print("--smetafile argument not given")
        exit(1)

    if args.get("tsmetafile") is None:
        print("--tsmetafile argument not given")
        exit(1)

    if args.get("tmetadir") is None:
        print("--tmetadir argument not given")
        exit(1)

    if args.get("rmetafile") is None:
        print("--rmetafile argument not given")
        exit(1)

    vef = uptane.verify.Verification(root_metadata_file_path=args["rmetafile"], \
        targets_files_dir_path=args["tmetadir"], snapshot_metadata_file_path=args["smetafile"], \
        timestamp_metadata_file_path=args["tsmetafile"])
    vef.verify()


def main():
    print("autosec_uptane version 0.0.2")

    # argument parser for generating metadata
    parser = argparse.ArgumentParser(
        prog="uptane",
        description=
        "a cmd program for creating metadata, image repo, director repo for uptane framework",
        usage="%(prog)s [command] [options]")

    parser.add_argument(
        "--role",
        help="the role ? [timestamp, snapshot, targets, root]",
        choices=["timestamp", "snapshot", "targets", "root"],
    )
    parser.add_argument(
        "--rcfg",
        help="the config file for the role?",
    )
    parser.add_argument("--icfg", help="the config file for the image?")
    parser.add_argument("--offline",
                        help="whether the role is online or offline",
                        action="store_true")

    parser.add_argument(
        "-t",
        "--tmetafile",
        action="append",
        help="names of all target metadata file wanted in snapshot")

    # verification arguments
    parser.add_argument(
        "--tmetadir",
        help="dir of targets metadata, images [choice for verify]")
    parser.add_argument("-s", "--smetafile", help="the snapshot metadata file")
    parser.add_argument("--tsmetafile", help="the timestamp metadata file")
    parser.add_argument("-r", "--rmetafile", help="the root metadata file")

    parser.add_argument("--name", help="name of the metadata file to output to")

    # server arguments
    parser.add_argument("--stype",
                        help="the type of server",
                        choices=["image", "director"])
    parser.add_argument("--authpubkey",
                        help="authentication key to be used for server")
    parser.add_argument("--ontscfg", help="online cfg for timestamp role")
    parser.add_argument("--onsnapcfg", help="online cfg for snapshot role")
    parser.add_argument("--ontarcfg", help="online cfg for targets role")

    parser.add_argument(
        "command",
        help=
        "metadata - command for generating metadata, server - command for generating a server, verify - command for verifying metadata, send - command for sending to server"
    )

    # send arguments
    parser.add_argument('--url', help='url for sending the file to')
    parser.add_argument('--authpemkey', help='private key for authenticating with server')
    parser.add_argument('--zipfpath', help='path of the zip file to send')
    parser.add_argument('--repo', help="name of the repo to send to")
    # 5th argument for send is --authpubkey, defined in server arguments as well
    
    # parsing args
    args = parser.parse_args()
    args = vars(args)
    print(args)

    if args["command"] == "metadata" and args["offline"] and args[
            "role"] is not None:
        exec_offline_metadata_gen(args)

    elif args["command"] == "server":
        exec_server_gen(args)
    elif args["command"] == "verify":
        exec_verify_metadata(args)
    elif args["command"] == "send":
        exec_send_to_image_repo(args)
    else:
        print(f'{args["command"]} not recognized')


if __name__ == "__main__":
    main()
