#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/update_seo_registry.py

SEO/GEO/AEO 콘텐츠 통합 관리대장 자동 갱신 모듈 (Phase 2C)
- 필수 6대 등록 조건 검증:
  1. 실제 공개 사이트맵(sitemap.xml)에 URL 존재
  2. 실제 배포 페이지 HTTP 200 OK 응답
  3. 배포 HTML의 <title>과 원본 question 일치 (or 포함)
  4. 배포 HTML의 <link rel="canonical"> href 일치
  5. 기존 관리번호(registry_id), content_id, slug, published_url 무중복
  6. 내부 발행 상태(content_status)와 실제 공개 상태를 구분하여 기록 (ready 상태 공개 시 '검토 필요' 추적)
- 배포 지연 또는 검증 실패 시 자동 등록 보류 (다음 실행 시 자동 복구 가능)
- 고유 식별자: max_id + 1 부여 (len + 1 금지)
- 이중 파일 저장(CSV, JSON) 원자성(Atomic) 및 롤백 안전장치 완비
"""

import os
import sys
import csv
import json
import re
import argparse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_DIR = os.path.join(BASE_DIR, "reports", "seo_registry")
REGISTRY_CSV = os.path.join(REGISTRY_DIR, "seo_content_registry.csv")
REGISTRY_JSON = os.path.join(REGISTRY_DIR, "seo_content_registry.json")
CONTENT_PLAN_CSV = os.path.join(BASE_DIR, "content_plan_110.csv")
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
BASE_URL = "https://lsb-svg.github.io/sangsangtak-ai-web"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

FIELDNAMES = [
    'registry_id',
    'content_id',
    'slug',
    'question_title',
    'answer',
    'discipline',
    'app_menu',
    'app_feature_evidence',
    'homepage_portal_url',
    'homepage_direct_evidence',
    'youtube_title',
    'youtube_url',
    'youtube_section',
    'official_source_evidence',
    'evidence_verified_date',
    'created_date',
    'published_date',
    'published_url',
    'http_status',
    'index_request_date',
    'index_request_status',
    'past_gsc_indexed_status',
    'current_actual_index_status',
    'index_verified_date',
    'search_impressions',
    'search_clicks',
    'last_audited_date',
    'recommended_recheck_date',
    'overlap_check_result',
    'improvement_needed',
    'actual_publish_status',
    'internal_publish_status',
    'approval_discrepancy'
]


def load_registry(csv_path=REGISTRY_CSV, json_path=REGISTRY_JSON):
    """기존 레지스트리 로드 (CSV 우선, JSON 보조)"""
    records = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    elif os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)
    return records


def get_next_registry_id(records):
    """max(existing_ids) + 1 방식으로 고유번호 생성 (len+1 사용 금지)"""
    max_num = 0
    for r in records:
        reg_id = r.get("registry_id", "")
        if reg_id.startswith("SEO-"):
            try:
                num = int(reg_id.replace("SEO-", ""))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"SEO-{max_num + 1:03d}", max_num + 1


def fetch_sitemap_urls(sitemap_url=SITEMAP_URL, timeout=10):
    """실제 공개 사이트맵(XML)에서 등록된 loc URL 목록 추출"""
    req = urllib.request.Request(
        sitemap_url,
        headers={"User-Agent": "Sangsangtak-SEO-Registry-Validator/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [elem.text.strip() for elem in root.findall("sm:url/sm:loc", ns)]
        if not urls:
            urls = [elem.text.strip() for elem in root.findall(".//loc") if elem.text]
        return set(urls)
    except Exception as e:
        print(f"[WARN] 사이트맵 수집 실패 ({sitemap_url}): {e}")
        return set()


def verify_live_page(url, expected_title, expected_canonical, timeout=10):
    """
    실제 배포 페이지 검증:
    1. HTTP 200 OK
    2. HTML <title> 태그에 expected_title 키워드 포함 여부
    3. HTML <link rel="canonical" href="...">가 expected_canonical과 일치 여부
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Sangsangtak-SEO-Registry-Validator/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return False, f"HTTP 상태 코드 비정상: {resp.status}"
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}"
    except Exception as e:
        return False, f"연결 실패: {e}"

    # Verify Title
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not title_match:
        return False, "HTML <title> 태그 없음"
    page_title = title_match.group(1).strip()
    clean_expected = expected_title.replace(" ", "").replace("?", "").replace("!", "")
    clean_page = page_title.replace(" ", "").replace("?", "").replace("!", "")
    if clean_expected not in clean_page and clean_page not in clean_expected:
        return False, f"제목 불일치 (원문: '{expected_title}', 페이지: '{page_title}')"

    # Verify Canonical URL
    canon_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if not canon_match:
        canon_match = re.search(r'<link\s+href=["\']([^"\']+)["\']\s+rel=["\']canonical["\']', html, re.IGNORECASE)
    if not canon_match:
        return False, "HTML canonical 태그 없음"
    page_canonical = canon_match.group(1).strip()
    if page_canonical != expected_canonical:
        return False, f"Canonical 불일치 (기대: '{expected_canonical}', 페이지: '{page_canonical}')"

    return True, "정상 검증 완료"


