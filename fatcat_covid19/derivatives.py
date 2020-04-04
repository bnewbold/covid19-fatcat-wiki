
import sys
import json
import argparse
import datetime

from fatcat_covid19.common import *


def enrich_derivatives_row(row, base_dir):
    """
    Takes *enriched* JSON objects which include a fatcat_release key/entity, and
    populate fulltext content and metadata.

    This script *only* looks for existing local files.

    Keys added:

    - fulltext_status: whether we could fetch or not (always added)
    - fulltext_file: fatcat file entity, plus
        - pdf_path
        - pdftotext_path (if exists)
        - thumbnail_path (if exists)
        - grobid_xml_path (if exists)
        - grobid_json_path (if exists)
    - fulltext_grobid: grobid2json format, including:
        - title
        - authors
        - journal
        - abstract
        - body
        - acknowledgement
        - annex
        - language_code
        - glutton_fatcat_release (renamed from fatcat_release)
    - fulltext_pdftotext: only if fulltext_grobid not set
        - body
    """

    if 'fulltext_file' in row:
        return row
    if not 'fatcat_release' in row:
        row['fulltext_status'] = 'no-release'
        return row
    if not row['fatcat_release'].get('files'):
        row['fulltext_status'] = 'no-file'
        return row
    fulltext_file = find_local_file(row['fatcat_release']['files'], base_dir=base_dir)
    if not fulltext_file:
        row['fulltext_status'] = 'no-local-file'
        return row
    else:
        row['fulltext_status'] = 'found'

    # ok, we have file, now populate derivatives etc
    fulltext_file['pdf_path'] = blob_path(
        fulltext_file['sha1'],
        directory="pdf/",
        file_suffix=".pdf",
        base_dir=base_dir,
    )
    fulltext_file['pdftotext_path'] = blob_path(
        fulltext_file['sha1'],
        directory="pdftotext/",
        file_suffix=".txt",
        base_dir=base_dir,
    )
    fulltext_file['thumbnail_path'] = blob_path(
        fulltext_file['sha1'],
        directory="thumbnail/",
        file_suffix=".png",
        base_dir=base_dir,
    )
    fulltext_file['grobid_xml_path'] = blob_path(
        fulltext_file['sha1'],
        directory="grobid/",
        file_suffix=".xml",
        base_dir=base_dir,
    )
    fulltext_file['grobid_json_path'] = blob_path(
        fulltext_file['sha1'],
        directory="grobid/",
        file_suffix=".json",
        base_dir=base_dir,
    )

    # check if derivatives actually exist
    for key in ('pdftotext_path', 'thumbnail_path', 'grobid_xml_path',
                'grobid_json_path'):
        if not os.path.isfile(fulltext_file[key]):
            fulltext_file[key] = None

    row['fulltext_file'] = fulltext_file

    # if there is no GROBID, try pdftotext
    if not fulltext_file['grobid_json_path']:

        if fulltext_file['pdftotext_path']:
            try:
                with open(fulltext_file['pdftotext_path'], 'r') as f:
                    row['fulltext_pdftotext'] = dict(body=f.read())
            except UnicodeDecodeError:
                row['fulltext_status'] = 'bad-unicode-pdftotext'
                return row
            row['fulltext_status'] = 'success-pdftotext'
            return row
        else:
            row['fulltext_status'] = 'no-extraction'
            return row

    with open(fulltext_file['grobid_json_path'], 'r') as f:
        grobid = json.loads(f.read())

    gfr = grobid.pop('fatcat_release', None)
    if gfr:
        grobid['glutton_fatcat_release'] = gfr
    row['fulltext_grobid'] = grobid
    row['fulltext_status'] = 'success-grobid'
    return row

def enrich_derivatives_file(json_input, json_output, base_dir):
    """
    Reads lines from json_input (an open, readable file or similar), looks for
    existing derivative files in base_dir (a path str), and writes string JSON
    lines to json_output (an open, writable file or similar).
    """
    for l in json_input:
        l = json.loads(l)
        result = enrich_derivatives_row(l, base_dir)
        if result:
            print(json.dumps(result, sort_keys=True), file=json_output)

