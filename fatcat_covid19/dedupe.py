
import sys
import json
import datetime


def dedupe_file(json_input, json_output):
    """
    Takes JSON file of "fatcat enriched" content, and de-dupes based on the
    fatcat identifier.
    """
    rows = dict()
    for l in json_input:
        l = json.loads(l)
        key = l.get('release_id')
        if not key:
            continue
        if not key in rows:
            rows[key] = l
            continue
        for other_info in ['cord19_paper', 'fatcat_hit',]:
            if other_info in l:
                rows[key][other_info] = l[other_info]

    for k in rows:
        print(json.dumps(rows[k], sort_keys=True), file=json_output)

