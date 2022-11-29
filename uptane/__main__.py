# parse command-line arguments
import argparse
import roles.targets
import roles.snapshot


def main():
    print("autosec_uptane version 0.0.1")
    parser = argparse.ArgumentParser(
        prog="uptane",
        description="a cmd program for creating metadata for uptane framework")
    parser.add_argument("--role",
                        help="the role ? [timestamp, snapshot, targets]",
                        choices=["timestamp", "snapshot", "targets"], required=True)
    parser.add_argument("--rcfg", help="the config file for the role?", required=True)
    parser.add_argument("--icfg", help="the config file for the image?", required=True)
    parser.add_argument("--offline",
                        help="whether the role is online or offline",
                        action="store_true")
    parser.add_argument("--tmetafile", help="the targets metadata file")
    parser.add_argument("--smetafile", help="the snapshot metadata file")
    parser.add_argument("name", help="name of the metadata file to output to")
    args = parser.parse_args()
    args = vars(args)
    print(args)

    if args["role"] == "timestamp" and args["offline"]:
        if args.get("smetafile") is None:
            print("--smetafile argument not given")

    if args["role"] == "snapshot" and args["offline"]:
        if args.get("tmetafile") is None:
            print("--tmetafile argument not given")
            exit(1)

        sg = roles.snapshot.SnapshotOffline(args["rcfg"], args["icfg"], args["tmetafile"])
        sg.gen_signed_metadata_file(args["name"])


    if args["role"] == "targets" and args["offline"]:
        tg = roles.targets.TargetsOffline(args["rcfg"], args["icfg"])
        tg.gen_signed_metadata_file(args["name"])


if __name__ == "__main__":
    main()
