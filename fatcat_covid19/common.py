
"""
Helper routines.

Many of these copied verbatim from fatcat or sandcrawler repositories.
"""

import os
import sys
import copy
import json
import magic
import hashlib

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # pylint: disable=import-error


def gen_file_metadata(blob):
    """
    Takes a file blob (bytestream) and returns hashes and other metadata.

    Returns a dict: size_bytes, md5hex, sha1hex, sha256hex, mimetype
    """
    assert blob
    mimetype = magic.Magic(mime=True).from_buffer(blob)
    hashes = [
        hashlib.sha1(),
        hashlib.sha256(),
        hashlib.md5(),
    ]
    for h in hashes:
        h.update(blob)
    return dict(
        size_bytes=len(blob),
        sha1hex=hashes[0].hexdigest(),
        sha256hex=hashes[1].hexdigest(),
        md5hex=hashes[2].hexdigest(),
        mimetype=mimetype,
    )

def requests_retry_session(retries=2, backoff_factor=3,
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

def blob_path(sha1hex, directory="", file_suffix="", base_dir="."):
    """
    directory: eg, "png/"
    sha1hex
    file_suffix: eg, ".png"
    """
    fpath = "{}/{}{}/{}{}".format(
            base_dir,
            directory,
            sha1hex[0:2],
            sha1hex,
            file_suffix)
    return fpath

def find_local_file(files, base_dir="."):
    """
    Takes a list of fatcat file entities (as dicts), and looks for a local file (PDF).

    If none found, returns None.
    If found, returns the file entity; the path can be determined from the sha1hex field.
    """
    for f in files:
        if f.get('mimetype') and not 'pdf' in f['mimetype'].lower():
            continue
        pdf_path = blob_path(f['sha1'], directory="pdf/", file_suffix=".pdf", base_dir=base_dir)
        if os.path.isfile(pdf_path):
            return copy.deepcopy(f)
    return None
