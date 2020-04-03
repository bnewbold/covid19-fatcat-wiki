#!/usr/bin/env python3

"""
Wrapper CLI tool for invoking code in the `fatcat_covid19` module.

Licensed the same as code under fatcat_covid19/
"""

import sys
import argparse

from fatcat_covid19.webface import app


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.set_defaults(
        action='none',
    )
    subparsers = parser.add_subparsers()

    sub_webface = subparsers.add_parser('webface',
        help="run flask web interface")
    sub_webface.set_defaults(
        action='webface',
    )
    sub_webface.add_argument('--debug',
        action='store_true',
        help="enable debugging interface (note: not for everything)")
    sub_webface.add_argument('--host',
        default="127.0.0.1",
        help="listen on this host/IP")
    sub_webface.add_argument('--port',
        type=int,
        default=9119,
        help="listen on this port")

    sub_enrich = subparsers.add_parser('enrich',
        help="enrich CORD-19 dataset (JSON) with fatcat metadata (prints to stdout)")
    sub_enrich.set_defaults(
        action='enrich',
    )
    sub_enrich.add_argument('json_file',
        help="CORD-19 parsed JSON file",
        type=argparse.FileType('r'))

    args = parser.parse_args()

    if args.action == 'webface':
        app.run(debug=args.debug, host=args.host, port=args.port)
    if args.action == 'enrich':
        # TODO
        pass
    else:
        print("tell me what to do!")
        sys.exit(-1)


if __name__ == '__main__':
    main()
