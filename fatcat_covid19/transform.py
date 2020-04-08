
import sys
import json
import argparse
import datetime

from fatcat_covid19.common import *


UNWANTED_ABSTRACT_PREFIXES = [
    # roughly sort this long to short
    'Abstract No Abstract ',
    'Publisher Summary ',
    'Abstract ',
    'ABSTRACT ',
    'Summary ',
    'Background: ',
    'Background ',
]

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

    abstracts = []
    abstract_langs = []

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
    ]
    EXT_IDS = [
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
    for key in EXT_IDS:
        t[key] = release['ext_ids'].get(key) or None

    t['contrib_count'] = len(release['contribs'] or [])

    if release.get('abstracts'):
        for a in release['abstracts']:

            # hack to (partially) clean up common JATS abstract display case
            if a.get('mimetype') == 'application/xml+jats':
                for tag in ('p', 'jats', 'jats:p', 'jats:title'):
                    a['content'] = a['content'].replace('<{}>'.format(tag), '')
                    a['content'] = a['content'].replace('</{}>'.format(tag), '')
                    # ugh, double encoding happens
                    a['content'] = a['content'].replace('&lt;/{}&gt;'.format(tag), '')
                    a['content'] = a['content'].replace('&lt;{}&gt;'.format(tag), '')

            # hack to remove abstract prefixes
            for prefix in UNWANTED_ABSTRACT_PREFIXES:
                if a['content'].startswith(prefix):
                    a['content'] = a['content'][len(prefix):]
                    break
            a['content'] = a['content'].strip()
            if a['content']:
                abstracts.append(a['content'].strip())
                if a.get('lang'):
                    abstract_langs.append(a['lang'])

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
        t['container_original_name'] = container.get('original_name')
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
        for url in full.get('urls', []):
            if url.get('rel') in ('webarchive', 'archive') and 'archive.org/' in url['url']:
                t['fulltext']['ia_pdf_url'] = url['url']
                break

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

    # then other metadata stuff
    if row.get('source_tags'):
        # will get set-uniq at the end
        t['source_tags'] = row['source_tags']
    else:
        t['source_tags'] = []

    if 'cord19_paper' in row:
        t['source_tags'].append('cord19')
        paper = row['cord19_paper']
        t['cord19_uid'] = paper['cord_uid']
        if paper.get('who_covidence_id'):
            t['who_covidence_id'] = paper['who_covidence_id']
            t['source_tags'].append('who')
        if paper.get('abstract') and not abstracts:
            abstracts.append(paper['abstract'])
        if not t['license']:
            t['license'] = paper.get('license') or None
    
    t['abstract'] = abstracts
    t['abstract_lang'] = list(set(abstract_langs))

    t['source_tags'] = list(set(t['source_tags']))

    return t

def transform_es_file(json_input, json_output):
    """
    Takes *enriched* JSON objects which include fatcat metadata and fulltext
    content, and outputs JSON lines in fatcat_fulltext schema.
    """
    for l in json_input:
        l = json.loads(l)
        result = fulltext_to_elasticsearch(l)
        if result:
            print(json.dumps(result, sort_keys=True), file=json_output)
