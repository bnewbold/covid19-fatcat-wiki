#!/usr/bin/env bash

set -e -u -o pipefail

export FULLTEXTDIR=$1

if [ ! -d $FULLTEXTDIR ]; then
    echo "Directory does not exist: $FULLTEXTDIR"
    exit -1
fi

# make directories
ls $FULLTEXTDIR/pdf/ | parallel mkdir -p $FULLTEXTDIR/pdftotext/{}
ls $FULLTEXTDIR/pdf/ | parallel mkdir -p $FULLTEXTDIR/thumbnail/{}

fd -I .pdf $FULLTEXTDIR/pdf/ | sed "s/\.pdf//g" | cut -d/ -f3-4 | parallel -j10 ./bin/make_pdf_derivatives.sh $FULLTEXTDIR {}
