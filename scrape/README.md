

## CNKI List

Base URL: <http://en.gzbd.cnki.net/GZBT/brief/Default.aspx>

2020-03-29: "Found 1914 articles"

Uses JS to fetch tables, URLs look like:

    http://en.gzbd.cnki.net/gzbt/request/otherhandler.ashx?action=gzbdFlag&contentID=0&orderStr=1&page=1&grouptype=undefined&groupvalue=undefined

Fetch a bunch:

    seq 0 64 | parallel http get "http://en.gzbd.cnki.net/gzbt/request/otherhandler.ashx?action=gzbdFlag\&contentID=0\&orderStr=1\&page={}\&grouptype=undefined\&groupvalue=undefined" > cnki_tables.html

Parse HTML snippets to JSON:

    ./parse_cnki_tables.py > cnki_metadata.json

The `info_url` seems to work, but the direct PDF download links don't naively.
Maybe need to set a referer, something like that?


## Wanfang Data

    mark=32 指南与共识 Guidelines and consensus
    mark=34 文献速递 Literature Express
    mark=38 中医药防治 Prevention and treatment of traditional Chinese medicine

    wget 'http://subject.med.wanfangdata.com.cn/Channel/7?mark=32' -O wanfang_guidance.2020-03-29.html
    wget 'http://subject.med.wanfangdata.com.cn/Channel/7?mark=34' -O wanfang_papers.2020-03-29.html

    ./parse_wanfang_html.py wanfang_papers.2020-03-29.html > wanfang_papers.2020-03-29.json
    ./parse_wanfang_html.py wanfang_guidance.2020-03-29.html > wanfang_guidance.2020-03-29.json

Download PDFs (without clobbering existing):

    cat wanfang_papers.2020-03-29.json wanfang_guidance.2020-03-29.json | jq .url -r | parallel wget -P fulltext_wanfang --no-clobber {}

    file fulltext_wanfang/* | cut -f2 -d' ' | sort | uniq -c
        144 HTML
        609 PDF

