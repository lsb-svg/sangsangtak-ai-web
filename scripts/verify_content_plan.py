#!/usr/bin/env python3
"""
Phase 3C-1B: Formal verification script for content_plan_110.csv
Validates:
1. Exact 110 rows
2. Category count across 8 categories
3. Status breakdown (6 live, 15 hold, 89 planned)
4. Existing 21 questions preserved exactly (slug & status)
5. publish_order range (001 to 110) with no duplicates or gaps
6. 100% unique slugs and titles
7. Valid app menu mapping
8. Strict data integrity for planned vs live items
"""
import sys, csv, json
from collections import Counter
from pathlib import Path

def run_checks():
    ROOT = Path(__file__).resolve().parent.parent
    csv_path = ROOT / "content_plan_110.csv"
    assert csv_path.exists(), "content_plan_110.csv does not exist"

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    print(f"[CHECK 1] Row count: {len(rows)} (Target: 110)")
    assert len(rows) == 110, f"Expected 110 rows, got {len(rows)}"

    print("[CHECK 2] Status breakdown:")
    statuses = Counter(r["content_status"] for r in rows)
    for s, count in statuses.items():
        print(f"  - {s}: {count}")
    # Allow live status to grow as items are reviewed and published
    assert statuses.get("live", 0) >= 6, f"Expected at least 6 live items, got {statuses.get('live')}"
    assert statuses.get("hold", 0) == 15, f"Expected exactly 15 hold items, got {statuses.get('hold')}"
    total_items = statuses.get("planned", 0) + statuses.get("ready", 0) + statuses.get("hold", 0) + statuses.get("live", 0)
    assert total_items == 110, f"Expected 110 total items, got {total_items}"

    print("[CHECK 3] Category breakdown across 8 categories:")
    cats = Counter(r["category"] for r in rows)
    expected_cats = {
        "스타플레이어·아마추어 장비관": 20,
        "AI 장비추천": 15,
        "배우기·기술 레슨": 12,
        "전국 탁구대회": 15,
        "라지볼": 12,
        "장애인 탁구": 10,
        "국내·세계 랭킹": 12,
        "탁구장·맞춤진단·앱 활용": 14
    }
    for c, target in expected_cats.items():
        actual = cats.get(c, 0)
        print(f"  - {c}: {actual}/{target}")
        assert actual == target, f"Category count mismatch for {c}: {actual} vs {target}"

    print("[CHECK 4] Existing questions verification:")
    existing_files = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "questions").glob("*.json")}
    assert len(existing_files) >= 21, f"Expected at least 21 questions files, got {len(existing_files)}"

    plan_by_slug = {r["slug"]: r for r in rows}
    assert len(plan_by_slug) == 110, "Duplicate slug in plan"

    # Core 6 live questions
    core_6_live = {"drive-long", "drive-net", "find-club", "para-classes", "rubber-choice", "tournament-check"}
    for slug in core_6_live:
        assert slug in plan_by_slug, f"Live slug {slug} missing from content_plan_110.csv"
        assert plan_by_slug[slug]["content_status"] == "live", f"{slug} status must be live"
        assert existing_files[slug]["review_status"] == "reviewed", f"{slug} must be reviewed"

    # Core 15 hold questions
    core_15_hold = {
        "amateur-gear-leejunsang", "diagnosis-playstyle", "domestic-division-ranking",
        "gear-recommend-drive-combo", "largeball-difference", "largeball-rubber",
        "pro-player-gear-fanzhendong", "pro-player-gear-felix-lebrun",
        "pro-player-gear-harimoto-tomokazu", "pro-player-gear-jangwoojin",
        "pro-player-gear-malong", "pro-player-gear-miwa-harimoto",
        "pro-player-gear-shinyubin", "tournament-registration-guide", "world-ranking-system"
    }
    for slug in core_15_hold:
        assert slug in plan_by_slug, f"Hold slug {slug} missing from content_plan_110.csv"
        assert plan_by_slug[slug]["content_status"] == "hold", f"{slug} status must be hold"
        assert existing_files[slug]["review_status"] == "editorial_review_required", f"{slug} must be hold in JSON"

    print(f"  - Core 6 live and 15 hold questions preserved and verified (Total questions on disk: {len(existing_files)}).")

    print("[CHECK 5] Slug and Question Title uniqueness:")
    slug_counts = Counter(r["slug"] for r in rows)
    assert max(slug_counts.values()) == 1, "Duplicate slug found"
    title_counts = Counter(r["question_title"] for r in rows)
    assert max(title_counts.values()) == 1, "Duplicate question title found"
    print("  - Slugs unique: 110/110")
    print("  - Titles unique: 110/110")

    print("[CHECK 6] Publish order sequence check:")
    orders = [r["publish_order"] for r in rows]
    expected_orders = [f"{i:03d}" for i in range(1, 111)]
    assert sorted(orders) == expected_orders, "publish_order sequence has gaps or duplicates"
    print("  - publish_order: 001 through 110 continuous without gaps")

    print("[CHECK 7] App menu validation:")
    valid_menus = {"AI 장비추천", "배우기", "경기일정", "랭킹", "탁구장", "맞춤진단", "홈"}
    for r in rows:
        menu = r["app_menu"]
        assert menu in valid_menus, f"Invalid app_menu: '{menu}' in {r['slug']}"
    print(f"  - All rows properly mapped to valid app menus: {sorted(valid_menus)}")

    print("[CHECK 8] Planned/Ready/Live status field sanity:")
    for r in rows:
        st = r["content_status"]
        if st in ("planned", "ready", "hold"):
            assert r["published_url"] == "", f"{st} question {r['slug']} must not have published_url"
            assert r["published_date"] == "", f"{st} question {r['slug']} must not have published_date"
        elif st == "live":
            assert r["published_url"].startswith("https://"), f"Live question {r['slug']} missing published_url"
            assert r["published_date"] != "", f"Live question {r['slug']} missing published_date"
    print("  - Status fields strictly isolated between unpublished (planned/ready/hold) and live.")

    print("\n>>> ALL VERIFICATION CHECKS PASSED (100% OK) <<<")

if __name__ == "__main__":
    run_checks()

