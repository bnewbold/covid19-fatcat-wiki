#!/usr/bin/env python3

"""
Takes a JSON-transformed CORD-19 *metadata* file and enriches it with fatcat
metadata.

TODO: refactor into `fatcat_covid19` module and wrapper CLI script.
"""

import sys
import json
import argparse
import datetime

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # pylint: disable=import-error


def requests_retry_session(retries=10, backoff_factor=3,
        status_forcelist=(500, 502, 504), session=None):
    """
    From: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def do_line(row, args):

    pubmed_id = row.get('pubmed_id') or None
    pmcid = row.get('pmcid') or None
    doi = row.get('doi') or None
    fatcat_release = None

    if doi == '0.1126/science.abb7331':
        doi = '10.1126/science.abb7331'

    if not fatcat_release and pmcid:
        resp = args.session.get('https://api.fatcat.wiki/v0/release/lookup',
            params={
                'pmcid': pmcid,
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'abstracts,references',
        })
        if resp.status_code == 200:
            fatcat_release = resp.json()
    if not fatcat_release and doi:
        resp = args.session.get('https://api.fatcat.wiki/v0/release/lookup',
            params={
                'doi': doi,
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'abstracts,references',
        })
        if resp.status_code == 200:
            fatcat_release = resp.json()
    if not fatcat_release and pubmed_id:
        resp = args.session.get('https://api.fatcat.wiki/v0/release/lookup',
            params={
                'pmid': pubmed_id,
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'abstracts,references',
        })
        if resp.status_code == 200:
            fatcat_release = resp.json()

    obj = dict(
        cord19_paper=row,
    )
    if fatcat_release:
        obj['fatcat_release'] = fatcat_release
        obj['release_id'] = fatcat_release['ident']
        obj['fatcat_url'] = "https://fatcat.wiki/release/{}".format(obj['release_id'])
    print(json.dumps(obj, sort_keys=True))

def run(args):
    for l in args.json_file:
        l = json.loads(l)
        do_line(l, args)

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('json_file',
        help="CORD-19 parsed JSON file",
        type=argparse.FileType('r'))
    subparsers = parser.add_subparsers()

    args = parser.parse_args()
    args.session = requests_retry_session()

    run(args)

if __name__ == '__main__':
    main()

