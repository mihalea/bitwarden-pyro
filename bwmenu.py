#!/usr/bin/env python

from logger import BwLogger
from arguments import parse_arguments
from settings import NAME, VERSION
from session import Session, SessionException
from rofi import Rofi
from completion import Completion, CompletionException


def main():
    args = parse_arguments()
    logger = BwLogger(args.verbose).get_logger()

    if args.version:
        print(f"{NAME} v{VERSION}")
        exit()

    logger.info("Application has been launched")
    try:
        session = Session(args.timeout)
        rofi = Rofi()
        completion = Completion()
    except (CompletionException, SessionException):
        logger.exception(f"Failed to initialise application")
        exit(1)

    pwd = None
    if not session.has_key():
        pwd = rofi.get_password()
        if pwd is not None:
            session.unlock(pwd)
        else:
            logger.info("Unlocking aborted")
            exit(0)

    # k = session.get_key()


if __name__ == "__main__":
    main()
