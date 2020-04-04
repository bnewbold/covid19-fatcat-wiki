
[covid19.fatcat.wiki](https://covid19.fatcat.wiki)
======================================================

**Not Medical Advice for General Public or Clinical Use!**

This repository contains a web search front-end and data munging pipeline for a
corpus of research publications and datasets relating to the COVID-19 pandemic.

The main dataset is the
["CORD-19"](https://pages.semanticscholar.org/coronavirus-research) (sic) paper
set from Semantic Scholar, enriched with additional metadata and web archive
fulltext from [fatcat.wiki](https://fatcat.wiki).

Visit the live site ["about"](https://covid19.fatcat.wiki/about) and
["sources"](https://covid19.fatcat.wiki/sources) pages for more context about
this project. In particular, note several **DISCLAIMERS** about quality,
content, and service reliability, and licensing context about paper content and
bibliographic metadata.


## Technical Overview

A crude python data perparation pipeline runs through the following stages:

- ``parse``: source metadata into JSON rows, one per paper
- ``enrich-fatcat``: queries fatcat API for full metadata and links to fulltext PDFs
- commands and shell scripts under `bin/` are run to download PDF copies and
  make "derivative" files (like thumbnails, extracting text)
- ``derivatives``: add derivative file paths and and full text to JSON rows
- ``transform-es``: convert from full JSON fulltext rows to elasticsearch schema
- load into elasticsearch cluster using `esbulk` tool

Currently, only documents with a fatcat release ident are indexed into
elasticsearch, and use that ident as the document key. This means that the
index can be reloaded to update documents without creating duplicate entries.

A stateless web interface (implemented in Python with Flask) provides a search
front-end to the elasticsearch index. The web interface uses the Babel library
to provide language localization, but additional work will be needed to make
the interface actually usable across languages.


## Elasticsearch API Access

The fulltext search index is currently world-readable in the native
elasticsearch 6.8 API at:

    https://search.fatcat.wiki/covid19_fatcat_fulltext

An index of native fatcat release schema for just the papers in this corpus is
also available at:

    https://search.fatcat.wiki/covid19_fatcat_release

Accessing both of these indices from your own software, or from browsers
directly via cross-site requests, should mostly work fine.

## Development Environment

This software is developed and deployed on GNU/Linux (Debian family) and hasn't
been tested elsewhere. Software dependencies include:

- python 3.7 (locked to this minor version)
- [pipenv](https://github.com/pypa/pipenv)
- `poppler-utils`
- elasticsearch 6.x (7.x may or may not work fine)
- [esbulk](https://github.com/sharkdp/fd)
- [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`)
- [`fd`](https://github.com/sharkdp/fd)
- `pv`
- `parallel`

To run the web interface in local/debug mode, with search queries sent to
public search index by default:

    cp example.env .env
    pipenv install --dev --deploy
    pipenv shell
    ./covid19_tool.py webface --debug

    # output will include a localhost URL to open


## Translations

Update the .pot file and translation files:

    pybabel extract -F extra/i18n/babel.cfg -o extra/i18n/web_interface.pot fatcat_covid19/
    pybabel update -i extra/i18n/web_interface.pot -d fatcat_covid19/translations

Compile translated messages together:

    pybabel compile -d fatcat_covid19/translations

Create initial .po file for a new language translation (then run the above
update/compile after doing initial translations):

    pybabel init -i extra/i18n/web_interface.pot -d fatcat_covid19/translations -l de


## Acknowledgements

For content and bibliographic metadata (partial list):

- Allen Institute's CORD-19 dataset
- PubMed catalog and PMC repository
- World Health Organization
- Wanfang Data
- CNKI
- biorxiv and medrxiv pre-print repositories
- publishers large and small, from around the world, making this research
  accessible (in some cases temporarily)
- research authors
- hospital workers and other emergency responders around the world

## Contact, Contributions, Licensing

General inquires should go to
[webservices@archive.org](mailto:webservices@archive.org). Take-down requests
and legal inqueries to [info@archive.org](mailto:info@archive.org). Bryan's
contact information is available [on his website](https://bnewbold.net/about/).

Contributions are welcome! Development is currently on Github and technical
issues (bugs, feature requests) can be filed there:
<https://github.com/bnewbold/covid19-fatcat-wiki>

The software in this repository is licensed under a combination of MIT and
AGPLv3 licenses. See `LICENSE.md` and `CONTRIBUTORS.md` for details.
