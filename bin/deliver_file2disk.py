#!/usr/bin/env python3
"""
Tool for downloading fatcat release PDFs to disk (assuming there is at least
one accessible PDF file entity for each release).

Behavior:
- if no file, or not accessible, skip release
- filter files, then iterate through:
    - if already exists locally on disk, skip
    - try downloading from any archive.org or web.archive.org URLs
    - verify SHA-1
    - write out to disk

This file is copied from the fatcat repository.
"""

# XXX: some broken MRO thing going on in here due to python3 object wrangling
# in `wayback` library. Means we can't run pylint.
# pylint: skip-file

import os
import sys
import json
import magic
import hashlib
import argparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # pylint: disable=import-error
from collections import Counter


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


class DeliverFatcatDisk:

    def __init__(self, disk_dir, **kwargs):
        self.count = Counter()
        self.disk_dir = disk_dir
        self.disk_prefix = kwargs.get('disk_prefix', 'pdf/')
        self.disk_suffix = kwargs.get('disk_suffix', '.pdf')
        self.session = requests_retry_session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 fatcat.DeliverFatcatDisk',
        })

    def run(self, release_json_file):
        sys.stderr.write("Ensuring all 256 base directories exist...\n")
        for i in range(256):
            fpath = "{}/{}{:02x}".format(
                    self.disk_dir,
                    self.disk_prefix,
                    i)
            os.makedirs(fpath, exist_ok=True)
        sys.stderr.write("Starting...\n")
        for line in release_json_file:
            self.count['total'] += 1
            if not line.startswith('{'):
                self.count['skip-no-release'] += 1
                continue
            #print(line)
            release = json.loads(line)
            assert 'ident' in release
            self.fetch_release(release)
        sys.stderr.write("{}\n".format(self.count))

    def blob_path(self, sha1hex):
        fpath = "{}/{}{}/{}{}".format(
                self.disk_dir,
                self.disk_prefix,
                sha1hex[0:2],
                sha1hex,
                self.disk_suffix)
        return fpath

    def does_file_already_exist(self, sha1hex):
        return os.path.isfile(self.blob_path(sha1hex))

    def filter_files(self, files):
        """
        Takes a list of file entities and only returns the ones which are PDFs
        we can download.
        """
        good = []
        for f in files:
            if f['mimetype'] and not 'pdf' in f['mimetype'].lower():
                continue
            for url in f['urls']:
                if 'archive.org/' in url['url']:
                    good.append(f)
                    break
        return good

    def fetch_content(self, url):
        """
        Returns tuple: (str:status, content)
        Content contains bytes only if status is "success", otherwise None
        """
        if '://web.archive.org/' in url:
            # add id_ to URL to avoid wayback re-writing
            l = url.split('/')
            if l[2] == 'web.archive.org' and l[3] == 'web' and not '_' in l[4]:
                l[4] = l[4] + 'id_'
            url = '/'.join(l)

        try:
            resp = self.session.get(url)
        except requests.exceptions.RetryError:
            return ('wayback-error', None)
        except requests.exceptions.TooManyRedirects:
            return ('too-many-redirects', None)
        if resp.status_code != 200:
            return ('fetch:{}'.format(resp.status_code), None)
        else:
            return ('success', resp.content)

    def fetch_file(self, f):
        """
        Returns tuple: (status, sha1hex, file_meta)

        file_meta is a dict on success, or None otherwise
        """
        sha1hex = f['sha1']
        if self.does_file_already_exist(sha1hex):
            return ('exists', sha1hex, None)
        status = None
        for url in f['urls']:
            url = url['url']
            if not 'archive.org' in url:
                continue
            status, content = self.fetch_content(url)
            if status == 'success':
                # TODO: verify sha1hex
                file_meta = gen_file_metadata(content)
                if file_meta['sha1hex'] != sha1hex:
                    status = 'sha1-mismatch'
                    continue
                with open(self.blob_path(sha1hex), 'wb') as outf:
                    outf.write(content)
                return ('success', sha1hex, file_meta)
        if status:
            return (status, sha1hex, None)
        else:
            return ('no-urls', sha1hex, None)

    def fetch_release(self, release):
        good_files = self.filter_files(release['files'])
        status = 'no-file'
        sha1hex = None
        for f in good_files:
            status, sha1hex, file_meta = self.fetch_file(f)
            if status in ('success', 'exists'):
                break
            else:
                continue
        if sha1hex:
            print("{}\t{}".format(status, sha1hex))
        else:
            print(status)
        self.count[status] += 1

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--disk-dir',
                        required=True,
                        type=str,
                        help='local base directory to save into')
    parser.add_argument('--disk-prefix',
                        type=str,
                        default="pdf/",
                        help='directory prefix for items created in bucket')
    parser.add_argument('--disk-suffix',
                        type=str,
                        default=".pdf",
                        help='file suffix for created files')
    parser.add_argument('release_json_file',
                        help="JSON manifest of fatcat release entities",
                        default=sys.stdin,
                        type=argparse.FileType('r'))
    args = parser.parse_args()

    worker = DeliverFatcatDisk(**args.__dict__)
    worker.run(args.release_json_file)

if __name__ == '__main__': # pragma: no cover
    main()
