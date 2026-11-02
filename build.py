#!/usr/bin/env python3
"""Zero-dependency static builder. Does not generate new articles or fact-check regulations."""
from pathlib import Path
import os, json, html, re, shutil, xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
CONFIG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
PUBLIC_URL=os.getenv('PUBLIC_URL',CONFIG['public_url']).rstrip('/')+'/'
if not PUBLIC_URL.startswith('https://') or urlparse(PUBLIC_URL).netloc == '':
    raise SystemExit('PUBLIC_URL must be an absolute HTTPS URL')
ESC=lambda text: html.escape(str(text),quote=True)

def markdown(text):
    out=[]; in_list=False
    def close():
        nonlocal in_list
        if in_list: out.append('</ul>'); in_list=False
    for raw in text.splitlines():
        s=raw.strip()
        if not s: close(); continue
        if s.startswith('- '):
            if not in_list: out.append('<ul>');in_list=True
            out.append('<li>'+ESC(s[2:])+'</li>');continue
        close()
        for prefix,tag in [('### ','h3'),('## ','h2'),('# ','h1')]:
            if s.startswith(prefix):out.append(f'<{tag}>{ESC(s[len(prefix):])}</{tag}>');break
        else: out.append('<p>'+ESC(s)+'</p>')
    close();return '\n'.join(out)

def downloads(depth):
    qr_prefix='../'*depth
    links=CONFIG['store_links']
    result=['<div class="downloads">']
    for os_name,img,label,style in [('android','android.png','Google Play',''),('ios','ios.png','App Store',' ios')]:
        url=links[os_name]
        if not url.startswith('https://'):raise SystemExit('Invalid store URL')
        result.append(f'<div class="download"><img src="{qr_prefix}static/qr/{img}" alt="{label} QR" width="210" height="210"><p><a class="btn{style}" href="{ESC(url)}" target="_blank" rel="noopener noreferrer">{label} 다운로드</a></p></div>')
    return '\n'.join(result+['</div>'])

def page(path,title,description,content):
    depth=len(path.parts)-1;home='../'*depth+'index.html';url=PUBLIC_URL+path.as_posix()
    template=(ROOT/'templates/base.html').read_text(encoding='utf-8')
    for token,value in {'__TITLE__':ESC(title),'__DESC__':ESC(description),'__CANONICAL__':ESC(url),'__HOME__':home,'__CONTENT__':content}.items():template=template.replace(token,value)
    target=DIST/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(template,encoding='utf-8')
    assert '__CONTENT__' not in template
    return url

def build():
    if DIST.exists():shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT/'static',DIST/'static')
    items=[('general/cutball-drive-mistakes.md','커트볼 드라이브 연습 점검','하회전 공 드라이브가 어려울 때 점검할 내용'),('largeball/largeball-differences.md','라지볼과 일반 탁구 차이','라지볼 대회와 용구를 확인할 때 참고할 사항'),('para/para-tabletennis-classes.md','장애인 탁구 등급 안내','장애인 탁구 분류와 대회 참가 준비')]
    urls=[]
    cards=[]
    article_template=(ROOT/'templates/article.html').read_text(encoding='utf-8')
    for md_path,title,desc in items:
        md=(ROOT/'content'/md_path).read_text(encoding='utf-8')
        rel=Path(md_path).with_suffix('.html')
        wrapper=article_template.replace('__HOME__','../index.html').replace('__ARTICLE__',markdown(md)).replace('__DOWNLOADS__',downloads(1))
        urls.append(page(rel,title+' | 상상탁구 AI',desc,wrapper))
        cards.append(f'<div class="card"><h3>{ESC(title)}</h3><p>{ESC(desc)}</p><a href="{rel.as_posix()}">글 읽기 →</a></div>')
    sessions=['홈','배우기','AI 장비추천','탁구장','경기일정','맞춤진단','랭킹']
    main='<section class="panel"><h2>상상탁구 AI를 소개합니다</h2><p>일반 탁구·라지볼·장애인 탁구 학습 정보와 장비, 구장, 대회 정보 등을 살펴보는 통합 앱입니다.</p><p><strong>7개 주요 메뉴:</strong> '+', '.join(sessions)+'</p></section><h2>탁구 정보 가이드</h2><div class="cards">'+''.join(cards)+'</div><section class="panel"><h2>공식 앱 다운로드</h2><p>PC에서는 QR을 스마트폰으로 스캔하고, 모바일에서는 스토어 버튼을 누르세요.</p>'+downloads(0)+'</section><p class="muted">이 사이트는 실증을 위한 독립 홍보 웹사이트입니다. 새로운 글 자동 생성 및 실제 설치 수 집계는 포함되지 않습니다.</p>'
    urls.insert(0,page(Path('index.html'),'상상탁구 AI | 공식 앱 다운로드 안내','탁구 배우기, 장비, 탁구장, 대회 일정, 랭킹 정보',main))
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns);root=ET.Element('{'+ns+'}urlset')
    for url in urls:ET.SubElement(ET.SubElement(root,'{'+ns+'}url'),'{'+ns+'}loc').text=url
    ET.ElementTree(root).write(DIST/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+PUBLIC_URL+'sitemap.xml\n',encoding='utf-8')
    for p in DIST.rglob('*.html'):
        s=p.read_text(encoding='utf-8')
        assert 'localhost' not in s and '{{' not in s and '{%' not in s
    print('BUILD OK:',len(urls),'HTML pages; URL:',PUBLIC_URL)
if __name__=='__main__':build()
