#!/usr/bin/env python3
"""
scripts/publish_daily_qa.py
Automated daily QA publisher with strict safety checks and DRY-RUN mode.
- Reads content_plan_110.csv
- Finds the next candidate with content_status == 'ready' (ordered by publish_order)
- Validates corresponding questions/<slug>.json exists and matches schema
- Validates candidate approval condition
- Prevents duplicate publishing on the same date (1 article/day max)
- In DRY-RUN mode (--dry-run), performs 100% simulation without writing to disk
"""
import sys
import os
import json
import csv
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
PLAN_CSV = ROOT / "content_plan_110.csv"
CONFIG_FILE = ROOT / "config.json"

KST = timezone(timedelta(hours=9))

def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file missing: {CONFIG_FILE}")
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

def load_plan():
    if not PLAN_CSV.exists():
        raise FileNotFoundError(f"Plan CSV missing: {PLAN_CSV}")
    with open(PLAN_CSV, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_plan(rows):
    fieldnames = list(rows[0].keys())
    with open(PLAN_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def validate_question_content(q_json_path, expected_slug):
    if not q_json_path.exists():
        return False, f"Question JSON not found: {q_json_path.name}"
    
    try:
        data = json.loads(q_json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"Invalid JSON format in {q_json_path.name}: {e}"
    
    if data.get("id") != expected_slug:
        return False, f"Slug mismatch: JSON id '{data.get('id')}' vs expected '{expected_slug}'"
    
    required_fields = (
        "id", "question", "category", "app_session", "feature_status",
        "answer", "steps", "related_guide", "review_status",
        "source_url", "verified_date", "reference_note"
    )
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing or empty required field: {field}"
    
    if len(data.get("steps", [])) < 2:
        return False, "Steps must contain at least 2 guidance points"
    
    return True, "Valid"

def verify_live_url_online(published_url, expected_keyword=None, expected_slug=None, retries=3, delay=5, timeout=10):
    """
    Verifies that the published URL responds with HTTP 200 and contains expected keyword/slug.
    Includes limited retry mechanism for CDN/Pages propagation delays.
    """
    import urllib.request
    import time

    # If expected_slug is provided, find its question title or signature from local question JSON
    search_terms = []
    if expected_keyword:
        search_terms.append(expected_keyword)
    if expected_slug:
        search_terms.append(expected_slug)
        q_path = QUESTIONS_DIR / f"{expected_slug}.json"
        if q_path.exists():
            try:
                q_obj = json.loads(q_path.read_text(encoding="utf-8"))
                if q_obj.get("question"):
                    search_terms.append(q_obj["question"])
            except Exception:
                pass

    last_err = "Unknown error"
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                published_url,
                headers={"User-Agent": "Mozilla/5.0 (SangsangTak-SEO-HealthCheck)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    last_err = f"HTTP status {resp.status}"
                else:
                    content = resp.read().decode("utf-8", errors="replace")
                    # Check for matching term
                    if search_terms:
                        matched = any(term in content for term in search_terms)
                        if not matched:
                            last_err = f"Content mismatch: expected terms {search_terms} not found in page HTML"
                        else:
                            return True, f"Online verified on attempt {attempt}"
                    else:
                        return True, f"Online verified (HTTP 200) on attempt {attempt}"
        except Exception as e:
            last_err = f"Network/HTTP exception: {e}"

        if attempt < retries:
            time.sleep(delay)

    return False, last_err

def find_pending_or_unverified_live(plan_rows, check_network=False):
    """
    Checks if there is a 'live' record in CSV whose actual deployment is unverified or broken.
    If check_network is True, checks the actual URL online.
    Prioritizes recovering unverified deployments before publishing new candidates.
    """
    live_rows = [r for r in plan_rows if r.get("content_status") == "live"]
    if not live_rows:
        return None
    
    # Sort by published_date / publish_order to check the most recently published items
    live_rows.sort(key=lambda x: (x.get("published_date", ""), x.get("publish_order", "")), reverse=True)
    
    if check_network:
        recent_item = live_rows[0]
        pub_url = recent_item.get("published_url", "")
        slug = recent_item.get("slug", "")
        if pub_url.startswith("https://"):
            ok, msg = verify_live_url_online(pub_url, slug, timeout=5)
            if not ok:
                return recent_item, f"Last published item {slug} is not online ({msg}). Recovery required!"
    return None

def find_next_candidate(plan_rows, target_date_str, dry_run=True, auto_approve=False, check_network=False):
    # STEP 0: Recovery priority check: is the last published live item broken or missing online?
    unverified = find_pending_or_unverified_live(plan_rows, check_network=check_network)
    if unverified:
        item, reason = unverified
        return item, f"[RECOVERY NEEDED] {reason}"

    # STEP 1: Check if a question was already published on this target_date_str
    already_published_today = [
        r for r in plan_rows
        if r.get("published_date") == target_date_str and r.get("content_status") == "live"
    ]
    if already_published_today:
        return None, f"Already published on {target_date_str}: {already_published_today[0]['slug']}"

    # STEP 2: Filter ready items sorted by publish_order
    ready_rows = [r for r in plan_rows if r.get("content_status") == "ready"]
    if not ready_rows:
        return None, "No candidates with content_status == 'ready' found"
    
    ready_rows.sort(key=lambda x: int(x.get("publish_order", "999")))
    
    # In DRY-RUN mode or when auto_approve is True, inspect the very first ready candidate
    if dry_run or auto_approve:
        return ready_rows[0], "Candidate found"
    
    # In live production mode without auto_approve:
    # Scan in publish_order for the first candidate whose JSON is explicitly approved ('reviewed').
    # Unapproved candidates remain safely held in queue and do NOT block approved candidates behind them.
    for cand in ready_rows:
        slug = cand["slug"]
        q_file = QUESTIONS_DIR / f"{slug}.json"
        if q_file.exists():
            try:
                data = json.loads(q_file.read_text(encoding="utf-8"))
                if data.get("review_status") == "reviewed":
                    return cand, "Approved candidate found"
            except Exception:
                continue
                
    # If no ready candidates are approved, return the first one so it reports AWAITING_EDITORIAL_APPROVAL
    return ready_rows[0], "Candidate awaiting approval"

def run_publisher(dry_run=True, force_date=None, auto_approve=False, check_network=False):
    now_kst = datetime.now(KST)
    target_date = force_date or now_kst.strftime("%Y-%m-%d")
    
    config = load_config()
    public_url = config.get("public_url", "").rstrip("/") + "/"
    
    plan_rows = load_plan()
    
    print(f"=== DAILY QA PUBLISHER (Mode: {'DRY-RUN' if dry_run else 'PRODUCTION'}) ===")
    print(f"Target Date (KST): {target_date}")
    
    candidate, reason = find_next_candidate(plan_rows, target_date, dry_run=dry_run, auto_approve=auto_approve, check_network=check_network)
    if not candidate:
        print(f"[SKIP] {reason}")
        return {
            "status": "SKIPPED",
            "reason": reason,
            "candidate": None
        }
    
    slug = candidate["slug"]
    cid = candidate["content_id"]
    order = candidate["publish_order"]
    title = candidate["question_title"]
    q_file = QUESTIONS_DIR / f"{slug}.json"
    is_recovery = "[RECOVERY NEEDED]" in reason

    if is_recovery:
        print(f"\n[!] INITIATING DEPLOYMENT RECOVERY:")
        print(f"  - Target: {order} / {cid} ({slug})")
        print(f"  - Issue: {reason}")
        
        expected_url = candidate.get("published_url") or f"{public_url}questions/{slug}.html"
        
        if dry_run:
            print(f"  - DRY-RUN: Deployment recovery needed for {slug}, but DRY-RUN simulation mode prevents execution.")
            print(f"  - No disk writes, no CI output triggers, no deploy actions executed.")
            return {
                "status": "DRY_RUN_RECOVERY_DETECTED",
                "candidate": slug,
                "url": expected_url,
                "reason": reason
            }

        print(f"  - Action: Triggering build & direct Pages redeployment for {slug} without modifying plan status.")
        
        # In LIVE mode only, export outputs so deploy-pages executes
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output and os.path.exists(github_output):
            with open(github_output, "a", encoding="utf-8") as gh_out:
                gh_out.write("has_published=true\n")
                gh_out.write(f"published_slug={slug}\n")
                gh_out.write(f"published_url={expected_url}\n")
                gh_out.write("is_recovery=true\n")
        
        return {
            "status": "RECOVERY_INITIATED",
            "candidate": slug,
            "url": expected_url,
            "reason": reason
        }

    print(f"\n[1] Next In Queue:")
    print(f"  - Order/ID: {order} / {cid}")
    print(f"  - Slug: {slug}")
    print(f"  - Title: {title}")
    
    # Content quality and metadata validation
    is_valid, val_msg = validate_question_content(q_file, slug)
    if not is_valid:
        print(f"[REJECT] Content validation failed for {slug}: {val_msg}")
        return {
            "status": "VALIDATION_ERROR",
            "candidate": slug,
            "error": val_msg
        }
    print(f"[2] Content validation: PASS ({val_msg})")
    
    # Check explicit editorial approval condition
    q_data = json.loads(q_file.read_text(encoding="utf-8"))
    
    # In safety policy: JSON must either be marked 'reviewed' OR auto_approve must be explicitly granted
    # If JSON is still 'editorial_review_required' and auto_approve is False, dry-run reports awaiting approval.
    has_approval = (q_data.get("review_status") == "reviewed") or auto_approve
    if not has_approval:
        expected_url = f"{public_url}questions/{slug}.html"
        print(f"[3] Approval Status: AWAITING_EDITORIAL_APPROVAL (JSON review_status is '{q_data.get('review_status')}')")
        print(f"  - Expected Live URL upon approval: {expected_url}")
        print(f"  - Candidate is ready in CSV queue, but safely blocked from live publication until explicit editorial sign-off.")
        return {
            "status": "AWAITING_APPROVAL",
            "candidate": slug,
            "expected_url": expected_url,
            "publish_order": order
        }
    
    expected_url = f"{public_url}questions/{slug}.html"
    print(f"[3] Approval Status: APPROVED (Will transition to 'reviewed' / 'live')")
    print(f"  - Target Live URL: {expected_url}")
    
    if dry_run:
        print(f"\n[DRY-RUN SIMULATION SUCCESSFUL]")
        print(f"  - Would update {q_file.name} review_status -> 'reviewed'")
        print(f"  - Would update {PLAN_CSV.name} [{cid}] content_status -> 'live', published_date -> '{target_date}', published_url -> '{expected_url}'")
        print(f"  - No disk files were modified.")
        return {
            "status": "DRY_RUN_PASS",
            "candidate": slug,
            "expected_url": expected_url,
            "target_date": target_date
        }
    else:
        # PRODUCTION MODE: Update JSON
        q_data["review_status"] = "reviewed"
        q_file.write_text(json.dumps(q_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        
        # Update CSV
        for r in plan_rows:
            if r["slug"] == slug:
                r["content_status"] = "live"
                r["published_date"] = target_date
                r["published_url"] = expected_url
                break
        save_plan(plan_rows)
        
        # Output GitHub Actions step output if running in CI
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output and os.path.exists(github_output):
            with open(github_output, "a", encoding="utf-8") as gh_out:
                gh_out.write("has_published=true\n")
                gh_out.write(f"published_slug={slug}\n")
                gh_out.write(f"published_url={expected_url}\n")
        
        print(f"\n[PRODUCTION PUBLISH SUCCESS]")
        print(f"  - Updated {q_file.name} to reviewed")
        print(f"  - Updated CSV plan for {slug} to live")
        return {
            "status": "PUBLISHED",
            "candidate": slug,
            "url": expected_url,
            "date": target_date
        }

if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Daily QA Publisher")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate without changes")
    parser.add_argument("--live", action="store_true", help="Actually execute publish")
    parser.add_argument("--force-date", type=str, default=None, help="Force specific date (YYYY-MM-DD)")
    parser.add_argument("--auto-approve", action="store_true", help="Simulate approval sign-off")
    parser.add_argument("--check-network", action="store_true", help="Verify online deployment health")
    parser.add_argument("--verify-url", type=str, default=None, help="Verify a specific published URL online")
    parser.add_argument("--verify-slug", type=str, default=None, help="Expected slug for verify-url check")
    parser.add_argument("--verify-keyword", type=str, default=None, help="Expected text keyword for verify-url check")
    args = parser.parse_args()

    if args.verify_url:
        ok, msg = verify_live_url_online(
            args.verify_url,
            expected_keyword=args.verify_keyword,
            expected_slug=args.verify_slug
        )
        print(f"URL Verification: {'PASS' if ok else 'FAIL'} - {msg}")
        sys.exit(0 if ok else 1)

    is_dry_run = not args.live
    res = run_publisher(dry_run=is_dry_run, force_date=args.force_date, auto_approve=args.auto_approve, check_network=args.check_network)

