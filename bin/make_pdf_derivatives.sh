#!/usr/bin/env bash

set -e -u -o pipefail

export FULLTEXTDIR=$1
export BLOBPATH=$2
export PDFPATH="$FULLTEXTDIR/pdf/$BLOBPATH.pdf"

if [[ ! -f $PDFPATH ]]; then
    echo "PDF does not exist: $PDFPATH"
    exit -1
fi

echo "processing: $PDFPATH"

if [[ ! -f "$FULLTEXTDIR/pdftotext/$BLOBPATH.txt" ]]; then
    pdftotext $PDFPATH $FULLTEXTDIR/pdftotext/$BLOBPATH.txt
fi

if [[ ! -f "$FULLTEXTDIR/thumbnail/$BLOBPATH.png" ]]; then
    pdftocairo -png -singlefile -scale-to-x 400 -scale-to-y -1 $PDFPATH $FULLTEXTDIR/thumbnail/$BLOBPATH
fi
