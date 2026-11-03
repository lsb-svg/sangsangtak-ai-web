# -*- coding: utf-8 -*-
import csv, json
from pathlib import Path

# Load existing 21 questions
existing = {}
for p in sorted(Path('questions').glob('*.json')):
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
        existing[d['id']] = d

assert len(existing) == 21

# Categories and their target counts:
# 1. 스타플레이어·아마추어 장비관: 20
# 2. AI 장비추천: 15
# 3. 배우기·기술 레슨: 12
# 4. 전국 탁구대회: 15
# 5. 라지볼: 12
# 6. 장애인 탁구: 10
# 7. 국내·세계 랭킹: 12
# 8. 탁구장·맞춤진단·앱 활용: 14
# Total = 110

items = []

# Group 1: 스타플레이어·아마추어 장비관 (20 items)
# Existing (8):
# amateur-gear-leejunsang (hold)
# pro-player-gear-fanzhendong (hold)
# pro-player-gear-felix-lebrun (hold)
# pro-player-gear-harimoto-tomokazu (hold)
# pro-player-gear-jangwoojin (hold)
# pro-player-gear-malong (hold)
# pro-player-gear-miwa-harimoto (hold)
# pro-player-gear-shinyubin (hold)

# New planned (12):
# pro-player-gear-limjonghoon (임종훈)
# pro-player-gear-ahnjaehyun (안재현)
# pro-player-gear-leesangsu (이상수)
# pro-player-gear-ohjunsung (오준성)
# pro-player-gear-jeonjihee (전지희)
# pro-player-gear-joocheonhui (주천희)
# pro-player-gear-kimnayeong (김나영)
# pro-player-gear-suhhyowon (서효원)
# pro-player-gear-linyunju (린윈루)
# pro-player-gear-sunyingsha (쑨잉샤)
# pro-player-gear-hinahayata (하야타 히나)
# pro-player-gear-mimaito (이토 미마)

g1 = [
    # Existing
    ('pro-player-gear-shinyubin', '스타플레이어·아마추어 장비관', '신유빈 선수는 어떤 라켓과 러버를 사용하나요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (Butterfly Global)', '2026-01-20', '007', '', ''),
    ('pro-player-gear-jangwoojin', '스타플레이어·아마추어 장비관', '장우진 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (공식 확인)', '2026-01-15', '008', '', ''),
    ('pro-player-gear-malong', '스타플레이어·아마추어 장비관', '마롱 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (공식 확인)', '2026-01-05', '009', '', ''),
    ('pro-player-gear-fanzhendong', '스타플레이어·아마추어 장비관', '판전둥(판젠동) 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (공식 확인)', '2026-01-10', '010', '', ''),
    ('pro-player-gear-harimoto-tomokazu', '스타플레이어·아마추어 장비관', '하리모토 토모카즈 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (Butterfly Global)', '2025-10-11', '011', '', ''),
    ('pro-player-gear-felix-lebrun', '스타플레이어·아마추어 장비관', '펠릭스 르브런 선수가 사용하는 펜홀더 라켓과 러버는 무엇인가요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (Tibhar Global)', '2026-02-01', '012', '', ''),
    ('pro-player-gear-miwa-harimoto', '스타플레이어·아마추어 장비관', '하리모토 미와 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?', 'AI 장비추천', 'hold', 'P1', 'starPlayerData.ts (Butterfly Global)', '2025-12-18', '013', '', ''),
    ('amateur-gear-leejunsang', '스타플레이어·아마추어 장비관', '아마추어 탁구인 이준상의 라켓과 러버 구성은 어떻게 되나요?', 'AI 장비추천', 'hold', 'P2', 'starPlayerData.ts (대표 제공)', '2026-08-21', '014', '', ''),
    # Planned
    ('pro-player-gear-limjonghoon', '스타플레이어·아마추어 장비관', '임종훈 선수가 사용하는 탁구 라켓과 러버 세팅은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-01-10', '022', '', ''),
    ('pro-player-gear-ahnjaehyun', '스타플레이어·아마추어 장비관', '안재현 선수의 라켓 블레이드와 러버 구성은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-01-12', '023', '', ''),
    ('pro-player-gear-leesangsu', '스타플레이어·아마추어 장비관', '이상수 선수가 사용하는 공격형 라켓과 러버는?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-01-08', '024', '', ''),
    ('pro-player-gear-ohjunsung', '스타플레이어·아마추어 장비관', '오준성 선수의 주력 블레이드와 러버 조합은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-01-15', '025', '', ''),
    ('pro-player-gear-jeonjihee', '스타플레이어·아마추어 장비관', '전지희 선수가 사용하는 왼손 셰이크핸드 라켓과 러버는?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (Butterfly Global)', '2026-01-18', '026', '', ''),
    ('pro-player-gear-joocheonhui', '스타플레이어·아마추어 장비관', '주천희 선수의 블레이드 및 전후면 러버 조합은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-01-15', '027', '', ''),
    ('pro-player-gear-kimnayeong', '스타플레이어·아마추어 장비관', '김나영 선수가 사용하는 국가대표 탁구 장비는?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-02-05', '028', '', ''),
    ('pro-player-gear-suhhyowon', '스타플레이어·아마추어 장비관', '서효원 선수의 수비형 라켓 및 롱핌플 러버 구성은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공개자료 확인)', '2025-12-10', '029', '', ''),
    ('pro-player-gear-linyunju', '스타플레이어·아마추어 장비관', '린윈루 선수의 치키타 특화 라켓과 러버 세팅은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (Butterfly Global)', '2026-01-05', '030', '', ''),
    ('pro-player-gear-sunyingsha', '스타플레이어·아마추어 장비관', '쑨잉샤 선수가 사용하는 세계 1위 라켓과 러버는?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (공식 확인)', '2026-01-15', '031', '', ''),
    ('pro-player-gear-hinahayata', '스타플레이어·아마추어 장비관', '하야타 히나 선수의 주력 블레이드와 러버 구성은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (Nittaku Global)', '2026-01-10', '032', '', ''),
    ('pro-player-gear-mimaito', '스타플레이어·아마추어 장비관', '이토 미마 선수의 이성 숏핌플 러버 및 라켓 조합은?', 'AI 장비추천', 'planned', 'P2', 'starPlayerData.ts (Nittaku Global)', '2026-01-10', '033', '', ''),
]
assert len(g1) == 20

