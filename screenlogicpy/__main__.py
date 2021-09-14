import sys
from screenlogicpy.cli import cli


def main():
    cli(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
