# parse command-line arguments
import argparse

def main():
    print("autosec_uptane version 0.0.1")
    parser = argparse.ArgumentParser(prog="uptane", description="a cmd program for creating metadata for uptane framework")
    parser.add_argument("file", help="the config file for the role?")
    args = parser.parse_args()

if __name__ == "__main__":
    main()
    
