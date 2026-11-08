#!/usr/bin/env python3
"""
Phase 3B-1 Comprehensive Content Integrity and Policy Verification
"""
from pathlib import Path
import json
import re
import csv

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
DIST = ROOT / "dist"

def verify_all():
    plan_csv_path = ROOT / "content_plan_110.csv"
    live_slugs = set()
    if plan_csv_path.exists():
        with open(plan_csv_path, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("content_status") == "live" and r.get("slug"):
                    live_slugs.add(r["slug"])

    q_files = list(QUESTIONS_DIR.glob("*.json"))
    print(f"Total question JSON files: {len(q_files)}")

    approved_count = 0
    hold_count = 0
    categories_found = set()

    for qf in q_files:
        obj = json.loads(qf.read_text(encoding="utf-8"))
        qid = obj["id"]
        qtext = obj["question"]
        cat = obj["category"]
        status = obj["review_status"]
        source_type = obj.get("source_type")
        source_url = obj.get("source_url")
        verified_date = obj.get("verified_date")
        ref_note = obj.get("reference_note")

        categories_found.add(cat)

        is_live = (status == "reviewed") and (qid in live_slugs)

        if is_live:
            approved_count += 1
            # Approved live files must have corresponding dist HTML
            assert (DIST / "questions" / f"{qid}.html").exists(), f"Approved {qid} missing in dist"
        else:
            hold_count += 1
            # Hold/ready files must NOT have corresponding dist HTML
            assert not (DIST / "questions" / f"{qid}.html").exists(), f"Hold/ready {qid} leaked to dist!"

        # Policy checks
        if "amateur-gear" in qid:
            assert "대표 직접 확인" in ref_note or source_type == "founder_direct_check"
            assert status == "editorial_review_required", f"Amateur gear {qid} must be HOLD"
        
        if "pro-player-gear" in qid:
            assert "공식 세팅" not in obj["answer"], f"Exaggerated phrase in {qid}"
            assert "앱 등록" in obj["answer"] or "공시" in obj["answer"] or "기록" in obj["answer"]

        if "world-ranking" in qid or "domestic-division" in qid:
            assert verified_date, f"Ranking question {qid} must have verified_date"

    assert approved_count >= 6, f"Expected at least 6 approved questions, got {approved_count}"
    assert hold_count >= 15, f"Expected at least 15 hold questions, got {hold_count}"

    # Verify sitemap has only approved pages
    sitemap_text = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    for qf in q_files:
        obj = json.loads(qf.read_text(encoding="utf-8"))
        qid = obj["id"]
        if (obj["review_status"] == "reviewed") and (qid in live_slugs):
            assert f"questions/{qid}.html" in sitemap_text, f"Approved {qid} missing from sitemap!"
        else:
            assert f"questions/{qid}.html" not in sitemap_text, f"Unreleased {qid} found in sitemap!"

    print("ALL POLICY VERIFICATIONS PASSED:")
    print(f" - Approved (Live HTML & Sitemap): {approved_count} QAs")
    print(f" - Hold (Strictly Isolated): {hold_count} QAs")
    print(f" - Categories active: {len(categories_found)}")

if __name__ == "__main__":
    verify_all()
