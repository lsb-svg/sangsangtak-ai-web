from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import json
root=Path(__file__).resolve().parent
cfg=json.loads((root/'config.json').read_text(encoding='utf-8'))
dist=root/'dist'
class Check(HTMLParser):
    def __init__(self,page):super().__init__();self.page=page;self.links=[];self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='img':self.images.append(a.get('src',''))
files=list(dist.rglob('*.html'))
assert len(files)==4,files
for page in files:
    text=page.read_text(encoding='utf-8');p=Check(page);p.feed(text)
    for link in p.links+p.images:
        if not link or link=='#':raise AssertionError((page,link))
        if link.startswith(('https://','mailto:')):continue
        resolved=(page.parent/link).resolve()
        if not resolved.is_file():raise AssertionError((page,link))
    assert cfg['store_links']['android'] in p.links
    assert cfg['store_links']['ios'] in p.links
    assert 'localhost' not in text and '{{' not in text
ET.parse(dist/'sitemap.xml')
assert 'sitemap.xml' in (dist/'robots.txt').read_text()
print('VERIFY OK:',len(files),'pages, all relative assets, store links, sitemap parsed')
