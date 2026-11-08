#!/usr/bin/env python3
"""Zero-dependency static builder. Does not generate new articles or fact-check regulations."""
from pathlib import Path
import os, json, html, re, shutil, csv, xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
CONFIG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
APP_CONFIG=json.loads((ROOT/'app_features.json').read_text(encoding='utf-8'))
FEATURES=APP_CONFIG['features']
CATEGORIES=APP_CONFIG['categories']
VALID_CATEGORIES={c['name'] for c in CATEGORIES}

PUBLIC_URL=os.getenv('PUBLIC_URL',CONFIG['public_url']).rstrip('/')+'/'
if not PUBLIC_URL.startswith('https://') or urlparse(PUBLIC_URL).netloc == '':
    raise SystemExit('PUBLIC_URL must be an absolute HTTPS URL')
ESC=lambda text: html.escape(str(text),quote=True)

def check_duplicates(questions_data):
    seen_ids = set()
    seen_questions = set()
    for item in questions_data:
        qid = item['id']
        if qid in seen_ids:
            raise SystemExit(f'Duplicate question id detected: {qid}')
        seen_ids.add(qid)
        
        # Normalized question text check (strip whitespaces and punctuation)
        norm = re.sub(r'[\s\?\!\.,·]+', '', item['question'].lower())
        if norm in seen_questions:
            raise SystemExit(f'Duplicate or near-identical question text detected: {item["question"]}')
        seen_questions.add(norm)

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

def hero_downloads():
    links=CONFIG['store_links']
    return (
        '<div class="hero-actions">'
        f'<a class="btn-hero play" href="{ESC(links["android"])}" target="_blank" rel="noopener noreferrer">Google Play 다운로드</a>'
        f'<a class="btn-hero appstore" href="{ESC(links["ios"])}" target="_blank" rel="noopener noreferrer">App Store 다운로드</a>'
        '</div>'
    )

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
    replacements={
        '__TITLE__': ESC(title),
        '__DESC__': ESC(description),
        '__CANONICAL__': ESC(url),
        '__HOME__': home,
        '__ASSET_PREFIX__': '../'*depth,
        '__ROBOTS__': robots_tag,
        '__HERO_DOWNLOADS__': hero_downloads(),
        '__CONTENT__': content
    }
    for token,value in replacements.items():
        template=template.replace(token,value)
    target=DIST/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(template,encoding='utf-8')
    assert '__CONTENT__' not in template and '__ROBOTS__' not in template and '__HERO_DOWNLOADS__' not in template
    return url

