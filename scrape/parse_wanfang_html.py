#!/usr/bin/env python3

import sys
import json
from bs4 import BeautifulSoup

def parse_wanfang_html(wanfang_html):
    soup = BeautifulSoup(wanfang_html, "lxml")

    papers = []
    papers_ul = soup.find('ul', **{'class': 'item_detail_list'})
    for paper_li in soup.find_all('li'):
        if paper_li.get('mark') not in ("32", "34"):
            continue
        if not paper_li.find('div'):
            continue
        #print(paper_li)
        title_div = paper_li.div
        title_a = title_div.find('text').a
        is_first_issue = bool(title_div.find('img'))
        subtitle_div = title_div.find('div', **{'class': 'subtitle'})
        summary_div = paper_li.find('div', **{'class': 'summary'})
        tag_div = paper_li.find('div', **{'class': 'tag'})
        paper = dict(
            is_first_issue=is_first_issue,
            url="http://subject.med.wanfangdata.com.cn" + title_a['href'],
            wanfang_id=title_a['href'].split('/')[-1],
            title=title_a.get_text().strip(),
            journal=subtitle_div.find('span', **{'class': 'origin'}).get_text().replace('来源：', '').strip(),
            date=subtitle_div.find('span', **{'class': None}).get_text().replace('时间：', '').strip(),
            #button_text=title_div.button.get_text().strip(),
            abstract=summary_div.get_text().strip(),
            tag=tag_div['text'] or None,
        )
        assert paper['date'].startswith('2020')
        papers.append(paper)
    return papers

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        res = parse_wanfang_html(f.read())
        for paper in res:
            print(json.dumps(paper, sort_keys=True))
