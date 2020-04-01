
Dependencies:

    sudo apt install poppler-utils
    pipenv shell
    pip install requests python-magic

Fetch and transform metadata:

    mkdir -p metadata fulltext_web
    wget https://archive.org/download/s2-cord19-dataset/cord19.2020-03-27.csv
    mv cord19.2020-03-27.csv metadata
    ./scripts/parse_cord19_csv.py metadata/cord19.2020-03-27.csv > metadata/cord19.2020-03-27.json
    cat metadata/cord19.2020-03-27.json | parallel -j10 --linebuffer --round-robin --pipe ./scripts/cord19_fatcat_enrich.py - | pv -l > metadata/cord19.2020-03-27.enrich.json
    cat metadata/cord19.2020-03-27.enrich.json | jq 'select(.release_id == null) | .cord19_paper' -c > metadata/cord19.2020-03-27.missing.json

Existing fatcat ES transform:

    # in fatcat python directory, pipenv shell
    cat /srv/covid19.fatcat.wiki/src/metadata/cord19.2020-03-27.enrich.json | jq .fatcat_release -c | rg -v '^null$' | ./fatcat_transform.py elasticsearch-releases - - | pv -l > /srv/covid19.fatcat.wiki/src/metadata/cord19.2020-03-27.fatcat_es.json

Download fulltext from wayback:

    cat metadata/cord19.2020-03-27.enrich.json | jq .fatcat_release -c | parallel -j20 --linebuffer --round-robin --pipe ./scripts/deliver_file2disk.py --disk-dir fulltext_web - | pv -l > fatcat_web_20200327.log

Extract text from PDFs:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/pdftotext/{}
    fd -I .pdf fulltext_web/pdf/ | cut -c18-60 | parallel -j10 pdftotext fulltext_web/pdf/{}.pdf fulltext_web/pdftotext/{}.txt

Create thumbnails:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/thumbnail/{}
    fd -I .pdf fulltext_web/pdf/ | cut -c18-60 | parallel -j10 pdftocairo -png -singlefile -scale-to-x 400 -scale-to-y -1 fulltext_web/pdf/{}.pdf fulltext_web/thumbnail/{}

Fetch GROBID:

Convert GROBID XML to JSON:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/grobid/{}
    fd -I .xml fulltext_web/grobid/ | cut -c18-60 | parallel -j10 "bin/grobid2json.py fulltext_web/grobid/{}.xml > fulltext_web/grobid/{}.json"

Create large derivatives file (including extracted fulltext):

    ./cord19_fatcat_derivatives.py metadata/cord19.2020-03-27.enrich.json --base-dir fulltext_web/ | pv -l > fulltext.json

    cat fulltext.json | jq .fulltext_status -r | sort | uniq -c | sort -nr


## ES Indices

Create and index existing `fatcat_release` schema:

    http put :9200/covid19_fatcat_release < schema/release_schema_v03b.json

    # in fatcat python directory, pipenv shell
    export LC_ALL=C.UTF-8
    cat /srv/covid19.fatcat.wiki/src/metadata/cord19.2020-03-27.enrich.json | jq .fatcat_release -c | rg -v '^null$' | pv -l | ./fatcat_transform.py elasticsearch-releases - - | esbulk -verbose -size 1000 -id ident -w 8 -index covid19_fatcat_release -type release

Create fulltext index:

    http put :9200/covid19_fatcat_fulltext < schema/fulltext_schema_v00.json

Transform to ES schema and index:

    ./elastic_transform.py cord19.2020-03-27.fulltext.json | pv -l | esbulk -verbose -size 1000 -id fatcat_ident -w 8 -index covid19_fatcat_fulltext -type release

## GROBID Processing

    zip -r fulltext_web.zip fulltext_web

    # on GROBID worker, in sandcrawler repo and pipenv
    ./grobid_tool.py --grobid-host http://localhost:8070 -j 24 extract-zipfile /srv/sandcrawler/tasks/fulltext_web.zip | pv -l > /srv/sandcrawler/tasks/fulltext_web.grobid.json

