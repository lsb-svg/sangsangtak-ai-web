from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
import json
import re

root = Path(__file__).resolve().parent
cfg = json.loads((root / 'config.json').read_text(encoding='utf-8'))
app_cfg = json.loads((root / 'app_features.json').read_text(encoding='utf-8'))
dist = root / 'dist'

class Check(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.links = []
        self.images = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag == 'img':
            self.images.append(a.get('src', ''))

# 1. Verify app_features.json category configuration (9 designated categories)
required_categories = {
    "일반 탁구 및 기술",
    "스타플레이어 장비",
    "라켓·러버 및 AI 장비추천",
    "세계·국내 탁구 랭킹",
    "전국 탁구대회",
    "탁구장",
    "라지볼",
    "장애인 탁구",
    "맞춤진단"
}
actual_categories = {c['name'] for c in app_cfg['categories']}
assert required_categories == actual_categories, f"Category mismatch: {required_categories ^ actual_categories}"

# Verify all features have valid release status (ranking & diagnosis are live menus)
for f_key, f_val in app_cfg['features'].items():
    assert f_val['status'] in ('released', 'upcoming', 'beta'), f"Invalid feature status in {f_key}"
assert app_cfg['features']['ranking']['status'] == 'released', "Ranking menu must be recognized as existing in live app"
assert app_cfg['features']['diagnosis']['status'] == 'released', "Diagnosis menu must be recognized as existing in live app"

# 2. Verify all questions data integrity and duplicate prevention
qas = list((root / 'questions').glob('*.json'))
assert len(qas) >= 12, f"Expected at least 12 question candidate files, got {len(qas)}"

seen_ids = set()
seen_questions = set()
reviewed_qas = []
hold_qas = []

for f in qas:
    obj = json.loads(f.read_text(encoding='utf-8'))
    qid = obj['id']
    qtext = obj['question']
    
    # Duplicate check
    assert qid not in seen_ids, f"Duplicate ID: {qid}"
    seen_ids.add(qid)
    
    norm_q = re.sub(r'[\s\?\!\.,·]+', '', qtext.lower())
    assert norm_q not in seen_questions, f"Duplicate question text: {qtext}"
    seen_questions.add(norm_q)
    
    # Extended schema check
    required_fields = (
        'id', 'question', 'category', 'app_session', 'feature_status',
        'answer', 'steps', 'related_guide', 'review_status',
        'source_url', 'verified_date', 'reference_note'
    )
    for field in required_fields:
        assert field in obj and obj[field], f"Missing or empty field '{field}' in {f.name}"
    
    assert obj['category'] in required_categories, f"Invalid category '{obj['category']}' in {f.name}"
    assert obj['feature_status'] in ('released', 'upcoming', 'beta')
    assert obj['review_status'] in ('editorial_review_required', 'reviewed')
    
    if obj['review_status'] == 'reviewed':
        reviewed_qas.append(qid)
    else:
        hold_qas.append(qid)

# Source type differentiation checks for hold items
shinyubin_obj = json.loads((root / 'questions' / 'pro-player-gear-shinyubin.json').read_text(encoding='utf-8'))
assert shinyubin_obj.get('source_type') in ('brand_sponsorship_and_match_record', 'public_media_and_manufacturer_announcement'), "Pro player gear must specify authentic source"
assert shinyubin_obj['question'] == "신유빈 선수는 어떤 라켓과 러버를 사용하나요?", "Shin Yubin question title must match exact specification"
assert "Butterfly Shin Yubin ALC" in shinyubin_obj['answer'], "Must mention exact blade from app data"
assert "Butterfly Dignics 09C" in shinyubin_obj['answer'] and "Butterfly Dignics 05" in shinyubin_obj['answer'], "Must mention exact rubbers from app data"
assert "현재 실사용 여부는 별도로 확인되지 않았습니다" in shinyubin_obj['answer'], "Must not claim current in-match use without verification"

leejunsang_obj = json.loads((root / 'questions' / 'amateur-gear-leejunsang.json').read_text(encoding='utf-8'))
assert leejunsang_obj.get('source_type') == 'founder_direct_check', "Amateur gear verified by founder must be marked founder_direct_check"

# Verify approved QAs maintained for live deployment (initially 6, now 7+)
assert len(reviewed_qas) >= 6, f"Expected at least 6 reviewed QAs, got {len(reviewed_qas)}: {reviewed_qas}"
assert len(hold_qas) >= 6, f"Expected at least 6 hold QAs, got {len(hold_qas)}"

# 3. Verify Google Search Console verification file in dist root
google_files = list(dist.glob('google*.html'))
assert len(google_files) == 1, 'Google verification file must exist in dist root'
assert google_files[0].name == 'googlecdd3231b60f25ebe.html', 'Google verification file name mismatch'
assert google_files[0].read_text(encoding='utf-8').strip() == 'google-site-verification: googlecdd3231b60f25ebe.html'

# 4. Verify generated HTML pages count and isolation of hold content
files = list(dist.rglob('*.html'))
content_files = [p for p in files if not p.name.startswith('google')]
# 4 base pages (index, general, largeball, para) + 6 reviewed QAs = 10 content pages
assert len(content_files) == 4 + len(reviewed_qas), f"Expected 10 content files, got {len(content_files)}"

# Verify hold files are completely absent from dist/ and index.html
for hid in hold_qas:
    assert not (dist / 'questions' / f'{hid}.html').exists(), f"Hold file {hid}.html must NOT exist in dist"
index_html = (dist / 'index.html').read_text(encoding='utf-8')
for hid in hold_qas:
    assert f'questions/{hid}.html' not in index_html, f"Hold file {hid} must NOT be linked in index.html"

# Verify largeball guide is marked noindex and excluded from sitemap
largeball_guide = (dist / 'largeball' / 'largeball-differences.html').read_text(encoding='utf-8')
assert '<meta name="robots" content="noindex, follow">' in largeball_guide, 'largeball guide must have noindex'
assert 'largeball-differences.html' not in (dist / 'sitemap.xml').read_text(encoding='utf-8'), 'noindex page must not be in sitemap'

# 5. Mobile readability & category filter UI checks
assert 'class="cat-filters"' in index_html, "Mobile category filters must exist in index.html"
assert 'class="cat-chip' in index_html, "Category chips must exist in index.html"
assert '<meta name="viewport"' in index_html, "Responsive viewport meta must exist"
assert 'id="question-search"' in index_html, "Question search bar must exist"

# 6. Verify link and asset integrity across all content pages
for page in content_files:
    text = page.read_text(encoding='utf-8')
    p = Check(page)
    p.feed(text)
    for link in p.links + p.images:
        if not link or link == '#':
            raise AssertionError((page, link))
        if link.startswith(('https://', 'mailto:')):
            continue
        resolved = (page.parent / link).resolve()
        if not resolved.is_file():
            raise AssertionError(f"Broken relative link: {link} in {page}")
    assert cfg['store_links']['android'] in p.links, f"Android store link missing in {page}"
    assert cfg['store_links']['ios'] in p.links, f"iOS store link missing in {page}"
    assert 'localhost' not in text and '{{' not in text

# 7. Sitemap verification (3 base pages + 6 reviewed QAs = 9 URLs)
sitemap_tree = ET.parse(dist / 'sitemap.xml')
assert 'sitemap.xml' in (dist / 'robots.txt').read_text()
sitemap_locs = [e.text for e in sitemap_tree.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(sitemap_locs) == 3 + len(reviewed_qas), f"Expected {3+len(reviewed_qas)} URLs in sitemap, got {len(sitemap_locs)}"
assert 'googlecdd3231b60f25ebe.html' not in (dist / 'sitemap.xml').read_text(), 'Google verification file must not be in sitemap'

# 8. QA quality checks for reviewed questions
for rid in reviewed_qas:
    obj = json.loads((root / 'questions' / f'{rid}.json').read_text(encoding='utf-8'))
    output = dist / 'questions' / f'{rid}.html'
    assert output.is_file(), f"Output file missing for {rid}"
    raw = output.read_text(encoding='utf-8')
    assert obj['question'] in raw and obj['answer'] in raw
    assert '<meta name="robots" content="index, follow">' in raw
    assert 'google.com/search?' not in raw
    # Check feature status badge rendering
    assert 'class="status-badge' in raw, f"Status badge missing in {output}"

# 9. Design and Usability Upgrades verification (Phase 3 Design Standards)
assert 'max-width: 1200px' in index_html, "PC wide container layout (1200px) must be configured"
assert 'class="hero-actions"' in index_html, "Hero download action buttons must exist in header"
assert 'btn-hero play' in index_html and 'btn-hero appstore' in index_html, "Google Play and App Store hero buttons required"
assert 'class="feature-grid"' in index_html, "Main app features grid section must exist"

# Exaggeration prevention check: '공식 세팅' must NOT exist in index_html
assert '공식 세팅' not in index_html, "Exaggerated phrase '공식 세팅' must be removed from marketing copy"

# Live menu checks: Ranking & Diagnosis must not be blanket-labeled as upcoming
assert '향후 출시 예정' not in index_html, "Blanket upcoming claims must be removed for existing menus"

required_features_text = [
    '배우기',
    'AI 장비추천',
    '스타플레이어 장비관',
    '탁구장',
    '전국 탁구대회 일정',
    '맞춤진단',
    '탁구 랭킹',
    '라지볼'
]
for feat in required_features_text:
    assert feat in index_html, f"Feature showcase text '{feat}' missing from index.html"

# Star Players Pavilion Mention Check (Shin Yu-bin, Jang Woo-jin, Ma Long, Harimoto)
star_players = ['신유빈', '장우진', '마롱', '하리모토']
for player in star_players:
    assert player in index_html, f"Star player '{player}' must be mentioned in star player gear pavilion description"

# Differentiated sources check: Must mention brand disclosure, tournament records, interviews, founder direct check
assert '공식 브랜드 공시·대회 기록·인터뷰 및 대표 직접 확인' in index_html, "Differentiated source categories must be explicitly stated in gear pavilion description"
assert '용품사 브랜드 공시 및 대회 실사용 기준' not in index_html, "Blanket verification phrasing must be removed"

assert '@media (max-width: 768px)' in index_html, "Tablet 768px media query missing"
assert '@media (max-width: 540px)' in index_html, "Mobile 540px/390px media query missing"
assert 'word-break: keep-all' in index_html, "Korean typography keep-all word-break rule missing"

print(f"VERIFY OK: 9 categories validated, {len(qas)} QAs verified (no duplicates).")
print(f"DIST OK: {len(content_files)} content pages (4 base + {len(reviewed_qas)} approved QAs), google verification file in dist root.")
print(f"ISOLATION OK: {len(hold_qas)} hold QAs strictly excluded from dist HTML and sitemap.")
print(f"SITEMAP OK: {len(sitemap_locs)} URLs parsed, store links and assets 100% verified.")
print(f"ACCURACY OK: No '공식 세팅' claims, ranking and diagnosis live menu status verified, source types distinguished.")
print(f"DESIGN OK: 1200px PC wide layout, hero CTAs, 7 app features, star player gear pavilion, and responsive breakpoints verified.")
