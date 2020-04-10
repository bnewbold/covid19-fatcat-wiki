#!/usr/bin/env python3

"""
Wrapper CLI tool for invoking code in the `fatcat_covid19` module.

Licensed the same as code under fatcat_covid19/
"""

import sys
import argparse

from fatcat_covid19.parse import parse_cord19_file
from fatcat_covid19.query import query_fatcat
from fatcat_covid19.enrich import enrich_fatcat_file
from fatcat_covid19.dedupe import dedupe_file
from fatcat_covid19.derivatives import enrich_derivatives_file
from fatcat_covid19.transform import transform_es_file


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.set_defaults(
        action='none',
    )
    subparsers = parser.add_subparsers()

    sub_parse_cord = subparsers.add_parser('parse-cord19',
        help="parse a CORD-19 CSV file into JSON")
    sub_parse_cord.set_defaults(
        action='parse-cord19',
    )
    sub_parse_cord.add_argument('csv_path',
        help="input CSV file path",
        type=str)
    sub_parse_cord.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('w'),
        default=sys.stdout)

    sub_query_fatcat = subparsers.add_parser('query-fatcat',
        help="query fatcat search index for releases")
    sub_query_fatcat.set_defaults(
        action='query-fatcat',
    )
    sub_query_fatcat.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('w'),
        default=sys.stdout)

    sub_dedupe = subparsers.add_parser('dedupe',
        help="emit only one JSON line per fatcat release_id")
    sub_dedupe.set_defaults(
        action='dedupe',
    )
    sub_dedupe.add_argument('--json-input',
        help="input JSON rows file (eg, CORD-19 parsed JSON)",
        type=argparse.FileType('r'),
        default=sys.stdin)
    sub_dedupe.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('w'),
        default=sys.stdout)

    sub_enrich_fatcat = subparsers.add_parser('enrich-fatcat',
        help="lookup fatcat releases from JSON metadata")
    sub_enrich_fatcat.set_defaults(
        action='enrich-fatcat',
    )
    sub_enrich_fatcat.add_argument('json_file',
        help="input JSON rows file (eg, CORD-19 parsed JSON)",
        type=argparse.FileType('r'))
    sub_enrich_fatcat.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('w'),
        default=sys.stdout)

    sub_enrich_derivatives = subparsers.add_parser('enrich-derivatives',
        help="enrich JSON rows with existing derivative files")
    sub_enrich_derivatives.set_defaults(
        action='enrich-derivatives',
    )
    sub_enrich_derivatives.add_argument('json_file',
        help="enriched (with fatcat_release) metadata file",
        type=argparse.FileType('r'))
    sub_enrich_derivatives.add_argument('--json-output',
        help="file to write ",
        type=argparse.FileType('w'),
        default=sys.stdout)
    sub_enrich_derivatives.add_argument('--base-dir',
        help="directory to look for files (in 'pdf' subdirectory)",
        default="fulltext_web")

    sub_transform_es = subparsers.add_parser('transform-es',
        help="transform fulltext JSON to elasticsearch schema JSON")
    sub_transform_es.set_defaults(
        action='transform-es',
    )
    sub_transform_es.add_argument('json_file',
        help="input JSON rows file (fulltext)",
        type=argparse.FileType('r'))
    sub_transform_es.add_argument('--json-output',
        help="file to write to",
        type=argparse.FileType('w'),
        default=sys.stdout)

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

    args = parser.parse_args()

    if args.action == 'parse-cord19':
        parse_cord19_file(args.csv_path, args.json_output)
    elif args.action == 'query-fatcat':
        query_fatcat(args.json_output)
    elif args.action == 'dedupe':
        dedupe_file(args.json_input, args.json_output)
    elif args.action == 'enrich-fatcat':
        enrich_fatcat_file(args.json_file, args.json_output)
    elif args.action == 'enrich-derivatives':
        enrich_derivatives_file(args.json_file, args.json_output,
            args.base_dir)
    elif args.action == 'transform-es':
        transform_es_file(args.json_file, args.json_output)
    elif args.action == 'webface':
        # don't import until we use app; otherwise sentry exception reporting happens
        from fatcat_covid19.webface import app
        app.run(debug=args.debug, host=args.host, port=args.port)
    else:
        print("tell me what to do!")
        sys.exit(-1)


if __name__ == '__main__':
    main()
