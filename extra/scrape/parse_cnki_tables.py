#!/usr/bin/env python3

import sys
import json
from bs4 import BeautifulSoup

def parse_cnki_tables(cnki_html):
    soup = BeautifulSoup(cnki_html, "lxml")

    papers = []
    for table in soup.find_all('table'):
        for row in table.tbody.find_all('tr'):
            paper = dict()
            for col in ('seq', 'author', 'date'):
                paper[col] = row.find('td', **{'class': col}).get_text().strip().replace('\n', ' ')
            name_td = row.find('td', **{'class': 'name'})
            operat_td = row.find('td', **{'class': 'operat'})
            paper['title'] = name_td.a.get_text().strip().replace('\n', ' ')
            paper['seq'] = int(paper['seq'])
            paper['authors'] = [a for a in paper.pop('author').split(';') if a]
            mark = row.find('span', **{'class': 'markOricon'})

            paper['info_url'] = "http://en.gzbd.cnki.net" + name_td.a['href']
            paper['pdf_url'] = "http://en.gzbd.cnki.net" + operat_td.find('a', **{'class': 'icon-download'})['href']
            try:
                paper['html_url'] = "http://en.gzbd.cnki.net" + operat_td.find('a', **{'class': 'icon-html'})['href']
            except TypeError:
                try:
                    paper['read_url'] = "http://en.gzbd.cnki.net" + operat_td.find('a', **{'class': 'icon-read'})['href']
                except TypeError:
                    #print(operat_td, file=sys.stderr)
                    pass

            if 'FileName=' in paper['info_url']:
                params = paper['info_url'].split('?')[1].split('&')
                for p in params:
                    if p.startswith("FileName="):
                        paper['cnki_id'] = p.replace("FileName=", "")
                        break

            if mark and mark.get_text() == 'CN':
                paper['is_cn'] = True
            else:
                paper['is_cn'] = False
            papers.append(paper)
    return papers

if __name__ == "__main__":
    with open("cnki_tables.html", "r") as f:
        res = parse_cnki_tables(f.read())
        for paper in res:
            print(json.dumps(paper, sort_keys=True))
