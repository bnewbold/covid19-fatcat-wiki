
Dependencies:

    sudo apt install poppler-utils
    pip install requests python-magic

Context:

    export CORDDATE="2020-03-27"

Fetch and transform metadata:

    mkdir -p metadata fulltext_web
    wget https://archive.org/download/s2-cord19-dataset/cord19.$CORDDATE.csv -O metadata/cord19.$CORDDATE.csv metadata
    ./bin/parse_cord19_csv.py metadata/cord19.$CORDDATE.csv > metadata/cord19.$CORDDATE.json
    cat metadata/cord19.$CORDDATE.json | parallel -j10 --linebuffer --round-robin --pipe ./covid19_tool.py enrich-fatcat - | pv -l > metadata/cord19.$CORDDATE.enrich.json
    cat metadata/cord19.$CORDDATE.enrich.json | jq 'select(.release_id == null) | .cord19_paper' -c > metadata/cord19.$CORDDATE.missing.json

Existing fatcat ES transform:

    # in fatcat python directory, pipenv shell
    cat /srv/covid19.fatcat.wiki/src/metadata/cord19.$CORDDATE.enrich.json | jq .fatcat_release -c | rg -v '^null$' | ./fatcat_transform.py elasticsearch-releases - - | pv -l > /srv/covid19.fatcat.wiki/src/metadata/cord19.$CORDDATE.fatcat_es.json

Download fulltext from wayback:

    cat metadata/cord19.$CORDDATE.enrich.json | jq .fatcat_release -c | parallel -j20 --linebuffer --round-robin --pipe ./bin/deliver_file2disk.py --disk-dir fulltext_web - | pv -l > fatcat_web_20200327.log

Extract text from PDFs:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/pdftotext/{}
    fd -I .pdf fulltext_web/pdf/ | cut -c18-60 | parallel -j10 pdftotext fulltext_web/pdf/{}.pdf fulltext_web/pdftotext/{}.txt

Create thumbnails:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/thumbnail/{}
    fd -I .pdf fulltext_web/pdf/ | cut -c18-60 | parallel -j10 pdftocairo -png -singlefile -scale-to-x 400 -scale-to-y -1 fulltext_web/pdf/{}.pdf fulltext_web/thumbnail/{}

Fetch GROBID:

    # TODO

Convert GROBID XML to JSON:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/grobid/{}
    fd -I .xml fulltext_web/grobid/ | cut -c18-60 | parallel -j10 "bin/grobid2json.py fulltext_web/grobid/{}.xml > fulltext_web/grobid/{}.json"

Create large derivatives file (including extracted fulltext):

    ./covid19_tool.py enrich-derivatives metadata/cord19.$CORDDATE.enrich.json --base-dir fulltext_web/ | pv -l > metadata/cord19.$CORDDATE.fulltext.json

    cat metadata/cord19.$CORDDATE.fulltext.json | jq .fulltext_status -r | sort | uniq -c | sort -nr


## ES Indices

Create fulltext index, transform to ES schema and index:

    # if existing, first: http delete :9200/covid19_fatcat_fulltext
    http put :9200/covid19_fatcat_fulltext < schema/fulltext_schema.v00.json

    # in fatcat_covid19, pipenv shell
    ./covid19_tool.py transform-es metadata/cord19.$CORDDATE.fulltext.json | pv -l | esbulk -verbose -size 1000 -id fatcat_ident -w 8 -index covid19_fatcat_fulltext -type release

Create and index existing `fatcat_release` schema:

    http put :9200/covid19_fatcat_release < schema/release_schema_v03b.json

    # in fatcat python directory, pipenv shell
    export LC_ALL=C.UTF-8
    cat /srv/fatcat_covid19/src/metadata/cord19.$CORDDATE.enrich.json | jq .fatcat_release -c | rg -v '^null$' | pv -l | ./fatcat_transform.py elasticsearch-releases - - | esbulk -verbose -size 1000 -id ident -w 8 -index covid19_fatcat_release -type release

## GROBID Processing

    zip -r fulltext_web.zip fulltext_web

    # on GROBID worker, in sandcrawler repo and pipenv
    ./grobid_tool.py --grobid-host http://localhost:8070 -j 24 extract-zipfile /srv/sandcrawler/tasks/fulltext_web.zip | pv -l > /srv/sandcrawler/tasks/fulltext_web.grobid.json