# Group 2: AI 장비추천 (15 items)
# Existing (2):
# rubber-choice (live)
# gear-recommend-drive-combo (hold)

# New planned (13):
# gear-recommend-beginner-racket (초보자 입문용 라켓)
# gear-recommend-inner-vs-outer (이너카본 vs 아우터카본 차이)
# gear-recommend-rubber-hardness (러버 경도 선택 기준)
# gear-recommend-tacky-vs-tension (점착성 러버와 텐션 러버 차이)
# gear-recommend-smash-drive-style (스매시형 vs 드라이브형 라켓 구분)
# gear-recommend-penholder-to-shake (펜홀더에서 셰이크핸드 전향 시 라켓)
# gear-recommend-lightweight (가벼운 라켓 조합 추천)
# gear-recommend-backhand-control (백핸드 쇼트·블록 안정성 러버)
# gear-recommend-rubber-replacement-cycle (탁구 러버 교체 주기와 관리법)
# gear-recommend-budget-100k (10만원대 가성비 탁구 라켓 추천 세트)
# gear-recommend-wood-vs-carbon (순수 5겹 합판 vs 특수소재 카본 라켓)
# gear-recommend-shakehand-grip-type (셰이크핸드 FL 그립과 ST 그립 차이점)
# gear-recommend-cleanser-adhesive-sheet (러버 클리너와 보호필름 관리 기준)

