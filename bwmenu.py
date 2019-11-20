#!/usr/bin/env python

from arguments import parse_arguments
from settings import NAME, VERSION
from session import Session
from rofi import Rofi


def main():
    args = parse_arguments()

    if args.version:
        print(f"{NAME} v{VERSION}")
        exit

    session = Session(args.timeout)
    rofi = Rofi()

    pwd = None
    if not session.has_key():
        pwd = rofi.get_password()
        session.unlock(pwd)

    k = session.get_key()
    print(k)


if __name__ == "__main__":
    main()
