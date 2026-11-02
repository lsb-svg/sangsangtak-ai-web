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

def page(path,title,description,content,robots='index, follow'):
    depth=len(path.parts)-1;home='../'*depth+'index.html';url=PUBLIC_URL+path.as_posix()
    template=(ROOT/'templates/base.html').read_text(encoding='utf-8')
    robots_tag=f'<meta name="robots" content="{robots}">' if robots else ''
    for token,value in {'__TITLE__':ESC(title),'__DESC__':ESC(description),'__CANONICAL__':ESC(url),'__HOME__':home,'__ASSET_PREFIX__':'../'*depth,'__ROBOTS__':robots_tag,'__CONTENT__':content}.items():template=template.replace(token,value)
    target=DIST/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(template,encoding='utf-8')
    assert '__CONTENT__' not in template and '__ROBOTS__' not in template
    return url

def build():
    if DIST.exists():shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT/'static',DIST/'static')
    items=[
        ('general/cutball-drive-mistakes.md','커트볼 드라이브 연습 점검','하회전 공 드라이브가 어려울 때 점검할 내용','index, follow',True,''),
        ('largeball/largeball-differences.md','라지볼과 일반 탁구 차이 (규정 확인용)','라지볼 대회와 용구를 확인할 때 참고할 사항 (공식 최신 요강 검토 중)','noindex, follow',False,'<div class="notice"><strong>대회 규정 확인 안내:</strong> 라지볼 공인 규격과 경기 규칙은 주최 단체 및 대회별 시행 요강에 따라 상이하므로 현재 최신 원문 검토가 진행 중인 참고 페이지입니다 (검색엔진 미색인).</div>'),
        ('para/para-tabletennis-classes.md','장애인 탁구 등급 안내','장애인 탁구 분류와 대회 참가 준비','index, follow',True,'')
    ]
    urls=[]
    sitemap_urls=[]
    cards=[]
    article_template=(ROOT/'templates/article.html').read_text(encoding='utf-8')
    for md_path,title,desc,robots_val,in_sitemap,notice_html in items:
        md=(ROOT/'content'/md_path).read_text(encoding='utf-8')
        rel=Path(md_path).with_suffix('.html')
        wrapper=article_template.replace('__HOME__','../index.html').replace('__ARTICLE__',notice_html+markdown(md)).replace('__DOWNLOADS__',downloads(1))
        u=page(rel,title+' | 상상탁구 AI',desc,wrapper,robots=robots_val)
        urls.append(u)
        if in_sitemap:
            sitemap_urls.append(u)
        cards.append(f'<div class="card"><h3>{ESC(title)}</h3><p>{ESC(desc)}</p><a href="{rel.as_posix()}">글 읽기 →</a></div>')
    sessions=['홈','배우기','AI 장비추천','탁구장','경기일정','맞춤진단','랭킹']
    main='<section class="panel"><h2>상상탁구 AI를 소개합니다</h2><p>일반 탁구·라지볼·장애인 탁구 학습 정보와 장비, 구장, 대회 정보 등을 살펴보는 통합 앱입니다.</p><p><strong>7개 주요 메뉴:</strong> '+', '.join(sessions)+'</p></section><h2>탁구 정보 가이드</h2><div class="cards">'+''.join(cards)+'</div><section class="panel"><h2>공식 앱 다운로드</h2><p>PC에서는 QR을 스마트폰으로 스캔하고, 모바일에서는 스토어 버튼을 누르세요.</p>'+downloads(0)+'</section><p class="muted">이 사이트는 실증을 위한 독립 홍보 웹사이트입니다. 새로운 글 자동 생성 및 실제 설치 수 집계는 포함되지 않습니다.</p>'
    # Question-first SEO landing pages: only reviewed questions generate HTML, appear in QA search, and enter sitemap.
    qa_cards=[]
    qa_items=[]
    hold_count=0
    for item_path in sorted((ROOT/'questions').glob('*.json')):
        data=json.loads(item_path.read_text(encoding='utf-8'))
        required=('id','question','category','app_session','answer','steps','related_guide','review_status','reference_note')
        if any(not data.get(k) for k in required):raise SystemExit('Missing question field: '+str(item_path))
        if not re.fullmatch(r'[a-z0-9-]+',data['id']):raise SystemExit('Invalid question slug')
        if data['review_status'] not in ('editorial_review_required','reviewed'):raise SystemExit('Bad review status')
        # Hold questions are completely excluded from dist HTML, home card list, and search index
        if data['review_status']!='reviewed':
            hold_count+=1
            continue
        rel=Path('questions')/(data['id']+'.html')
        guide='../'+data['related_guide']
        status_text='일반 정보 안내 · 적용 규정과 사실관계는 게시 후에도 정기 확인 필요'
        content='<article class="panel qa-article"><p class="eyebrow">'+ESC(data['category'])+' · 관련 앱 메뉴: '+ESC(data['app_session'])+'</p><h2>'+ESC(data['question'])+'</h2><p class="answer">'+ESC(data['answer'])+'</p><h3>이렇게 확인하세요</h3><ol>'+''.join('<li>'+ESC(step)+'</li>' for step in data['steps'])+'</ol><p class="muted">'+ESC(data['reference_note'])+'</p><p class="review">'+ESC(status_text)+'</p><p><a href="'+ESC(guide)+'">관련 상세 가이드 읽기 →</a></p></article><section class="panel"><h2>상상탁구 AI에서 더 살펴보기</h2><p>앱의 '+ESC(data['app_session'])+' 메뉴와 연계된 정보를 탐색해 보세요.</p>'+downloads(1)+'</section>'
        u=page(rel,data['question']+' | 상상탁구 AI',data['answer'][:130],content,robots='index, follow')
        urls.append(u)
        sitemap_urls.append(u)
        qa_cards.append('<a class="qa-row" href="questions/'+ESC(data['id'])+'.html" data-question="' + ESC(data['question']+' '+data['category'])+'"><span>'+ESC(data['question'])+'</span><small>'+ESC(data['category'])+'</small></a>')
        qa_items.append(data)
    questions_section='<section class="panel"><h2>탁구 질문 · 답변 찾기</h2><p class="muted">구글에서 많이 묻는 유형을 참고한 예시 질문입니다. 실시간 구글 검색어 수집 결과가 아닙니다.</p><label for="question-search">궁금한 탁구 질문 검색</label><input id="question-search" class="qa-search" type="search" placeholder="예: 드라이브, 대회, 탁구장" autocomplete="off"><div id="qa-list">'+''.join(qa_cards)+'</div><p id="qa-empty" hidden>일치하는 질문이 없습니다. 다른 단어로 검색해 주세요.</p></section>'
    main=questions_section+main
    home_url=page(Path('index.html'),'상상탁구 AI | 공식 앱 다운로드 안내','탁구 배우기, 장비, 탁구장, 대회 일정, 랭킹 정보',main,robots='index, follow')
    urls.insert(0,home_url)
    sitemap_urls.insert(0,home_url)
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns);root=ET.Element('{'+ns+'}urlset')
    for url in sitemap_urls:ET.SubElement(ET.SubElement(root,'{'+ns+'}url'),'{'+ns+'}loc').text=url
    ET.ElementTree(root).write(DIST/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+PUBLIC_URL+'sitemap.xml\n',encoding='utf-8')
    for f in ROOT.glob('google*.html'):
        shutil.copy2(f,DIST/f.name)
    for p in DIST.rglob('*.html'):
        s=p.read_text(encoding='utf-8')
        assert 'localhost' not in s and '{{' not in s and '{%' not in s
    print(f'BUILD OK: {len(urls)} HTML pages generated ({hold_count} hold questions excluded from dist); Sitemap: {len(sitemap_urls)} URLs; URL: {PUBLIC_URL}')
if __name__=='__main__':build()