g2 = [
    # Existing
    ('rubber-choice', 'AI 장비추천', '초보자는 탁구 라켓과 러버를 어떻게 고르나요?', 'AI 장비추천', 'live', 'P0', 'content/questions/rubber-choice.json', '2026-08-20', '005', '2026-08-20', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/rubber-choice.html'),
    ('gear-recommend-drive-combo', 'AI 장비추천', '드라이브 전형 탁구 동호인을 위한 추천 라켓과 러버 조합은?', 'AI 장비추천', 'hold', 'P1', 'questions/gear-recommend-drive-combo.json', '2026-08-28', '015', '', ''),
    # Planned
    ('gear-recommend-beginner-racket', 'AI 장비추천', '탁구 입문 초보자를 위한 추천 완성형 라켓과 조합형 라켓 차이는?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '034', '', ''),
    ('gear-recommend-inner-vs-outer', 'AI 장비추천', '이너카본과 아우터카본 블레이드의 반발력 및 타구감 차이는?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '035', '', ''),
    ('gear-recommend-rubber-hardness', 'AI 장비추천', '탁구 러버 경도(45도·47.5도·50도)는 어떻게 선택해야 하나요?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '036', '', ''),
    ('gear-recommend-tacky-vs-tension', 'AI 장비추천', '점착성 러버와 일반 하이텐션 러버의 스핀 및 비거리 차이는?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '037', '', ''),
    ('gear-recommend-smash-drive-style', 'AI 장비추천', '전진 속공 스매시 전형에 어울리는 블레이드와 러버 조합은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '038', '', ''),
    ('gear-recommend-penholder-to-shake', 'AI 장비추천', '펜홀더에서 셰이크핸드로 전향할 때 적응하기 쉬운 라켓 세팅은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '039', '', ''),
    ('gear-recommend-lightweight', 'AI 장비추천', '손목 부담을 줄여주는 가벼운 탁구 라켓·러버 무게 조합 기준은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '040', '', ''),
    ('gear-recommend-backhand-control', 'AI 장비추천', '백핸드 쇼트와 안정적인 블록을 위한 추천 러버 조합은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '041', '', ''),
    ('gear-recommend-rubber-replacement-cycle', 'AI 장비추천', '탁구 러버의 수명 주기와 교체 시기를 판별하는 기준은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '042', '', ''),
    ('gear-recommend-budget-100k', 'AI 장비추천', '10만원대 예산으로 맞출 수 있는 가성비 탁구 라켓·러버 추천은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '043', '', ''),
    ('gear-recommend-wood-vs-carbon', 'AI 장비추천', '순수 5겹 합판 라켓과 카본 특수소재 라켓의 장단점 비교는?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '044', '', ''),
    ('gear-recommend-shakehand-grip-type', 'AI 장비추천', '셰이크핸드 FL 그립과 ST 그립의 형태 및 손 크기별 선택법은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '045', '', ''),
    ('gear-recommend-cleanser-adhesive-sheet', 'AI 장비추천', '러버 클리너 사용법과 점착 보호필름 부착 관리 요령은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '046', '', ''),
]
assert len(g2) == 15

# Group 3: 배우기·기술 레슨 (12 items)
# Existing (2):
# drive-long (live)
# drive-net (live)

# New planned (10):
# lesson-forehand-stroke-posture (포핸드 기본 스트로크 자세)
# lesson-backhand-short-timing (백핸드 쇼트의 정확한 타점)
# lesson-backspin-push-technique (보스커트/하회전 푸시 기술)
# lesson-under-spin-serve-basics (하회전 서브 기본 회전 넣는 법)
# lesson-topspin-forehand-drive (상회전 전진 드라이브 회전 거는 요령)
# lesson-receive-short-serve (짧은 서브에 대한 리시브 대처법)
# lesson-footwork-two-step (탁구 기본 좌우 2스텝 풋워크)
# lesson-smash-high-ball (찬스볼 높은 공 스매시 타격 타이밍)
# lesson-flick-banana-chiquita (치키타 및 백핸드 플릭 기술 원리)
# lesson-block-power-drive (상대의 강한 파워 드라이브 블록 차단 요령)

g3 = [
    # Existing
    ('drive-long', '배우기·기술 레슨', '드라이브 공이 자꾸 테이블 밖으로 나가는 이유는?', '배우기', 'live', 'P0', 'content/questions/drive-long.json', '2026-08-20', '001', '2026-08-20', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/drive-long.html'),
    ('drive-net', '배우기·기술 레슨', '커트볼 드라이브가 네트에 걸리는 이유는?', '배우기', 'live', 'P0', 'content/questions/drive-net.json', '2026-08-20', '002', '2026-08-20', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/drive-net.html'),
    # Planned
    ('lesson-forehand-stroke-posture', '배우기·기술 레슨', '포핸드 롱 기본 스트로크의 올바른 폼과 체중 이동 방법은?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '047', '', ''),
    ('lesson-backhand-short-timing', '배우기·기술 레슨', '백핸드 쇼트에서 공이 뜨지 않고 깔끔하게 들어가는 타점은?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '048', '', ''),
    ('lesson-backspin-push-technique', '배우기·기술 레슨', '하회전 볼을 안전하게 깎아 넘기는 보스커트(푸시) 요령은?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '049', '', ''),
    ('lesson-under-spin-serve-basics', '배우기·기술 레슨', '탁구 서브에서 강한 하회전(백스핀)을 넣는 손목 스냅 원리는?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '050', '', ''),
    ('lesson-topspin-forehand-drive', '배우기·기술 레슨', '포핸드 드라이브 시 공을 두텁게 긁어 스핀을 높이는 방법은?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '051', '', ''),
    ('lesson-receive-short-serve', '배우기·기술 레슨', '네트 앞 짧게 떨어지는 상대 서브에 대처하는 리시브 위치는?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '052', '', ''),
    ('lesson-footwork-two-step', '배우기·기술 레슨', '좌우 왕복 드라이브 연습을 위한 2스텝 기본 풋워크 요령은?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '053', '', ''),
    ('lesson-smash-high-ball', '배우기·기술 레슨', '네트 위로 높이 뜬 찬스볼을 실수 없이 때리는 스매시 자세는?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '054', '', ''),
    ('lesson-flick-banana-chiquita', '배우기·기술 레슨', '현대 탁구 필수 리시브 기술 치키타의 회전 원리와 연습 순서는?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '055', '', ''),
    ('lesson-block-power-drive', '배우기·기술 레슨', '상대방의 강한 회전 드라이브를 라켓 각도로 흡수하는 블록법은?', '배우기', 'planned', 'P2', 'app_features.json (배우기)', '2026-09-01', '056', '', ''),
]
assert len(g3) == 12

# Group 4: 전국 탁구대회 (15 items)
# Existing (2):
# tournament-check (live)
# tournament-registration-guide (hold)

# New planned (13):
# tournament-division-system-t1-t7 (디비전 리그 T1~T7 구분)
# tournament-amateur-handicap-rule (동호인 핸디 경기 규정)
# tournament-official-ball-selection (대회 공인구 3성구 규격 확인)
# tournament-ittf-authorized-rubber (대회 참가 가능 ITTF 공인 러버 확인)
# tournament-singles-vs-team-match (개인단식과 단체전 경기 진행 방식)
# tournament-dress-code-regulations (탁구대회 복장 유니폼 규정)
# tournament-first-entry-tips (동호인 첫 대회 출전 시 준비물 및 체크리스트)
# tournament-warmup-routine (대회 당일 테이블 적응 및 15분 웜업 루틴)
# tournament-protest-umpire-rule (심판 판정 및 네트/에지 항의 규정)
# tournament-bracket-seeding-rules (조별 예선 리그와 토너먼트 대진표 추첨 방식)
# tournament-consolation-matches (하위부 패자부활전 하위리그 진행 규정)
# tournament-time-out-card-rule (생활체육 탁구대회 타임아웃 규정)
# tournament-local-vs-national-rating (지역 부수와 전국 오픈 부수 출전 자격)

g4 = [
    # Existing
    ('tournament-check', '전국 탁구대회', '전국 탁구대회 일정은 어디에서 확인하나요?', '경기일정', 'live', 'P0', 'content/questions/tournament-check.json', '2026-08-20', '006', '2026-08-20', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/tournament-check.html'),
    ('tournament-registration-guide', '전국 탁구대회', '생활체육 탁구대회 참가 신청 시 확인할 핵심 사항은 무엇인가요?', '경기일정', 'hold', 'P1', 'questions/tournament-registration-guide.json', '2026-08-25', '016', '', ''),
    # Planned
    ('tournament-division-system-t1-t7', '전국 탁구대회', '대한탁구협회 디비전 리그 T1~T7 리그 등급 체계와 승강제 방식은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '057', '', ''),
    ('tournament-amateur-handicap-rule', '전국 탁구대회', '생활체육 탁구대회 부수별 핸디 점수(1+1+1 점수차) 계산 기준은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '058', '', ''),
    ('tournament-official-ball-selection', '전국 탁구대회', '대회 공인구(ABS 40+ 3스타 공인구) 종류와 제조사별 반발력 차이는?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '059', '', ''),
    ('tournament-ittf-authorized-rubber', '전국 탁구대회', '생활체육 전국 오픈대회에서 사용 가능한 ITTF 공인 러버 확인법은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '060', '', ''),
    ('tournament-singles-vs-team-match', '전국 탁구대회', '탁구 단체전 경기 진행 순서(단-단-복-단-단)와 오더지 제출 요령은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '061', '', ''),
    ('tournament-dress-code-regulations', '전국 탁구대회', '탁구대회 시합 유니폼 상하의 색상 규정(흰색 상의 착용 금지)은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '062', '', ''),
    ('tournament-first-entry-tips', '전국 탁구대회', '탁구 동호인 첫 시합 출전 시 반드시 챙겨야 할 필수 준비물은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '063', '', ''),
    ('tournament-warmup-routine', '전국 탁구대회', '시합 시작 전 2분 연습시간을 효과적으로 활용하는 웜업 순서는?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '064', '', ''),
    ('tournament-protest-umpire-rule', '전국 탁구대회', '경기 중 에지볼·네트 판정 및 심판 판정 시 공식 이의제기 절차는?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '065', '', ''),
    ('tournament-bracket-seeding-rules', '전국 탁구대회', '탁구대회 조별 예선 리그 동률 시 세트 득실 계산 및 본선 추첨법은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '066', '', ''),
    ('tournament-consolation-matches', '전국 탁구대회', '생활체육 탁구대회 패자부활전(하위부 리그) 진행 규칙과 출전 자격은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '067', '', ''),
    ('tournament-time-out-card-rule', '전국 탁구대회', '시합 중 타임아웃 요청 규정(게임당 1회 1분)과 옐로카드 기준은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '068', '', ''),
    ('tournament-local-vs-national-rating', '전국 탁구대회', '지역 협회 등록 부수와 전국 오픈대회 참가 부수의 차이점은?', '경기일정', 'planned', 'P2', 'app_features.json (경기일정)', '2026-09-01', '069', '', ''),
]
assert len(g4) == 15

# Group 5: 라지볼 (12 items)
# Existing (2):
# largeball-difference (hold)
# largeball-rubber (hold)

# New planned (10):
# largeball-ball-size-weight (44mm 라지볼 공 규격과 무게)
# largeball-net-height (라지볼 네트 높이 17.25cm 규정)
# largeball-service-rotation-rule (라지볼 서브 회전 및 노터치 규칙)
# largeball-racket-blade-selection (라지볼 전용 라켓 블레이드 특징)
# largeball-pimples-out-rubber-types (라지볼 전용 숏핌플 러버 돌기 규격)
# largeball-scoring-rules (라지볼 13점제 듀스 및 세트 규정)
# largeball-senior-division-classes (라지볼 연령별 참가 부수 구분)
# largeball-gameplay-tactics (라지볼 랠리 연결과 롱랠리 전술)
# largeball-health-benefits-seniors (시니어 건강증진을 위한 라지볼 운동 효과)
# largeball-national-tournaments (전국 라지볼 탁구 페스티벌 및 대회 일정 확인)

g5 = [
    # Existing
    ('largeball-difference', '라지볼', '라지볼과 일반 탁구는 무엇이 다른가요?', 'AI 장비추천', 'hold', 'P1', 'questions/largeball-difference.json', '2026-08-20', '017', '', ''),
    ('largeball-rubber', '라지볼', '라지볼 경기에서 어떤 러버를 사용해야 하나요?', 'AI 장비추천', 'hold', 'P1', 'questions/largeball-rubber.json', '2026-08-20', '018', '', ''),
    # Planned
    ('largeball-ball-size-weight', '라지볼', '라지볼 공 규격(지름 44mm, 무게 2.2~2.4g)과 주황색 사용 이유는?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '070', '', ''),
    ('largeball-net-height', '라지볼', '라지볼 경기 규정에서 일반 탁구보다 높은 네트(17.25cm)의 영향은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '071', '', ''),
    ('largeball-service-rotation-rule', '라지볼', '라지볼 서브 시 강한 회전 제한 규정과 엔드라인 서비스 원칙은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '072', '', ''),
    ('largeball-racket-blade-selection', '라지볼', '라지볼에서 가벼운 반발력을 얻기 위한 전용 블레이드 추천 기준은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '073', '', ''),
    ('largeball-pimples-out-rubber-types', '라지볼', '라지볼 전용 공인 러버(표면 돌기 숏핌플)의 종류와 선택 방법은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '074', '', ''),
    ('largeball-scoring-rules', '라지볼', '라지볼 대회의 13점 게임 규정과 듀스 시 최대 15점 마감 규칙은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '075', '', ''),
    ('largeball-senior-division-classes', '라지볼', '전국 라지볼 탁구대회의 연령대별 부수(60대·70대·80대) 참가 기준은?', '경기일정', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '076', '', ''),
    ('largeball-gameplay-tactics', '라지볼', '라지볼 경기에서 스매시보다 랠리 안정성과 코스 배분이 중요한 이유는?', '배우기', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '077', '', ''),
    ('largeball-health-benefits-seniors', '라지볼', '시니어와 어르신들의 관절 부담을 줄여주는 라지볼 유산소 운동 효과는?', '맞춤진단', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '078', '', ''),
    ('largeball-national-tournaments', '라지볼', '대한탁구협회 공인 전국 라지볼 페스티벌 일정과 대회 접수처는?', '경기일정', 'planned', 'P2', 'app_features.json (라지볼)', '2026-09-01', '079', '', ''),
]
assert len(g5) == 12

# Group 6: 장애인 탁구 (10 items)
# Existing (1):
# para-classes (live)

# New planned (9):
# para-wheelchair-rules-class1-5 (휠체어 탁구 클래스 1~5 경기 규정)
# para-standing-rules-class6-10 (스탠딩 지체장애 탁구 클래스 6~10 특성)
# para-intellectual-class11 (지적장애 탁구 클래스 11 규정)
# para-wheelchair-service-net-rule (휠체어 탁구 서브 렛 판정 및 사이드라인 규정)
# para-table-specs-wheelchair (휠체어 선수를 위한 탁구대 다리 간격 규격)
# para-racket-strapping-rules (손 기능 장애 선수를 위한 라켓 붕대 고정 규정)
# para-paralympic-qualification (패럴림픽 및 장애인 아시안게임 탁구 출전권 획득 방식)
# para-national-tournaments-korea (국내 대한장애인탁구협회 주관 전국대회 일정 확인)
# para-classification-process (장애인 탁구 공식 등급분류 심사 절차)

g6 = [
    # Existing
    ('para-classes', '장애인 탁구', '장애인 탁구의 클래스 1~11은 무슨 뜻인가요?', '경기일정', 'live', 'P0', 'content/questions/para-classes.json', '2026-08-20', '004', '2026-08-20', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/para-classes.html'),
    # Planned
    ('para-wheelchair-rules-class1-5', '장애인 탁구', '휠체어 탁구(클래스 1~5) 선수의 시합 특성과 경기 진행 규칙은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '080', '', ''),
    ('para-standing-rules-class6-10', '장애인 탁구', '스탠딩 지체장애(클래스 6~10) 선수의 경기 방식과 신체 기능 기준은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '081', '', ''),
    ('para-intellectual-class11', '장애인 탁구', '지적장애 탁구 선수들이 출전하는 클래스 11의 경기 규정은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '082', '', ''),
    ('para-wheelchair-service-net-rule', '장애인 탁구', '휠체어 탁구 서브에서 공이 네트 맞고 넘어가거나 옆으로 나갈 때 규칙은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '083', '', ''),
    ('para-table-specs-wheelchair', '장애인 탁구', '휠체어 선수의 접근을 돕는 공인 탁구대 엔드라인 다리 규격은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '084', '', ''),
    ('para-racket-strapping-rules', '장애인 탁구', '손 기능 장애 선수를 위해 라켓을 손에 밴드로 고정하는 공식 규정은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '085', '', ''),
    ('para-paralympic-qualification', '장애인 탁구', '패럴림픽 및 국제 장애인 탁구 대회 출전 랭킹 포인트 획득 방식은?', '랭킹', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '086', '', ''),
    ('para-national-tournaments-korea', '장애인 탁구', '대한장애인탁구협회 공식 국내 대회 및 전국장애인체전 일정 확인법은?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '087', '', ''),
    ('para-classification-process', '장애인 탁구', '장애인 탁구 선수가 시합에 나가기 위해 받는 등급분류(선수등록) 심사는?', '경기일정', 'planned', 'P2', 'app_features.json (장애인 탁구)', '2026-09-01', '088', '', ''),
]
assert len(g6) == 10

# Group 7: 국내·세계 랭킹 (12 items)
# Existing (2):
# domestic-division-ranking (hold)
# world-ranking-system (hold)

# New planned (10):
# ranking-ittf-point-validity-period (세계 랭킹 유효기간 12개월 반영)
# ranking-wtt-tournament-tier-points (WTT 그랜드스매시·챔피언스·컨텐더 배점)
# ranking-olympic-seed-criteria (올림픽 및 세계선수권 시드 배정 기준)
# ranking-ktta-national-squad-selection (대한탁구협회 국가대표 선발 포인트)
# ranking-division-t3-t4-promotion (생활체육 디비전 리그 승급 포인트 계산)
# ranking-app-realtime-lookup (상상탁구 AI 앱에서 국내외 랭킹 확인하는 법)
# ranking-youth-u19-u15-system (WTT 유스 시리즈 청소년 랭킹 산정 방식)
# ranking-mixed-doubles-world (혼합복식 세계 랭킹 산정 규정과 페어 포인트)
# ranking-penalty-zero-point (WTT 대회 기권 및 불참 시 페널티 포인트 규정)
# ranking-amateur-club-bu-system (전국 탁구 동호인 오픈 부수와 승급 기준)

g7 = [
    # Existing
    ('domestic-division-ranking', '국내·세계 랭킹', '대한탁구협회 디비전 리그 랭킹과 동호인 부수 체계는 어떻게 되나요?', '랭킹', 'hold', 'P1', 'questions/domestic-division-ranking.json', '2026-08-20', '019', '', ''),
    ('world-ranking-system', '국내·세계 랭킹', '세계 탁구 랭킹(ITTF/WTT)은 어떻게 산정되나요?', '랭킹', 'hold', 'P1', 'questions/world-ranking-system.json', '2026-08-20', '020', '', ''),
    # Planned
    ('ranking-ittf-point-validity-period', '국내·세계 랭킹', 'ITTF 세계 랭킹 포인트의 유효기간(12개월)과 성적 반영 규정은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '089', '', ''),
    ('ranking-wtt-tournament-tier-points', '국내·세계 랭킹', 'WTT 그랜드스매시·챔피언스·컨텐더 등급별 우승 랭킹 포인트 비교는?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '090', '', ''),
    ('ranking-olympic-seed-criteria', '국내·세계 랭킹', '올림픽 탁구 단식 및 단체전 시드 배정에 반영되는 세계 랭킹 기준은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '091', '', ''),
    ('ranking-ktta-national-squad-selection', '국내·세계 랭킹', '대한탁구협회 국가대표 최종 선발전 출전 자격과 랭킹 배점은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '092', '', ''),
    ('ranking-division-t3-t4-promotion', '국내·세계 랭킹', '전국 디비전 리그(T4/T5/T6) 팀 승강 및 개인 랭킹 포인트 계산법은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '093', '', ''),
    ('ranking-app-realtime-lookup', '국내·세계 랭킹', '상상탁구 AI 앱의 랭킹 메뉴에서 주요 선수 순위를 조회하는 방법은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '094', '', ''),
    ('ranking-youth-u19-u15-system', '국내·세계 랭킹', 'WTT 유스 컨텐더 청소년(U19/U15) 랭킹 포인트 산정 규칙은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '095', '', ''),
    ('ranking-mixed-doubles-world', '국내·세계 랭킹', '혼합복식 세계 랭킹 산정 시 개인 포인트와 페어 랭킹의 연계 방식은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '096', '', ''),
    ('ranking-penalty-zero-point', '국내·세계 랭킹', 'WTT 상위 대회 불참 시 부여되는 0점 페널티와 랭킹 하락 규정은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '097', '', ''),
    ('ranking-amateur-club-bu-system', '국내·세계 랭킹', '전국 동호인 탁구 부수(1부~7부) 승급 기준과 포인트 누적 방식은?', '랭킹', 'planned', 'P2', 'app_features.json (랭킹)', '2026-09-01', '098', '', ''),
]
assert len(g7) == 12

# Group 8: 탁구장·맞춤진단·앱 활용 (14 items)
# Existing (2):
# find-club (live)
# diagnosis-playstyle (hold)

# New planned (12):
# club-facilities-shower-parking (탁구장 시설 편의시설 주차장 확인법)
# club-etiquette-rules (탁구장 이용 기본 매너와 에티켓)
# club-floor-mat-table-brand (탁구대 브랜드 및 마룻바닥 바닥재 중요성)
# club-machine-robot-practice (탁구 로봇 머신 연습 효과와 활용 팁)
# club-lesson-monthly-fee-guide (탁구장 월 레슨비 및 회원제 이용 요금 기준)
# diagnosis-rubber-combination-test (맞춤진단: 내 타구 습관에 맞는 러버 조합 테스트)
# diagnosis-shake-vs-penholder (맞춤진단: 셰이크핸드와 중펜 중 나에게 맞는 그립은?)
# diagnosis-grip-power-control (맞춤진단: 파워 공격형 vs 안정 컨트롤형 성향 진단)
# diagnosis-footwork-stamina (맞춤진단: 동호인 풋워크 이동 반경 및 체력 상태 체크)
# app-feature-star-gear-hub (상상탁구 AI 스타플레이어 장비관 활용법)
# app-feature-qr-download (스마트폰 카메라로 상상탁구 AI 공식 앱 설치하는 법)
# app-feature-equipment-search (상상탁구 AI 앱에서 내 예산 맞춤 라켓 검색하기)

g8 = [
    # Existing
    ('find-club', '탁구장·맞춤진단·앱 활용', '가까운 탁구장은 어떻게 찾나요?', '탁구장', 'live', 'P0', 'content/questions/find-club.json', '2026-08-20', '003', '2026-08-20', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/find-club.html'),
    ('diagnosis-playstyle', '탁구장·맞춤진단·앱 활용', '탁구 초보자에게 맞는 플레이 스타일과 전형은 어떻게 찾나요?', '맞춤진단', 'hold', 'P1', 'questions/diagnosis-playstyle.json', '2026-08-20', '021', '', ''),
    # Planned
    ('club-facilities-shower-parking', '탁구장·맞춤진단·앱 활용', '내 주변 탁구장 찾을 때 샤워실·주차장·탁구대 수 확인하는 팁은?', '탁구장', 'planned', 'P2', 'app_features.json (탁구장)', '2026-09-01', '099', '', ''),
    ('club-etiquette-rules', '탁구장·맞춤진단·앱 활용', '탁구장 일일 입장 시 지켜야 할 기본 에티켓과 전용 탁구화 착용 규정은?', '탁구장', 'planned', 'P2', 'app_features.json (탁구장)', '2026-09-01', '100', '', ''),
    ('club-floor-mat-table-brand', '탁구장·맞춤진단·앱 활용', '탁구장 바닥 탄성 마루와 국제 공인 탁구대(참피온/버터플라이) 차이점은?', '탁구장', 'planned', 'P2', 'app_features.json (탁구장)', '2026-09-01', '101', '', ''),
    ('club-machine-robot-practice', '탁구장·맞춤진단·앱 활용', '혼자 탁구 연습할 때 탁구 로봇 머신기 활용법과 반복 훈련 효과는?', '배우기', 'planned', 'P2', 'app_features.json (탁구장)', '2026-09-01', '102', '', ''),
    ('club-lesson-monthly-fee-guide', '탁구장·맞춤진단·앱 활용', '일반 탁구장 월 회비와 1:1 개인 레슨비 평균 시세 및 선택 기준은?', '탁구장', 'planned', 'P2', 'app_features.json (탁구장)', '2026-09-01', '103', '', ''),
    ('diagnosis-rubber-combination-test', '탁구장·맞춤진단·앱 활용', '상상탁구 AI 맞춤진단으로 내 스윙 궤적에 맞는 러버를 진단하는 원리는?', '맞춤진단', 'planned', 'P2', 'app_features.json (맞춤진단)', '2026-09-01', '104', '', ''),
    ('diagnosis-shake-vs-penholder', '탁구장·맞춤진단·앱 활용', '입문자를 위한 맞춤진단: 셰이크핸드와 중국식 펜홀더(중펜) 선택 기준은?', '맞춤진단', 'planned', 'P2', 'app_features.json (맞춤진단)', '2026-09-01', '105', '', ''),
    ('diagnosis-grip-power-control', '탁구장·맞춤진단·앱 활용', '플레이 스타일에 따른 성향 진단: 스피드 파워 공격형 vs 회전 컨트롤형은?', '맞춤진단', 'planned', 'P2', 'app_features.json (맞춤진단)', '2026-09-01', '106', '', ''),
    ('diagnosis-footwork-stamina', '탁구장·맞춤진단·앱 활용', '동호인 경기 체력과 움직임 범위를 자가 진단하는 맞춤 팁은?', '맞춤진단', 'planned', 'P2', 'app_features.json (맞춤진단)', '2026-09-01', '107', '', ''),
    ('app-feature-star-gear-hub', '탁구장·맞춤진단·앱 활용', '상상탁구 AI 스타플레이어 장비관에서 국내외 선수별 장비를 비교하는 법은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (홈)', '2026-09-01', '108', '', ''),
    ('app-feature-qr-download', '탁구장·맞춤진단·앱 활용', '상상탁구 AI 공식 앱을 스마트폰 카메라 QR 코드로 간편 설치하는 방법은?', '홈', 'planned', 'P2', 'config.json (스토어 링크)', '2026-09-01', '109', '', ''),
    ('app-feature-equipment-search', '탁구장·맞춤진단·앱 활용', '상상탁구 AI 앱의 맞춤 장비 검색 기능으로 내 예산별 라켓 찾는 법은?', 'AI 장비추천', 'planned', 'P2', 'app_features.json (AI 장비추천)', '2026-09-01', '110', '', ''),
]
assert len(g8) == 14

all_rows = g1 + g2 + g3 + g4 + g5 + g6 + g7 + g8
assert len(all_rows) == 110

# Header fields:
# content_id,category,question_title,app_menu,slug,content_status,priority,source_data,verified_date,publish_order,published_date,published_url

csv_path = Path('content_plan_110.csv')
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'content_id',
        'category',
        'question_title',
        'app_menu',
        'slug',
        'content_status',
        'priority',
        'source_data',
        'verified_date',
        'publish_order',
        'published_date',
        'published_url'
    ])
    
    seen_slugs = set()
    seen_titles = set()
    live_count = 0
    hold_count = 0
    planned_count = 0

    for idx, r in enumerate(all_rows, start=1):
        slug, category, title, app_menu, status, priority, source, vdate, porder, pubdate, puburl = r
        cid = f'C{idx:03d}'
        assert slug not in seen_slugs, f'Duplicate slug: {slug}'
        seen_slugs.add(slug)
        assert title not in seen_titles, f'Duplicate title: {title}'
        seen_titles.add(title)
        
        if status == 'live': live_count += 1
        elif status == 'hold': hold_count += 1
        elif status == 'planned': planned_count += 1
        
        writer.writerow([
            cid, category, title, app_menu, slug, status, priority, source, vdate, porder, pubdate, puburl
        ])

print(f'Successfully generated {csv_path.name}')
print(f'Total rows: {len(all_rows)}')
print(f'Live: {live_count}, Hold: {hold_count}, Planned: {planned_count}')
print(f'Existing 21 covered: {all(k in seen_slugs for k in existing)}')