def build_app_features_section():
    # 7 key features with authentic app status, honest menu descriptions, and no exaggerated claims
    cards=[
        (
            '📚',
            '배우기',
            '초보자 기본자세부터 하회전·상회전 드라이브, 서브, 리시브 등 체계적인 원포인트 레슨과 기술 팁을 앱에서 제공합니다.',
            'live',
            '정식 서비스 중',
            False
        ),
        (
            '🏓',
            'AI 장비추천 &amp; 스타플레이어 장비관',
            '개인 맞춤 라켓·러버 탐색 기능과 함께, 신유빈·장우진·마롱·하리모토 등 국내외 주요 선수들의 장비 조합 정보를 앱에서 살펴보실 수 있습니다 (정보 출처: 공식 브랜드 공시·대회 기록·인터뷰 및 대표 직접 확인 등으로 구분 관리).',
            'live',
            '정식 서비스 중',
            True
        ),
        (
            '📍',
            '전국 탁구장 찾기',
            '내 위치 주변 가까운 탁구장의 기본 위치 정보와 등록 목록을 검색할 수 있으며, 운영시간과 세부 시설은 방문 전 직접 확인하는 것이 좋습니다.',
            'live',
            '정식 서비스 중',
            False
        ),
        (
            '🏆',
            '전국 탁구대회 일정',
            '전국 오픈대회, 시·도 협회 대회, 생활체육 대회 일정과 참가 접수 기간, 대회 요강을 실시간으로 확인합니다.',
            'live',
            '정식 서비스 중',
            False
        ),
        (
            '🔍',
            '맞춤진단',
            '앱 내 맞춤진단 메뉴를 통해 플레이 스타일과 전형을 점검하고 실력 향상을 위한 가이드를 제공합니다 (세부 진단 항목은 지속 업데이트).',
            'live',
            '정식 서비스 중',
            False
        ),
        (
            '📊',
            '탁구 랭킹',
            '상상탁구 AI 앱의 랭킹 메뉴에서 국내외 탁구 선수들의 랭킹 및 순위 정보를 안내합니다.',
            'live',
            '정식 서비스 중',
            False
        ),
        (
            '🤝',
            '일반탁구 · 라지볼 · 장애인 탁구',
            '일반 규격 탁구뿐만 아니라 시니어 라지볼, 패럴림픽 장애인 탁구(클래스 1~11)까지 모두를 위한 통합 탁구 정보를 제공합니다.',
            'live',
            '통합 지원',
            False
        )
    ]
    card_htmls=[]
    for icon,title,desc,status_cls,status_text,is_hl in cards:
        hl_class=' highlight' if is_hl else ''
        card_htmls.append(
            f'<div class="feature-card{hl_class}">'
            '<div class="feature-top">'
            f'<span class="feature-icon">{icon}</span>'
            f'<span class="feat-status {status_cls}">{status_text}</span>'
            '</div>'
            f'<h3>{title}</h3>'
            f'<p>{desc}</p>'
            '</div>'
        )
    return (
        '<section class="panel">'
        '<h2>상상탁구 AI 핵심 기능 한눈에 보기</h2>'
        '<p class="muted">스마트폰 하나로 탁구의 기술 학습, 장비 탐색, 구장 및 대회 검색, 진단까지 원스톱으로 누리세요.</p>'
        '<div class="feature-grid">' + ''.join(card_htmls) + '</div>'
        '</section>'
    )

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
    
    # Load and validate all question files
    all_questions=[]
    for item_path in sorted((ROOT/'questions').glob('*.json')):
        data=json.loads(item_path.read_text(encoding='utf-8'))
        required=('id','question','category','app_session','feature_status','answer','steps','related_guide','review_status','source_url','verified_date','reference_note')
        if any(not data.get(k) for k in required):raise SystemExit('Missing question field: '+str(item_path))
        if not re.fullmatch(r'[a-z0-9-]+',data['id']):raise SystemExit('Invalid question slug: '+data['id'])
        if data['category'] not in VALID_CATEGORIES:raise SystemExit(f'Invalid category: {data["category"]} in {item_path.name}')
        if data['feature_status'] not in ('released','upcoming','beta'):raise SystemExit(f'Invalid feature_status: {data["feature_status"]} in {item_path.name}')
        if data['review_status'] not in ('editorial_review_required','reviewed'):raise SystemExit('Bad review status: '+item_path.name)
        all_questions.append(data)
    
    # Check for duplicates across all question candidates
    check_duplicates(all_questions)

    # Load plan CSV to enforce content_status == 'live' for public distribution
    plan_csv_path = ROOT / 'content_plan_110.csv'
    live_slugs = set()
    if plan_csv_path.exists():
        with open(plan_csv_path, 'r', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if r.get('content_status') == 'live' and r.get('slug'):
                    live_slugs.add(r['slug'])

    qa_cards=[]
    qa_items=[]
    hold_count=0
    approved_categories=set()
    for data in all_questions:
        qid = data['id']
        # Deployable questions MUST meet all 4 conditions:
        # 1. JSON review_status == 'reviewed'
        # 2. CSV content_status == 'live'
        # 3. JSON slug matches CSV live slug
        # 4. Mandatory content schema validated
        # All ready, planned, hold, editorial_review_required or unlisted questions are strictly excluded.
        if data['review_status'] != 'reviewed' or qid not in live_slugs:
            hold_count+=1
            continue
        approved_categories.add(data['category'])
        rel=Path('questions')/(data['id']+'.html')
        guide='../'+data['related_guide']
        status_text='일반 정보 안내 · 적용 규정과 사실관계는 게시 후에도 정기 확인 필요'
        
        # Branch CTA and status badge based on actual feature_status
        f_status=data['feature_status']
        feat_key=next((c['feature_key'] for c in CATEGORIES if c['name']==data['category']),'home')
        feat_meta=FEATURES.get(feat_key,{})
        if f_status=='released':
            badge_html='<span class="status-badge live">정식 서비스 중</span>'
            cta_html=f'<p class="feature-status">관련 앱 메뉴: <strong>{ESC(data["app_session"])}</strong> {badge_html}</p><p>{ESC(feat_meta.get("cta_text", "앱에서 관련 기능을 바로 이용해 보세요."))}</p>'
        elif f_status=='beta':
            badge_html='<span class="status-badge beta">베타 준비 중</span>'
            cta_html=f'<p class="feature-status">관련 앱 메뉴: <strong>{ESC(data["app_session"])}</strong> {badge_html}</p><p>{ESC(feat_meta.get("cta_text", "현재 고도화 중인 기능입니다."))}</p>'
        else:
            badge_html='<span class="status-badge upcoming">출시 예정</span>'
            cta_html=f'<p class="feature-status">관련 앱 메뉴: <strong>{ESC(data["app_session"])}</strong> {badge_html}</p><p>{ESC(feat_meta.get("cta_text", "향후 업데이트에서 정식 오픈될 예정입니다."))}</p>'
            
        content='<article class="panel qa-article"><p class="eyebrow">'+ESC(data['category'])+' · 앱 연동 메뉴: '+ESC(data['app_session'])+'</p><h2>'+ESC(data['question'])+'</h2><p class="answer">'+ESC(data['answer'])+'</p><h3>이렇게 확인하세요</h3><ol>'+''.join('<li>'+ESC(step)+'</li>' for step in data['steps'])+'</ol><p class="muted">'+ESC(data['reference_note'])+'</p><p class="review">'+ESC(status_text)+'</p><p><a href="'+ESC(guide)+'">관련 상세 가이드 읽기 →</a></p></article><section class="panel"><h2>상상탁구 AI에서 더 살펴보기</h2>'+cta_html+downloads(1)+'</section>'
        u=page(rel,data['question']+' | 상상탁구 AI',data['answer'][:130],content,robots='index, follow')
        urls.append(u)
        sitemap_urls.append(u)
        qa_cards.append('<a class="qa-row" href="questions/'+ESC(data['id'])+'.html" data-category="'+ESC(data['category'])+'" data-question="' + ESC(data['question']+' '+data['category'])+'"><span>'+ESC(data['question'])+'</span><small>'+ESC(data['category'])+'</small></a>')
        qa_items.append(data)
    
    # Render category filter chips
    chips_html=['<button class="cat-chip active" data-cat="all">전체</button>']
    for cat in CATEGORIES:
        if cat['name'] in approved_categories:
            chips_html.append(f'<button class="cat-chip" data-cat="{ESC(cat["name"])}">{ESC(cat["name"])}</button>')
    chips_section='<div class="cat-filters">'+''.join(chips_html)+'</div>'
    
    questions_section=(
        '<section class="panel">'
        '<h2>탁구 질문 · 답변 찾기</h2>'
        '<p class="muted">궁금한 질문을 검색하거나 카테고리별로 살펴보세요. 실시간 구글 검색어 수집 결과가 아닙니다.</p>'
        '<div class="qa-search-box">'
        '<label class="qa-search-label" for="question-search">궁금한 탁구 질문 검색</label>'
        '<input id="question-search" class="qa-search" type="search" placeholder="예: 드라이브, 대회, 탁구장, 장애인, 러버" autocomplete="off">'
        '</div>'
        +chips_section+
        '<div id="qa-list">'+''.join(qa_cards)+'</div>'
        '<p id="qa-empty" hidden>일치하는 질문이 없습니다. 다른 단어나 카테고리를 선택해 주세요.</p>'
        '</section>'
    )
    
    app_features_section = build_app_features_section()
    
    guides_section=(
        '<section class="panel">'
        '<h2>탁구 정보 가이드</h2>'
        '<p class="muted">초보자부터 동호인까지 참고할 수 있는 필수 기술 및 규정 안내 문서입니다.</p>'
        '<div class="cards">'+''.join(cards)+'</div>'
        '</section>'
    )
    
    downloads_section=(
        '<section class="panel">'
        '<h2>공식 앱 다운로드</h2>'
        '<p>PC에서는 QR을 스마트폰 카메라로 스캔하시고, 모바일에서는 아래 스토어 버튼을 터치하여 바로 설치하세요.</p>'
        +downloads(0)+
        '</section>'
    )
    
    disclaimer='<p class="muted" style="text-align: center; margin-top: 1.5rem;">이 사이트는 실증 및 안내를 위한 상상탁구 AI 공식 홍보 웹사이트입니다. 새로운 글 자동 생성 및 실제 설치 수 집계는 포함되지 않습니다.</p>'
    
    main = app_features_section + questions_section + guides_section + downloads_section + disclaimer
    
    home_url=page(Path('index.html'),'상상탁구 AI | 탁구 정보와 공식 앱 다운로드','탁구 배우기, AI 장비추천, 스타플레이어 장비관, 전국 탁구장, 대회 일정, 맞춤진단, 랭킹 정보',main,robots='index, follow')
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

if __name__=='__main__':
    build()
