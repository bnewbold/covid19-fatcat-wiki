#!/usr/bin/env bash


# invoke this script like:
#
#   pipenv shell
#   CORDDATE=2020-04-03 ./bin/run_pipeline.sh

set -e -u -o pipefail

export TODAY="`TZ=UTC date --iso-8601=date`"

echo "TODAY=$TODAY"
echo "CORDDATE=$CORDDATE"

# versbose:
set -x

mkdir -p metadata fulltext_web

if [ ! -f metadata/cord19.$CORDDATE.csv ]; then
    rm metadata/cord19.$CORDDATE.csv.wip || true
    wget https://archive.org/download/s2-cord19-dataset/cord19.$CORDDATE.csv -O metadata/cord19.$CORDDATE.csv.wip --no-clobber
    mv metadata/cord19.$CORDDATE.csv.wip metadata/cord19.$CORDDATE.csv
fi

if [ ! -f metadata/cord19.$CORDDATE.json ]; then
    ./covid19_tool.py parse-cord19 metadata/cord19.$CORDDATE.csv > metadata/cord19.$CORDDATE.json.wip
    mv metadata/cord19.$CORDDATE.json.wip metadata/cord19.$CORDDATE.json
fi

if [ ! -f metadata/cord19.$CORDDATE.enrich.json ]; then
    cat metadata/cord19.$CORDDATE.json | parallel -j10 --linebuffer --round-robin --pipe ./covid19_tool.py enrich-fatcat - | pv -l > metadata/cord19.$CORDDATE.enrich.json.wip
    mv metadata/cord19.$CORDDATE.enrich.json.wip metadata/cord19.$CORDDATE.enrich.json
fi

if [ ! -f metadata/cord19.$CORDDATE.missing.json ]; then
    cat metadata/cord19.$CORDDATE.enrich.json | jq 'select(.release_id == null) | .cord19_paper' -c > metadata/cord19.$CORDDATE.missing.json.wip
    mv metadata/cord19.$CORDDATE.missing.json.wip metadata/cord19.$CORDDATE.missing.json
fi

if [ ! -f metadata/fatcat_hits.$TODAY.enrich.json ]; then
    ./covid19_tool.py query-fatcat | pv -l > metadata/fatcat_hits.$TODAY.enrich.json.wip
    mv metadata/fatcat_hits.$TODAY.enrich.json.wip metadata/fatcat_hits.$TODAY.enrich.json
fi

if [ ! -f metadata/combined.$TODAY.enrich.json ]; then
    cat metadata/fatcat_hits.$TODAY.enrich.json metadata/cord19.$CORDDATE.enrich.json | ./covid19_tool.py dedupe | pv -l > metadata/combined.$TODAY.enrich.json.wip
    mv metadata/combined.$TODAY.enrich.json.wip metadata/combined.$TODAY.enrich.json
fi

if [ ! -f fatcat_web_$TODAY.log ]; then
    cat metadata/combined.$TODAY.enrich.json | jq .fatcat_release -c | parallel -j20 --linebuffer --round-robin --pipe ./bin/deliver_file2disk.py --disk-dir fulltext_web - | pv -l > fatcat_web_$TODAY.log.wip
    mv fatcat_web_$TODAY.log.wip fatcat_web_$TODAY.log
fi

if [ ! -f metadata/derivatives.$TODAY.stamp ]; then
    ./bin/make_dir_derivatives.sh fulltext_web
    touch metadata/derivatives.$TODAY.stamp
fi

if [ ! -f metadata/combined.$TODAY.fulltext.json ]; then
    ./covid19_tool.py enrich-derivatives metadata/combined.$TODAY.enrich.json --base-dir fulltext_web/ | pv -l > metadata/combined.$TODAY.fulltext.json.wip
    mv metadata/combined.$TODAY.fulltext.json.wip metadata/combined.$TODAY.fulltext.json
fi

echo "## Fulltext Inclusion Counts"
cat metadata/combined.$TODAY.fulltext.json | jq .fulltext_status -r | sort | uniq -c | sort -nr

./covid19_tool.py transform-es metadata/combined.$TODAY.fulltext.json | pv -l | esbulk -verbose -size 1000 -id fatcat_ident -w 8 -index covid19_fatcat_fulltext -type release
