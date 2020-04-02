#!/usr/bin/env python3

"""
Takes *enriched* JSON objects which include fatcat metadata and fulltext
content, and outputs JSON lines in fatcat_fulltext schema.
"""

import sys
import json
import argparse
import datetime

from fatcat_covid19.common import *


def fulltext_to_elasticsearch(row, force_bool=True):
    """
    Converts from fulltext content and release model/schema to elasticsearch
    oriented schema.

    Returns: dict
    Raises exception on error (never returns None)
    """

    if not 'fatcat_release' in row:
        # skip papers that don't match to a fatcat release
        return None

    release = row['fatcat_release']

    # first, easy fatcat metadata
    t = {
        'fatcat_ident': release['ident'],
        'fatcat_revision': release['revision'],
        'fulltext': dict(),
    }
    BIBLIO_KEYS = [
        'work_id',
        'title',
        'subtitle',
        'original_title',
        'release_type',
        'release_stage',
        'release_year',
        'release_date',
        'withdrawn_status',
        'language',
        'volume',
        'issue',
        'pages',
        'number',
        'license',
        'doi',
        'pmid',
        'pmcid',
        'isbn13',
        'wikidata_qid',
        'arxiv_id',
        'jstor_id',
        'mag_id',
    ]
    for key in BIBLIO_KEYS:
        t[key] = release.get(key) or None

    abstracts = []
    abstract_langs = []

    # then the fulltext stuff
    t['fulltext']['status'] = row.get('fulltext_status', 'none')
    if 'fulltext_file' in row:
        full = row['fulltext_file']
        t['fulltext']['sha1'] = full['sha1']
        t['fulltext']['pdf_url'] = "/" + full['pdf_path']
        if full.get('pdftotext_path'):
            t['fulltext']['pdftotext_url'] = "/" + full['pdftotext_path']
        if full.get('thumbnail_path'):
            t['fulltext']['thumbnail_url'] = "/" + full['thumbnail_path']
        if full.get('grobid_xml_path'):
            t['fulltext']['grobid_xml_url'] = "/" + full['grobid_xml_path']

    if 'fulltext_grobid' in row:
        grobid = row['fulltext_grobid']
        if grobid.get('abstract'):
            abstracts.append(grobid['abstract'])
            abstract_langs.append(grobid['language_code'])
        t['fulltext']['abstract'] = grobid.get('abstract', None)
        t['fulltext']['body'] = grobid.get('body', None)
        t['fulltext']['acknowledgement'] = grobid.get('acknowledgement', None)
        t['fulltext']['annex'] = grobid.get('annex', None)
        t['fulltext']['lang'] = grobid.get('language_code', None)
    elif 'fulltext_pdftotext' in row:
        pdftotext = row['fulltext_pdftotext']
        t['fulltext']['body'] = pdftotext.get('body', None)

    if 'cord19_paper' in row:
        paper = row['cord19_paper']
        t['cord19_uid'] = paper['cord_uid']
        if paper.get('abstract'):
            abstracts.append(paper['abstract'])

    t['contrib_count'] = len(release['contribs'] or [])

    if release.get('abstracts'):
        for a in release['abstracts']:
            abstracts.append(a['content'])
            abstract_langs.append(a['lang'])
    
    t['abstract'] = abstracts
    t['abstract_lang'] = list(set(abstract_langs))

    contrib_names = []
    contrib_affiliations = []
    creator_ids = []
    for c in (release['contribs'] or []):
        if c.get('raw_name'):
            contrib_names.append(c['raw_name'])
        elif c.get('surname'):
            contrib_names.append(c['surname'])
        if c.get('creator_id'):
            creator_ids.append(c['creator_id'])
        if c.get('raw_affiliation'):
            contrib_affiliations.append(c['raw_affiliation'])
    t['contrib_names'] = contrib_names
    t['creator_ids'] = creator_ids
    t['affiliations'] = contrib_affiliations

    container = release.get('container')
    if container:
        t['publisher'] = container.get('publisher')
        t['container_name'] = container.get('name')
        # this is container.ident, not release.container_id, because there may
        # be a redirect involved
        t['container_id'] = container['ident']
        t['container_issnl'] = container.get('issnl')
        t['container_type'] = container.get('container_type')
        if container.get('extra'):
            c_extra = container['extra']
            if c_extra.get('country'):
                t['country_code'] = c_extra['country']
                t['country_code_upper'] = c_extra['country'].upper()

    # fall back to release-level container metadata if container not linked or
    # missing context
    if not t.get('publisher'):
        t['publisher'] = release.get('publisher')
    if not t.get('container_name') and release.get('extra'):
        t['container_name'] = release['extra'].get('container_name')

    extra = release['extra'] or dict()
    if extra:
        if not t.get('container_name'):
            t['container_name'] = extra.get('container_name')
        # backwards compatible subtitle fetching
        if not t['subtitle'] and extra.get('subtitle'):
            if type(extra['subtitle']) == list:
                t['subtitle'] = extra['subtitle'][0]
            else:
                t['subtitle'] = extra['subtitle']

    t['first_page'] = None
    if release.get('pages'):
        first = release['pages'].split('-')[0]
        first = first.replace('p', '')
        if first.isdigit():
            t['first_page'] = first
        # TODO: non-numerical first pages

    t['doi_registrar'] = None
    if extra and t['doi']:
        for k in ('crossref', 'datacite', 'jalc'):
            if k in extra:
                t['doi_registrar'] = k
        if not 'doi_registrar' in t:
            t['doi_registrar'] = 'crossref'

    if t['doi']:
        t['doi_prefix'] = t['doi'].split('/')[0]

    return t

def run(args):
    for l in args.json_file:
        l = json.loads(l)
        result = fulltext_to_elasticsearch(l, args)
        if result:
            print(json.dumps(result, sort_keys=True))

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('json_file',
        help="fulltext content input",
        type=argparse.FileType('r'))
    subparsers = parser.add_subparsers()

    args = parser.parse_args()
    args.session = requests_retry_session()

    run(args)

if __name__ == '__main__':
    main()

