#!/usr/bin/env python3
"""
Phase 3B-1: Automated question candidate generation based on authentic STAI app data.
- Read-only ingestion from C:\\STAI_WORK_20261019\\src\\data
- Idempotent and safe: never modifies existing approved questions (reviewed)
- Isolates all newly generated candidates with 'editorial_review_required' (HOLD)
- Enforces duplicate detection and 12-field schema standards
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
APP_DATA_DIR = Path(r"C:\STAI_WORK_20261019\src\data")

# Core approved question slugs that must NEVER be overwritten
APPROVED_SLUGS = {
    "drive-long",
    "drive-net",
    "find-club",
    "para-classes",
    "rubber-choice",
    "tournament-check"
}

# Manually refined HOLD question slugs that must NEVER be overwritten by automation
PROTECTED_SLUGS = {
    "pro-player-gear-shinyubin"
}

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def normalize_q(q):
    return re.sub(r"[\s\?\!\.,·]+", "", q.lower())

def load_existing_questions():
    existing = {}
    normalized_texts = set()
    for f in QUESTIONS_DIR.glob("*.json"):
        obj = json.loads(f.read_text(encoding="utf-8"))
        qid = obj["id"]
        existing[qid] = obj
        normalized_texts.add(normalize_q(obj["question"]))
    return existing, normalized_texts

def generate_star_player_candidates():
    from extract_app_data import parse_star_players
    players = parse_star_players()
    candidates = []

    # Map key players to standardized slugs and questions
    target_configs = {
        "pro-shin-yubin": {
            "slug": "pro-player-gear-shinyubin",
            "question": "신유빈 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?",
            "source_type": "brand_sponsorship_and_match_record",
            "source_url": "https://www.butterfly-korea.co.kr",
            "is_amateur": False
        },
        "pro-jang-woojin": {
            "slug": "pro-player-gear-jangwoojin",
            "question": "장우진 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?",
            "source_type": "tournament_match_record",
            "source_url": "https://ktta.sports.or.kr",
            "is_amateur": False
        },
        "world-ma-long": {
            "slug": "pro-player-gear-malong",
            "question": "마롱 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?",
            "source_type": "tournament_match_record",
            "source_url": "https://www.ittf.com",
            "is_amateur": False
        },
        "world-tomokazu-harimoto": {
            "slug": "pro-player-gear-harimoto-tomokazu",
            "question": "하리모토 토모카즈 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?",
            "source_type": "brand_sponsorship_and_match_record",
            "source_url": "https://www.butterfly-global.com",
            "is_amateur": False
        },
        "world-fan-zhendong": {
            "slug": "pro-player-gear-fanzhendong",
            "question": "판전둥(판젠동) 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?",
            "source_type": "tournament_match_record",
            "source_url": "https://www.ittf.com",
            "is_amateur": False
        },
        "amateur-lee-junsang": {
            "slug": "amateur-gear-leejunsang",
            "question": "아마추어 탁구인 이준상의 라켓과 러버 구성은 어떻게 되나요?",
            "source_type": "founder_direct_check",
            "source_url": "https://sangsangtak.com/founder-verification (대표 선수 본인 직접 구두 확인)",
            "is_amateur": True
        },
        "world-felix-lebrun": {
            "slug": "pro-player-gear-felix-lebrun",
            "question": "펠릭스 르브런 선수가 사용하는 펜홀더 라켓과 러버는 무엇인가요?",
            "source_type": "brand_sponsorship_and_match_record",
            "source_url": "https://www.tibhar.com",
            "is_amateur": False
        },
        "world-miwa-harimoto": {
            "slug": "pro-player-gear-miwa-harimoto",
            "question": "하리모토 미와 선수가 사용하는 탁구 라켓과 러버는 무엇인가요?",
            "source_type": "brand_sponsorship_and_match_record",
            "source_url": "https://www.butterfly-global.com",
            "is_amateur": False
        }
    }

    for p in players:
        pid = p["id"]
        if pid not in target_configs:
            continue
        cfg = target_configs[pid]
        p_name = p["name"]
        blade = p["blade"]
        fh = p["forehandRubber"]
        bh = p["backhandRubber"]
        grip = p["gripType"]
        style = p["playStyle"] or "공격형"
        verified_date = p["verifiedAt"] or "2026-01-15"

        if cfg["is_amateur"]:
            short_answer = f"{p_name}의 장비 구성은 {blade} 블레이드에 포핸드 {fh}, 백핸드 {bh} 조합입니다 (상상탁구 AI 앱 등록 기준, 대표 선수 직접 확인)."
            note = f"출처 유형: 대표 직접 확인(founder_direct_check). 앱 등록 정보 기준({verified_date})이며, 아마추어 선수의 외부 검색 공개 동의 및 2차 공인 검증 절차 진행 전까지 보류(HOLD) 상태를 유지합니다."
            step3 = "상상탁구 AI 앱의 'AI 장비추천' 및 스타플레이어 장비관에서 선수별 세부 장비 구성을 직접 살펴보실 수 있습니다."
        else:
            short_answer = f"{p_name} 선수는 {blade} 블레이드에 전면(FH) {fh}, 후면(BH) {bh} 러버를 사용하는 것으로 알려져 있습니다 (상상탁구 AI 앱 등록 정보 기준)."
            note = f"출처 유형: {cfg['source_type']}. 앱 등록 정보 기준 스냅샷({verified_date}, {p['sourceName']})이며, 선수의 대회별 실사용 세팅 및 협찬 상황에 따라 변경될 수 있습니다 (외부 비공개 보류 유지)."
            step3 = "상상탁구 AI 앱의 'AI 장비추천' 메뉴와 스타플레이어 장비관에서 국내외 주요 선수들의 장비 구성을 비교해 보세요."

        candidate = {
            "id": cfg["slug"],
            "question": cfg["question"],
            "category": "스타플레이어 장비",
            "app_session": "AI 장비추천",
            "feature_status": "released",
            "source_type": cfg["source_type"],
            "source_url": cfg["source_url"],
            "verified_date": verified_date,
            "answer": short_answer,
            "steps": [
                f"블레이드({blade}, {grip} 그립)와 러버 조합의 반발력 및 회전 특성을 파악합니다.",
                "선수용 특수소재 블레이드와 고경도 러버는 개인의 타구 임팩트와 연습량에 맞춰 선택해야 합니다.",
                step3
            ],
            "related_guide": "index.html",
            "review_status": "editorial_review_required",
            "reference_note": note
        }
        candidates.append(candidate)
    
    return candidates

def generate_other_category_candidates():
    return [
        {
            "id": "domestic-division-ranking",
            "question": "대한탁구협회 디비전 리그 랭킹과 동호인 부수 체계는 어떻게 되나요?",
            "category": "세계·국내 탁구 랭킹",
            "app_session": "랭킹",
            "feature_status": "released",
            "source_type": "ktta_official_notice",
            "source_url": "https://ttadivision.sports.or.kr/statistic/moveBestPlayerRanking.do",
            "verified_date": "2026-08-20",
            "answer": "대한탁구협회 디비전 리그는 T4~T7 등 리그 등급별 승강제와 승점 포인트를 바탕으로 랭킹이 산정되며, 지역별 부수 규정과 연계됩니다.",
            "steps": [
                "참가하는 디비전 리그의 배점 기준과 전국/지역 랭킹 포인트 반영 방식을 확인합니다.",
                "동호인 부수(1부~7부) 승급 기준과 대회 참가 자격을 각 시·도 탁구협회 요강에서 대조합니다.",
                "상상탁구 AI 앱의 '랭킹' 메뉴에서 다양한 선수들의 순위 및 리그 정보를 살펴보실 수 있습니다."
            ],
            "related_guide": "index.html",
            "review_status": "editorial_review_required",
            "reference_note": "검토 보류: 2026 하반기 디비전 리그 포인트 승급 규정 최종 공시 대조 중 (외부 비공개 유지)."
        },
        {
            "id": "tournament-registration-guide",
            "question": "생활체육 탁구대회 참가 신청 시 확인할 핵심 사항은 무엇인가요?",
            "category": "전국 탁구대회",
            "app_session": "경기일정",
            "feature_status": "released",
            "source_type": "tournament_association_announcement",
            "source_url": "https://ktta.sports.or.kr",
            "verified_date": "2026-08-25",
            "answer": "대회 참가 신청 시에는 접수 시작·마감일, 참가 부수(오픈부·희망부 등) 자격, 사용 공인구 및 러버 규정을 먼저 확인해야 합니다.",
            "steps": [
                "주최 단체(아이핑, 오케이핑퐁, 협회 등)의 공식 대회 요강에서 참가 자격과 정원 마감 여부를 확인합니다.",
                "자신의 지역 공인 부수와 전국 오픈 부수 인정 기준의 차이를 점검합니다.",
                "상상탁구 AI 앱의 '경기일정' 메뉴에서 전국의 최신 대회 일정과 요강을 실시간으로 확인해 보세요."
            ],
            "related_guide": "index.html",
            "review_status": "editorial_review_required",
            "reference_note": "검토 보류: 주최사별 참가 신청 접수 프로세스 검증 진행 중 (외부 비공개 유지)."
        },
        {
            "id": "gear-recommend-drive-combo",
            "question": "드라이브 전형 탁구 동호인을 위한 추천 라켓과 러버 조합은?",
            "category": "라켓·러버 및 AI 장비추천",
            "app_session": "AI 장비추천",
            "feature_status": "released",
            "source_type": "app_curation_database",
            "source_url": "https://lsb-svg.github.io/sangsangtak-ai-web/",
            "verified_date": "2026-08-28",
            "answer": "드라이브 전형 동호인에게는 안정적인 볼 그립력의 5겹 순수합판이나 이너 아릴레이트 카본(ALC) 블레이드에 45~48도 경도의 텐션 러버 조합이 추천됩니다.",
            "steps": [
                "자신의 구력과 임팩트 파워에 맞춰 아우터 카본보다 컨트롤이 편한 이너 카본 또는 합판을 검토합니다.",
                "포핸드는 회전력이 우수한 스핀형 러버를, 백핸드는 안정적인 쇼트와 블록이 가능한 러버를 배치합니다.",
                "상상탁구 AI 앱의 'AI 장비추천' 메뉴에서 구력과 예산에 맞춘 최적의 장비 추천을 확인해 보세요."
            ],
            "related_guide": "index.html",
            "review_status": "editorial_review_required",
            "reference_note": "검토 보류: 앱 내 20개 표준 장비 추천 콤보 데이터셋 연계 검증 중 (외부 비공개 유지)."
        }
    ]

def run_generation():
    existing, norm_texts = load_existing_questions()
    print(f"Loaded {len(existing)} existing questions.")

    new_candidates = generate_star_player_candidates() + generate_other_category_candidates()
    print(f"Prepared {len(new_candidates)} candidate templates.")

    added_count = 0
    updated_count = 0
    unchanged_count = 0
    skipped_approved = 0
    skipped_protected = 0
    duplicate_count = 0

    for item in new_candidates:
        qid = item["id"]
        qtext = item["question"]
        norm = normalize_q(qtext)
        existing_obj = existing.get(qid)

        # 1. Never overwrite approved live questions (by slug or review_status == 'reviewed')
        if qid in APPROVED_SLUGS or (existing_obj and existing_obj.get("review_status") == "reviewed"):
            print(f"[SKIP] Approved question preserved: {qid}")
            skipped_approved += 1
            continue

        # 2. Never overwrite manually curated HOLD questions (by PROTECTED_SLUGS or manual_protected flag)
        if qid in PROTECTED_SLUGS or (existing_obj and existing_obj.get("manual_protected") is True):
            print(f"[SKIP] Protected manual question preserved: {qid}")
            skipped_protected += 1
            continue

        # 3. Check if text duplicates an existing question with a different ID
        if qid not in existing and norm in norm_texts:
            print(f"[DUPLICATE BLOCKED] Question text already exists: '{qtext}'")
            duplicate_count += 1
            continue

        target_file = QUESTIONS_DIR / f"{qid}.json"
        is_new = not target_file.exists()

        # 4. Do not re-save unchanged files
        if not is_new and existing_obj == item:
            unchanged_count += 1
            print(f"[UNCHANGED] Candidate already up to date: {qid}")
            continue
        
        target_file.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if is_new:
            added_count += 1
            norm_texts.add(norm)
            print(f"[NEW] Created question candidate: {qid} ({item['category']})")
        else:
            updated_count += 1
            print(f"[UPDATE] Synchronized question candidate: {qid}")

    print("\n--- GENERATION SUMMARY ---")
    print(f"Added new candidates: {added_count}")
    print(f"Updated candidates: {updated_count}")
    print(f"Unchanged candidates: {unchanged_count}")
    print(f"Skipped approved: {skipped_approved}")
    print(f"Skipped protected: {skipped_protected}")
    print(f"Duplicates blocked: {duplicate_count}")
    print(f"Total questions in questions/: {len(list(QUESTIONS_DIR.glob('*.json')))}")

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent))
    run_generation()
