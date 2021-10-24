import asyncio
import sys
from screenlogicpy.cli import cli


def main():
    args = sys.argv[1:]
    # Save for debugger
    # args = ["-i", "xx.xx.xx.xx", "get", "json"]
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(cli(args))


if __name__ == "__main__":
    sys.exit(main())
