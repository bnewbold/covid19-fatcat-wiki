
Dependencies:

    sudo apt install poppler-utils
    pipenv shell
    pip install requests python-magic

Fetch and transform metadata:

    mkdir -p metadata fulltext_web
    wget https://archive.org/download/s2-cord19-dataset/cord19.2020-03-20.csv
    mv cord19.2020-03-20.csv metadata
    ./scripts/parse_cord19_csv.py metadata/cord19.2020-03-20.csv > metadata/cord19.2020-03-20.json
    cat metadata/cord19.2020-03-20.json | parallel -j10 --linebuffer --round-robin --pipe ./scripts/cord19_fatcat_enrich.py - | pv -l > metadata/cord19.2020-03-20.enrich.json
    cat metadata/cord19.2020-03-20.enrich.json | jq 'select(.release_id == null) | .cord19_paper' -c > metadata/cord19.2020-03-20.missing.json

Existing fatcat ES transform:

    cat /srv/covid19.fatcat.wiki/src/metadata/cord19.2020-03-20.enrich.json | jq .fatcat_release -c | rg -v '^null$' | ./fatcat_transform.py elasticsearch-releases - - | pv -l > cord19.2020-03-20.fatcat_es.json

Download fulltext from wayback:

    cat metadata/cord19.2020-03-20.enrich.json | jq .fatcat_release -c | parallel -j20 --linebuffer --round-robin --pipe ./scripts/deliver_file2disk.py --disk-dir fulltext_web - | pv -l > fatcat_web_20200320.log

Extract text from PDFs:

    ls fulltext_web/pdf/ | parallel mkdir -p fulltext_web/pdftotext/{}
    fd .pdf fulltext_web/pdf/ | cut -c18-60 | parallel -j10 pdftotext fulltext_web/pdf/{}.pdf fulltext_web/pdftotext/{}.txt

