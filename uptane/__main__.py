# parse command-line arguments
import argparse
import typing
import uptane.roles.root
import uptane.roles.targets
import uptane.roles.snapshot
import uptane.roles.timestamp
#import uptane.repository.inventorydb
#import uptane.repository.directordb
import uptane.verify


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
    pass


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
    print("autosec_uptane version 0.0.1")

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

    parser.add_argument(
        "--tmetadir",
        help="dir of targets metadata, images [choice for verify]")
    parser.add_argument("-s", "--smetafile", help="the snapshot metadata file")
    parser.add_argument("--tsmetafile", help="the timestamp metadata file")
    parser.add_argument("-r", "--rmetafile", help="the root metadata file")
    parser.add_argument("--name", help="name of the metadata file to output to")
    parser.add_argument(
        "command",
        help=
        "metadata - command for generating metadata, server - command for generating a server, verify - command for verifying metadata"
    )

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
    else:
        print(f'{args["command"]} not recognized')


if __name__ == "__main__":
    main()
