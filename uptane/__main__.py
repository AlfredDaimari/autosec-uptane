# parse command-line arguments
import argparse
import roles.targets


def main():
    print("autosec_uptane version 0.0.1")
    parser = argparse.ArgumentParser(
        prog="uptane",
        description="a cmd program for creating metadata for uptane framework")
    parser.add_argument("role",
                        help="the role ? [timestamp, snapshot, targets]",
                        choices=["timestamp", "snapshot", "targets"])
    parser.add_argument("rolecfg", help="the config file for the role?")
    parser.add_argument("imagecfg", help="the config file for the image?")
    parser.add_argument("name", help="name of the metadata file")
    parser.add_argument("--offline",
                        help="whether the role is online or offline",
                        action="store_true")
    args = parser.parse_args()
    args = vars(args)
    print(args)

    if args["role"] == "timestamp" and args["offline"]:
        return

    if args["role"] == "snapshot" and args["offline"]:
        return

    if args["role"] == "targets" and args["offline"]:
        tg = roles.targets.TargetsOffline(args["rolecfg"], args["imagecfg"])
        tg.gen_signed_metadata_file("test_metadata.toml")


if __name__ == "__main__":
    main()
