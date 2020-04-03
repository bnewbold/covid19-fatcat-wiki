#!/usr/bin/env python3

"""
Wrapper CLI tool for invoking code in the `fatcat_covid19` module.

Licensed the same as code under fatcat_covid19/
"""

import sys
import argparse

from fatcat_covid19.webface import app
from fatcat_covid19.derivatives import enrich_derivatives_file
from fatcat_covid19.transform import transform_es_file


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
        help="enrich CORD-19 dataset (JSON) with fatcat metadata")
    sub_enrich.set_defaults(
        action='enrich',
    )
    sub_enrich.add_argument('json_file',
        help="CORD-19 parsed JSON file",
        type=argparse.FileType('r'))

    sub_derivatives = subparsers.add_parser('derivatives',
        help="enrich JSON rows with existing derivative files")
    sub_derivatives.add_argument('json_file',
        help="enriched (with fatcat_release) metadata file",
        type=argparse.FileType('r'))
    sub_derivatives.add_argument('--json-output',
        help="file to write ",
        type=argparse.FileType('r'),
        default=sys.stdout)
    sub_derivatives.add_argument('--base-dir',
        help="directory to look for files (in 'pdf' subdirectory)",
        default="fulltext_web")

    sub_transform_es = subparsers.add_parser('transform-es',
        help="transform fulltext JSON to elasticsearch schema JSON")
    sub_transform_es.add_argument('json_file',
        help="input JSON rows file (fulltext)",
        type=argparse.FileType('r'))
    sub_transform_es.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('r'),
        default=sys.stdout)

    sub_enrich_fatcat = subparsers.add_parser('enrich-fatcat',
        help="lookup fatcat releases from JSON metadata")
    sub_enrich_fatcat.add_argument('json_file',
        help="input JSON rows file (eg, CORD-19 parsed JSON)",
        type=argparse.FileType('r'))
    sub_enrich_fatcat.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('r'),
        default=sys.stdout)

    args = parser.parse_args()

    if args.action == 'webface':
        app.run(debug=args.debug, host=args.host, port=args.port)
    elif args.action == 'derivatives':
        enrich_derivatives_file(args.json_file, args.json_output,
            args.base_dir)
    elif args.action == 'transform-es':
        transform_es_file(args.json_file, args.json_output)
    elif args.action == 'enrich-fatcat':
        transform_es_file(args.json_file, args.json_output)
    else:
        print("tell me what to do!")
        sys.exit(-1)


if __name__ == '__main__':
    main()