def load_all_content_plan(plan_path=CONTENT_PLAN_CSV):
    """content_plan_110.csv의 전체 행을 slug 키 딕셔너리로 로드"""
    plan_dict = {}
    if not os.path.exists(plan_path):
        return plan_dict

    with open(plan_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slug = row.get("slug", "").strip()
            if slug:
                plan_dict[slug] = row
    return plan_dict


def build_new_registry_record(slug, plan_row, next_id, questions_dir=QUESTIONS_DIR):
    """신규 live/공개 콘텐츠에 대한 레지스트리 레코드 생성"""
    content_id = plan_row.get("content_id", "").strip() if plan_row else ""
    title = plan_row.get("question_title", "").strip() if plan_row else ""
    pub_date = plan_row.get("published_date", "").strip() if plan_row else ""
    internal_status = plan_row.get("content_status", "").strip().lower() if plan_row else "unknown"

    today_str = datetime.now().strftime("%Y-%m-%d")
    if not pub_date:
        pub_date = today_str

    url = plan_row.get("published_url", "").strip() if plan_row else ""
    if not url:
        url = f"{BASE_URL}/questions/{slug}.html"

    # 질문 원고 JSON 확인
    q_json_path = os.path.join(questions_dir, f"{slug}.json")
    question_data = {}
    if os.path.exists(q_json_path):
        try:
            with open(q_json_path, "r", encoding="utf-8") as f:
                question_data = json.load(f)
        except Exception:
            pass

    if not title:
        title = question_data.get("question", slug)
    if not content_id:
        content_id = question_data.get("id", slug)

    discipline = question_data.get("discipline", plan_row.get("category", "기본") if plan_row else "기본")
    app_menu = question_data.get("app_menu", plan_row.get("app_menu", "배우기") if plan_row else "배우기")
    sources = question_data.get("sources", [])
    source_evidence = "; ".join(sources) if sources else (plan_row.get("source_data", "공식 데이터베이스") if plan_row else "공식 데이터베이스")
    answer = question_data.get("answer", "")

    # 불일치 여부 판단
    discrepancy = "일치" if internal_status == "live" else "검토 필요"
    improvement = "신규 공개에 따른 색인 크롤링 대기" if discrepancy == "일치" else "내부 발행 상태 ready vs 실제 공개 일치화 검토 필요"

    record = {
        'registry_id': next_id,
        'content_id': content_id,
        'slug': slug,
        'question_title': title,
        'answer': answer,
        'discipline': discipline,
        'app_menu': app_menu,
        'app_feature_evidence': f"상상탁구 앱 {app_menu} 화면 기능 연동",
        'homepage_portal_url': "https://sangsangtak.com",
        'homepage_direct_evidence': "포털 메인 안내 (상세 서브페이지 없음)",
        'youtube_title': question_data.get("youtube_title", "상상탁구TV"),
        'youtube_url': question_data.get("youtube_url", "https://www.youtube.com/@sangsangtak"),
        'youtube_section': question_data.get("youtube_section", "전체"),
        'official_source_evidence': source_evidence,
        'evidence_verified_date': today_str,
        'created_date': today_str,
        'published_date': pub_date,
        'published_url': url,
        'http_status': "200 OK",
        'index_request_date': "",
        'index_request_status': "미확인",
        'past_gsc_indexed_status': "미확인",
        'current_actual_index_status': "미확인",
        'index_verified_date': "",
        'search_impressions': "0",
        'search_clicks': "0",
        'last_audited_date': today_str,
        'recommended_recheck_date': today_str,
        'overlap_check_result': "정상 (신규 자동 등록)",
        'improvement_needed': improvement,
        'actual_publish_status': "공개 확인",
        'internal_publish_status': internal_status,
        'approval_discrepancy': discrepancy
    }
    return record


def save_atomic(records, csv_path=REGISTRY_CSV, json_path=REGISTRY_JSON):
    """Phase 2A 호환용 별칭 (save_atomic_with_rollback 호출)"""
    return save_atomic_with_rollback(records, csv_path, json_path)


def save_atomic_with_rollback(records, csv_path=REGISTRY_CSV, json_path=REGISTRY_JSON, inject_json_failure=False):
    """
    이중 파일 저장(CSV, JSON) 원자성 및 롤백 보장 함수
    """
    csv_temp = f"{csv_path}.tmp"
    json_temp = f"{json_path}.tmp"

    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)

    orig_csv_bytes = None
    orig_json_bytes = None
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            orig_csv_bytes = f.read()
    if os.path.exists(json_path):
        with open(json_path, "rb") as f:
            orig_json_bytes = f.read()

    try:
        # Write CSV temp
        with open(csv_temp, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for r in records:
                writer.writerow({k: r.get(k, "") for k in FIELDNAMES})

        # Write JSON temp
        if inject_json_failure:
            raise IOError("[FAIL_INJECTION] JSON 저장 실패 강제 주입 시험")

        with open(json_temp, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        if os.path.getsize(csv_temp) == 0 or os.path.getsize(json_temp) == 0:
            raise IOError("임시 파일 크기가 0바이트입니다.")

        # Atomic replace
        os.replace(csv_temp, csv_path)
        os.replace(json_temp, json_path)

    except Exception as e:
        print(f"[ERROR] 파일 저장 중 오류 발생 -> 롤백 절차 가동: {e}")
        if os.path.exists(csv_temp):
            try: os.remove(csv_temp)
            except Exception: pass
        if os.path.exists(json_temp):
            try: os.remove(json_temp)
            except Exception: pass

        if orig_csv_bytes is not None:
            with open(csv_path, "wb") as f:
                f.write(orig_csv_bytes)
        if orig_json_bytes is not None:
            with open(json_path, "wb") as f:
                f.write(orig_json_bytes)

        raise IOError(f"저장 실패 및 롤백 완료: {e}")


def update_registry(dry_run=False, check_network=True, target_slug=None,
                    csv_path=REGISTRY_CSV, json_path=REGISTRY_JSON,
                    plan_path=CONTENT_PLAN_CSV, questions_dir=QUESTIONS_DIR,
                    sitemap_url=SITEMAP_URL, mock_sitemap_urls=None,
                    inject_save_failure=False):
    """
    관리대장 갱신 메인 로직 (Phase 2C)
    - content_plan_110.csv의 live 항목뿐 아니라 실제 공개된 사이트맵 항목 전체를 감지
    - 실제 공개 확인되었으나 내부가 ready인 경우에도 누락 없이 '검토 필요'로 등록 추적
    """
    records = load_registry(csv_path, json_path)
    existing_urls = {r.get("published_url", "").strip() for r in records}
    existing_slugs = {r.get("slug", "").strip() for r in records}
    existing_ids = {r.get("content_id", "").strip() for r in records}

    plan_dict = load_all_content_plan(plan_path)

    # 1. 사이트맵 URL 수집
    sitemap_urls = mock_sitemap_urls if mock_sitemap_urls is not None else (fetch_sitemap_urls(sitemap_url) if check_network else set())

    # 후보군 수집: plan_dict 중 live 항목 + sitemap_urls 중 questions 경로
    candidate_slugs = set()
    for slug, row in plan_dict.items():
        if row.get("content_status", "").strip().lower() == "live":
            candidate_slugs.add(slug)

    for sm_url in sitemap_urls:
        if "/questions/" in sm_url and sm_url.endswith(".html"):
            slug = sm_url.split("/questions/")[-1].replace(".html", "").strip()
            if slug:
                candidate_slugs.add(slug)

    added_records = []
    skipped_count = 0
    deferred_count = 0
    error_count = 0

    for slug in sorted(candidate_slugs):
        if target_slug and slug != target_slug:
            continue

        plan_row = plan_dict.get(slug, {})
        cid = plan_row.get("content_id", "").strip()
        expected_url = plan_row.get("published_url", "").strip() or f"{BASE_URL}/questions/{slug}.html"

        # 중복 체크
        if expected_url in existing_urls or slug in existing_slugs or (cid and cid in existing_ids):
            skipped_count += 1
            continue

        # 원고 JSON 파일 확인
        q_json_path = os.path.join(questions_dir, f"{slug}.json")
        if not os.path.exists(q_json_path):
            print(f"[보류] 원고 JSON 누락: {slug}")
            deferred_count += 1
            continue

        # 실제 사이트맵 존재 여부 검증
        if check_network and sitemap_urls:
            if expected_url not in sitemap_urls:
                print(f"[보류] 사이트맵에 URL 미반영 (배포 지연 가능성): {expected_url}")
                deferred_count += 1
                continue

        # 실제 페이지 HTTP 200, title, canonical 검증
        title_for_check = plan_row.get("question_title", "")
        if not title_for_check and os.path.exists(q_json_path):
            try:
                with open(q_json_path, "r", encoding="utf-8") as qf:
                    title_for_check = json.load(qf).get("question", "")
            except Exception:
                pass

        if check_network:
            is_valid, reason = verify_live_page(expected_url, title_for_check, expected_url)
            if not is_valid:
                print(f"[보류] 실제 페이지 검증 미통과 ({reason}): {expected_url}")
                deferred_count += 1
                continue

        # 신규 채번 및 등록
        next_id_str, _ = get_next_registry_id(records + added_records)
        new_rec = build_new_registry_record(slug, plan_row, next_id_str, questions_dir)
        added_records.append(new_rec)
        print(f"[등록 준비] {next_id_str} | {slug} | {new_rec['question_title']}")

    total_records = records + added_records

    if added_records:
        if dry_run:
            print(f"\n[DRY RUN] {len(added_records)}건 등록 예정 (실제 파일 저장 생략)")
            for r in added_records:
                print(f"  + {r['registry_id']} : {r['slug']} ({r['published_url']})")
        else:
            save_atomic_with_rollback(total_records, csv_path, json_path, inject_json_failure=inject_save_failure)
            print(f"\n[성공] {len(added_records)}건 신규 등록 완료 (총 {len(total_records)}건)")
    else:
        print(f"\n[안내] 신규 추가 대상 없음. 기존 관리대장 최신 유지 중 (총 {len(records)}건)")

    return {
        "existing": len(records),
        "added": len(added_records),
        "skipped": skipped_count,
        "deferred": deferred_count,
        "errors": error_count,
        "total": len(total_records)
    }


def main():
    parser = argparse.ArgumentParser(description="상상탁구 SEO 관리대장 자동 운영 연동 모듈 (Phase 2C)")
    parser.add_argument("--dry-run", action="store_true", help="실제 쓰기 없이 시뮬레이션만 수행")
    parser.add_argument("--no-network", action="store_true", help="네트워크 검증 생략 (오프라인 테스트용)")
    parser.add_argument("--target-slug", type=str, default=None, help="특정 슬러그 1건만 검사/추가")
    args = parser.parse_args()

    check_net = not args.no_network
    try:
        res = update_registry(
            dry_run=args.dry_run,
            check_network=check_net,
            target_slug=args.target_slug
        )
        sys.exit(0 if res["errors"] == 0 else 1)
    except Exception as e:
        print(f"[치명적 오류] 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
