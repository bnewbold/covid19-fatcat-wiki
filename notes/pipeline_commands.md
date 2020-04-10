
Dependencies:

    sudo apt install poppler-utils
    pip install requests python-magic

Context:

    export TODAY="`TZ=UTC date --iso-8601=date`"
    export CORDDATE="2020-04-03"

Fetch and transform CORD-19 metadata:

    mkdir -p metadata fulltext_web
    wget https://archive.org/download/s2-cord19-dataset/cord19.$CORDDATE.csv -O metadata/cord19.$CORDDATE.csv metadata
    ./covid19_tool.py parse-cord19 metadata/cord19.$CORDDATE.csv > metadata/cord19.$CORDDATE.json
    cat metadata/cord19.$CORDDATE.json | parallel -j10 --linebuffer --round-robin --pipe ./covid19_tool.py enrich-fatcat - | pv -l > metadata/cord19.$CORDDATE.enrich.json
    cat metadata/cord19.$CORDDATE.enrich.json | jq 'select(.release_id == null) | .cord19_paper' -c > metadata/cord19.$CORDDATE.missing.json

Fetch fatcat query metadata:

    ./covid19_tool.py query-fatcat | pv -l > metadata/fatcat_hits.$TODAY.enrich.json

Combine and de-dupe:

    cat metadata/fatcat_hits.$TODAY.enrich.json metadata/cord19.$CORDDATE.enrich.json | ./covid19_tool.py dedupe | pv -l > metadata/combined.$TODAY.enrich.json

Download fulltext from wayback:

    cat metadata/combined.$TODAY.enrich.json | jq .fatcat_release -c | parallel -j20 --linebuffer --round-robin --pipe ./bin/deliver_file2disk.py --disk-dir fulltext_web - | pv -l > fatcat_web_$TODAY.log

    cut -f1 fatcat_web_$TODAY.log | sort | uniq -c | sort -nr

Update PDF derivative files (pdftotext and PNG thumbnail):

    ./bin/make_dir_derivatives.sh fulltext_web

Fetch GROBID:

    # TODO

Convert GROBID XML to JSON:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/grobid/{}
    fd -I .xml fulltext_web/grobid/ | cut -c18-60 | parallel -j10 "bin/grobid2json.py fulltext_web/grobid/{}.xml > fulltext_web/grobid/{}.json"

Create large derivatives file (including extracted fulltext):

    ./covid19_tool.py enrich-derivatives metadata/combined.$TODAY.enrich.json --base-dir fulltext_web/ | pv -l > metadata/combined.$TODAY.fulltext.json

    cat metadata/combined.$TODAY.fulltext.json | jq .fulltext_status -r | sort | uniq -c | sort -nr


## ES Indices

Create fulltext index, transform to ES schema and index:

    # if existing, first: http delete :9200/covid19_fatcat_fulltext
    http put :9200/covid19_fatcat_fulltext < schema/fulltext_schema.v00.json

    # in fatcat_covid19, pipenv shell
    ./covid19_tool.py transform-es metadata/combined.$TODAY.fulltext.json | pv -l | esbulk -verbose -size 1000 -id fatcat_ident -w 8 -index covid19_fatcat_fulltext -type release

Create and index existing `fatcat_release` schema:

    http put :9200/covid19_fatcat_release < schema/release_schema_v03b.json

    # in fatcat python directory, pipenv shell
    export LC_ALL=C.UTF-8
    cat /srv/fatcat_covid19/src/metadata/combined.$TODAY.enrich.json | jq .fatcat_release -c | rg -v '^null$' | pv -l | ./fatcat_transform.py elasticsearch-releases - - | esbulk -verbose -size 1000 -id ident -w 8 -index covid19_fatcat_release -type release

## GROBID Processing

    zip -r fulltext_web.zip fulltext_web

    # on GROBID worker, in sandcrawler repo and pipenv
    ./grobid_tool.py --grobid-host http://localhost:8070 -j 24 extract-zipfile /srv/sandcrawler/tasks/fulltext_web.zip | pv -l > /srv/sandcrawler/tasks/fulltext_web.grobid.json

