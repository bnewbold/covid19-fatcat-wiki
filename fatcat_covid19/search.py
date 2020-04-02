
import datetime
import requests
from flask import abort, flash
from fatcat_covid19.webface import app

def do_search(index, request, limit=30, offset=0, deep_page_limit=2000):

    # Sanity checks
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0
    if offset > deep_page_limit:
        # Avoid deep paging problem.
        offset = deep_page_limit

    request["size"] = int(limit)
    request["from"] = int(offset)
    # print(request)
    resp = requests.get("%s/%s/_search" %
            (app.config['ELASTICSEARCH_BACKEND'], index),
        json=request)

    if resp.status_code == 400:
        print("elasticsearch 400: " + str(resp.content))
        #flash("Search query failed to parse; you might need to use quotes.<p><code>{}</code>".format(resp.content))
        abort(resp.status_code)
    elif resp.status_code != 200:
        print("elasticsearch non-200 status code: " + str(resp.status_code))
        print(resp.content)
        abort(resp.status_code)

    content = resp.json()
    results = [h['_source'] for h in content['hits']['hits']]
    for h in results:
        # Handle surrogate strings that elasticsearch returns sometimes,
        # probably due to mangled data processing in some pipeline.
        # "Crimes against Unicode"; production workaround
        for key in h:
            if type(h[key]) is str:
                h[key] = h[key].encode('utf8', 'ignore').decode('utf8')

    return {"count_returned": len(results),
            "count_found": content['hits']['total'],
            "results": results,
            "offset": offset,
            "deep_page_limit": deep_page_limit}

def do_fulltext_search(q, limit=30, offset=0):

    #print("Search hit: " + q)
    if limit > 100:
        # Sanity check
        limit = 100

    # Convert raw DOIs to DOI queries
    if len(q.split()) == 1 and q.startswith("10.") and q.count("/") >= 1:
        q = 'doi:"{}"'.format(q)


    search_request = {
        "query": {
            "query_string": {
                "query": q,
                "default_operator": "AND",
                "analyze_wildcard": True,
                "lenient": True,
                "fields": ["everything"],
            },
        },
    }

    resp = do_search(app.config['ELASTICSEARCH_FULLTEXT_INDEX'], search_request, offset=offset)
    for h in resp['results']:
        # Ensure 'contrib_names' is a list, not a single string
        if type(h['contrib_names']) is not list:
            h['contrib_names'] = [h['contrib_names'], ]
        h['contrib_names'] = [name.encode('utf8', 'ignore').decode('utf8') for name in h['contrib_names']]
    resp["query"] = { "q": q }
    resp["limit"] = limit
    return resp
