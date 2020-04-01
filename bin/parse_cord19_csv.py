#!/usr/bin/env python3

import sys
import csv
import json

CSVFILE = sys.argv[1]

with open(CSVFILE, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        row = dict(row)
        row['mag_id'] = row.pop('Microsoft Academic Paper ID')
        row['who_covidence_id'] = row.pop('WHO #Covidence').replace('#', '')
        print(json.dumps(row, sort_keys=True))
