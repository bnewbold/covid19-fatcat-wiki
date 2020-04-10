
## Python Client

Install (using a virtualenv, conda, whatever):

    pip install jupyter matplotlib elasticsearch-dsl



## Browser Javascript

In short, *direct, rich, browser search queries will not work* because browser
HTTP GET requests do not allow bodies, and this is the mechanism Elasticsearch
uses to send complex queries. The search.fatcat.wiki endpoint currently blocks
all POST requests for security reasons.

This includes things like the elasticsearch-js/elasticsearch-browser client,
and use from "notebooks" like observablehq.com, jsfiddle, etc.

A subset of queries may work using only GET with URL parameters, for example
X-Pack SQL queries.

The resolution for this would be to implement proper read-only filtering of ES
requests, either with middleware or upgrading ES and configuring access
policies properly.

Note: would import with something like:

    elasticsearch = require('https://bundle.run/elasticsearch-browser@16.7.1');
