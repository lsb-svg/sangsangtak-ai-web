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
qas=list((root/'questions').glob('*.json'))
assert len(qas)>=8
reviewed_qas=[json.loads(f.read_text(encoding='utf-8'))['id'] for f in qas if json.loads(f.read_text(encoding='utf-8'))['review_status']=='reviewed']
hold_qas=[json.loads(f.read_text(encoding='utf-8'))['id'] for f in qas if json.loads(f.read_text(encoding='utf-8'))['review_status']!='reviewed']
assert len(reviewed_qas)==6 and len(hold_qas)==2

# Verify Google Search Console verification file
google_files=list(dist.glob('google*.html'))
assert len(google_files)==1, 'Google verification file must exist in dist root'
assert google_files[0].name=='googlecdd3231b60f25ebe.html', 'Google verification file name mismatch'
assert google_files[0].read_text(encoding='utf-8').strip()=='google-site-verification: googlecdd3231b60f25ebe.html', 'Google verification file content mismatch'

files=list(dist.rglob('*.html'))
content_files=[p for p in files if not p.name.startswith('google')]
assert len(content_files)==4+len(reviewed_qas),(len(content_files),4+len(reviewed_qas))

# Verify hold files are completely absent from dist/ and index.html
for hid in hold_qas:
    assert not (dist/'questions'/(hid+'.html')).exists(), f'Hold file {hid}.html must not exist in dist'
index_html=(dist/'index.html').read_text(encoding='utf-8')
for hid in hold_qas:
    assert f'questions/{hid}.html' not in index_html, f'Hold file {hid} must not be referenced in index.html'

# Verify largeball guide is marked noindex and excluded from sitemap
largeball_guide=(dist/'largeball/largeball-differences.html').read_text(encoding='utf-8')
assert '<meta name="robots" content="noindex, follow">' in largeball_guide, 'largeball guide must be noindex'
assert 'largeball-differences.html' not in (dist/'sitemap.xml').read_text(encoding='utf-8'), 'noindex page must not be in sitemap'

for page in content_files:
    text=page.read_text(encoding='utf-8');p=Check(page);p.feed(text)
    for link in p.links+p.images:
        if not link or link=='#':raise AssertionError((page,link))
        if link.startswith(('https://','mailto:')):continue
        resolved=(page.parent/link).resolve()
        if not resolved.is_file():raise AssertionError((page,link))
    assert cfg['store_links']['android'] in p.links
    assert cfg['store_links']['ios'] in p.links
    assert 'localhost' not in text and '{{' not in text
sitemap_tree=ET.parse(dist/'sitemap.xml')
assert 'sitemap.xml' in (dist/'robots.txt').read_text()
sitemap_locs=[e.text for e in sitemap_tree.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(sitemap_locs)==3+len(reviewed_qas),(len(sitemap_locs),3+len(reviewed_qas))
assert 'googlecdd3231b60f25ebe.html' not in (dist/'sitemap.xml').read_text(), 'Google verification file must not be in sitemap'
print('VERIFY OK:',len(content_files),'content pages (4 base + 6 approved QAs), google verification file in dist, relative assets, store links, sitemap parsed')

# QA quality checks for reviewed questions
for rid in reviewed_qas:
    obj=json.loads((root/'questions'/(rid+'.json')).read_text(encoding='utf-8'))
    output=dist/'questions'/(rid+'.html')
    assert output.is_file()
    raw=output.read_text(encoding='utf-8')
    assert obj['question'] in raw and obj['answer'] in raw
    assert '<meta name="robots" content="index, follow">' in raw
    assert 'google.com/search?' not in raw
print(f'QA VERIFY OK: {len(reviewed_qas)} reviewed QAs generated in dist and sitemap; {len(hold_qas)} hold QAs strictly excluded')
