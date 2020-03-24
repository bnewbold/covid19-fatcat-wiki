
Research index and searchable discovery tool of papers and datasets related to
COVID-19.

Features:
- fulltext search over papers
- direct download PDFs
- find content by search queries + lists of identifiers

## Design

Web interface build on elasticsearch. Guessing on the order of 100k entities.

Batch back-end system aggregates papers of interest, fetches metadata from
fatcat, fetches fulltext+GROBID, indexes into elasticsearch. Run periodically
(eg, daily, hourly)

Some light quality tooling to find bad metadata; do cleanups in fatcat itself.


## Thoughts / Brainstorm

Tagging? Eg, by type of flu, why paper included

Clearly indicate publication status (pre-prints).

Auto-translation to multiple languages. Translation/i18n of user interface.

Dashboards/graphs of stats?

Faceted search.


## Also

Find historical papers of interest, eg the Spanish Flu, feature in blog posts.

Manually add interesting/valuable greylit like notable blog posts, WHO reports.
