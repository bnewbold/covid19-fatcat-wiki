
import os
import sys
import json
import datetime

import elasticsearch
from elasticsearch_dsl import Search, Q

from fatcat_covid19.common import requests_retry_session


def query_fatcat(json_output):
    """
    Queries fatcat search index (the full regular fatcat.wiki release index)
    for COVID-19 keywords and phrases, iterates over the result set (using
    scroll), and fetches full release entity (via api.fatcat.wik) for each.
    """
    api_session = requests_retry_session()

    es_backend = os.environ.get(
        "ELASTICSEARCH_BACKEND",
        default="https://search.fatcat.wiki",
    )
    es_index = "fatcat_release"
    es_client = elasticsearch.Elasticsearch(es_backend)

    search = Search(using=es_client, index=es_index)

    search = search.exclude("terms", release_type=["stub", "component", "abstract"])

    # "Emerald Expert Briefings"
    search = search.exclude("terms", container_id=["fnllqvywjbec5eumrbavqipfym"])

    # ResearchGate
    search = search.exclude("terms", doi_prefix=["10.13140"])

    # some industrial thing
    search = search.exclude("query_string", query='"Report on SARS backfit evaluation"', fields=["title"])

    # physic experiment
    search = search.exclude("query_string", query='"TOF-SARS"', fields=["title"])

    # species not related to SARS
    # something based on excluding "lake" in title might be easier?
    search = search.exclude("query_string", query='"G.O. Sars"', fields=["title"])
    search = search.exclude("query_string", query='"Gomphocythere Sars"', fields=["title"])
    search = search.exclude("query_string", query='"Australis Sars"', fields=["title"])
    search = search.exclude("query_string", query='"scutifer Sars"', fields=["title"])
    search = search.exclude("query_string", query='"lumholtzi Sars"', fields=["title"])

    search = search.query(
        Q("query_string", query='"COVID-19" coronavirus coronaviruses "sars-cov-2" "2019-nCoV" "SARS-CoV" "MERS-CoV" SARS', default_operator="OR", fields=["title", "original_title"]) |
        Q("query_string", query='pandemic influenza', default_operator="AND", fields=["biblio"]) |
        Q("query_string", query='epidemic influenza', default_operator="AND", fields=["biblio"]) |
        Q("query_string", query='pandemic ventilator', default_operator="AND", fields=["biblio"])
    )

    print("Expecting {} search hits".format(search.count()), file=sys.stderr)

    search = search.params(clear_scroll=False)
    search = search.params(_source=False)

    results = search.scan()
    for hit in results:
        release_id = hit.meta.id
        resp = api_session.get(
            'https://api.fatcat.wiki/v0/release/{}'.format(release_id),
            params={
                'expand': 'container,files,filesets,webcaptures',
                'hide': 'references',
        })
        resp.raise_for_status()
        row = dict(
            fatcat_hit=hit.meta._d_,
            release_id=release_id,
            fatcat_release=resp.json(),
        )
        print(json.dumps(row, sort_keys=True), file=json_output)

