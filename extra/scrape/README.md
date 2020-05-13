
Need beautiful soup; we aren't using pipenv here:

    sudo apt install python3-bs4 python3-lxml

## CNKI List

Base URL: <http://en.gzbd.cnki.net/GZBT/brief/Default.aspx>

- 2020-03-29: "Found 1914 articles"
- 2020-04-06: "Found 2224 articles"
- 2020-04-13: "Found 2536 articles"

Uses JS to fetch tables, URLs look like:

    http://en.gzbd.cnki.net/gzbt/request/otherhandler.ashx?action=gzbdFlag&contentID=0&orderStr=1&page=1&grouptype=undefined&groupvalue=undefined

Fetch a bunch:

    # bump this seq number based on number of articles divided by 30, round up
    seq 0 85 | parallel http get "http://en.gzbd.cnki.net/gzbt/request/otherhandler.ashx?action=gzbdFlag\&contentID=0\&orderStr=1\&page={}\&grouptype=undefined\&groupvalue=undefined" > metadata/cnki_tables.`date -I`.html

Parse HTML snippets to JSON:

    ./extra/scrape/parse_cnki_tables.py metadata/cnki_tables.`date -I`.html > metadata/cnki_metadata.`date -I`.json

The `info_url` seems to work, but the direct PDF download links don't naively.
Maybe need to set a referer, something like that?


## Wanfang Data

    mark=32 指南与共识 Guidelines and consensus
    mark=34 文献速递 Literature Express
    mark=38 中医药防治 Prevention and treatment of traditional Chinese medicine

    wget 'http://subject.med.wanfangdata.com.cn/Channel/7?mark=32' -O metadata/wanfang_guidance.`date -I`.html
    wget 'http://subject.med.wanfangdata.com.cn/Channel/7?mark=34' -O metadata/wanfang_papers.`date -I`.html
    wget 'http://subject.med.wanfangdata.com.cn/Channel/7?mark=38' -O metadata/wanfang_tcm.`date -I`.html

    ./extra/scrape/parse_wanfang_html.py metadata/wanfang_papers.`date -I`.html > metadata/wanfang_papers.`date -I`.json
    ./extra/scrape/parse_wanfang_html.py metadata/wanfang_guidance.`date -I`.html > metadata/wanfang_guidance.`date -I`.json

Download PDFs (without clobbering existing):

    mkdir -p fulltext_wanfang_download fulltext_wanfang
    cat metadata/wanfang_papers.`date -I`.json metadata/wanfang_guidance.`date -I`.json | jq .url -r | shuf | parallel wget -P fulltext_wanfang_download --no-clobber {}

Rename based on mimetype:

    cp fulltext_wanfang_download/* fulltext_wanfang
    ./bin/fix_extensions.sh fulltext_wanfang

What did we get?

    file fulltext_wanfang/* | awk '{print $2}' | sort | uniq -c
        144 HTML
        609 PDF

2020-04-06:

    wc -l metadata/wanfang_*.json
        200 metadata/wanfang_guidance.2020-04-06.json
        739 metadata/wanfang_papers.2020-04-06.json
        939 total

    144 HTML
    679 PDF

    ls fulltext_wanfang | wc -l
    823

