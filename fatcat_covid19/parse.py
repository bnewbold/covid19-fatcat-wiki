
import sys
import csv
import json


def parse_cord19_file(csv_path, json_output):
    """
    Trivial helper to transform the CORD-19 CSV file to JSON, and rename a
    couple of the column keys.
    """

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row = dict(row)
            row['mag_id'] = row.pop('Microsoft Academic Paper ID')
            row['who_covidence_id'] = row.pop('WHO #Covidence').replace('#', '')
            obj = dict(cord19_paper=row)
            print(json.dumps(obj, sort_keys=True), file=json_output)

