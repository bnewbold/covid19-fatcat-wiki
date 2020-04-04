
import sys
import json
import datetime

from fatcat_covid19.common import requests_retry_session


def enrich_fatcat_row(row, api_session):

    cord19_paper = row.get('cord19_paper')
    if not cord19_paper:
        return row

    pubmed_id = cord19_paper.get('pubmed_id') or None
    pmcid = cord19_paper.get('pmcid') or None
    doi = cord19_paper.get('doi') or None
    fatcat_release = None

    if doi == '0.1126/science.abb7331':
        doi = '10.1126/science.abb7331'

    if not fatcat_release and pmcid:
        resp = api_session.get('https://api.fatcat.wiki/v0/release/lookup',
            params={
                'pmcid': pmcid,
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'references',
        })
        if resp.status_code == 200:
            fatcat_release = resp.json()
    if not fatcat_release and doi:
        resp = api_session.get('https://api.fatcat.wiki/v0/release/lookup',
            params={
                'doi': doi,
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'references',
        })
        if resp.status_code == 200:
            fatcat_release = resp.json()
    if not fatcat_release and pubmed_id:
        resp = api_session.get('https://api.fatcat.wiki/v0/release/lookup',
            params={
                'pmid': pubmed_id,
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'references',
        })
        if resp.status_code == 200:
            fatcat_release = resp.json()

    if fatcat_release:
        row['fatcat_release'] = fatcat_release
        row['release_id'] = fatcat_release['ident']
    print(json.dumps(row, sort_keys=True))


def enrich_fatcat_file(json_input, json_output):
    """
    Takes a JSON-transformed CORD-19 *metadata* file and enriches it with
    fatcat metadata.
    """
    api_session = requests_retry_session()
    for l in json_input:
        l = json.loads(l)
        result = enrich_fatcat_row(l, api_session)
        if result:
            print(json.dumps(result, sort_keys=True), file=json_output)
