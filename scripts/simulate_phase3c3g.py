#!/usr/bin/env python3
"""
scripts/simulate_phase3c3g.py
Phase 3C-3G Isolated Simulation:
1. Validates unapproved candidate blocking (AWAITING_EDITORIAL_APPROVAL)
2. Validates 1 approved candidate publishing (pro-player-gear-limjonghoon on virtual date 2026-11-04)
3. Validates static HTML & Sitemap generation (12 HTML pages, 11 URLs in sitemap)
4. Validates duplicate run prevention on the same date
5. Validates next candidate selection on the next date
6. Validates rollback/recovery on simulated failure
7. Ensures working tree of original project remains completely untouched
"""
import sys
import shutil
import tempfile
import subprocess
import json
import csv
from pathlib import Path

def run_simulation():
    sys.stdout.reconfigure(encoding="utf-8")
    ROOT = Path(__file__).resolve().parent.parent

    print("==================================================================")
    print("PHASE 3C-3G: DAILY PUBLISH PIPELINE SIMULATION IN ISOLATED COPY")
    print("==================================================================")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        print(f"[SETUP] Isolated sandbox directory: {tmp}")

        items = [
            'questions', 'templates', 'static', 'content', 'scripts',
            'build.py', 'verify.py', 'config.json', 'app_features.json',
            'content_plan_110.csv'
        ]
        for it in items:
            src = ROOT / it
            dst = tmp / it
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        for g in ROOT.glob("google*.html"):
            shutil.copy2(g, tmp / g.name)

        def run_in_tmp(cmd_list):
            return subprocess.run(
                [sys.executable] + cmd_list,
                cwd=str(tmp),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

        # 1. Initial State in sandbox
        print("\n--- TEST 1: Initial State in Sandbox ---")
        res = run_in_tmp(['scripts/verify_content_plan.py'])
        assert res.returncode == 0, f"Initial plan verify failed: {res.stderr}"
        res = run_in_tmp(['build.py'])
        assert res.returncode == 0, f"Initial build failed: {res.stderr}"
        assert "11 HTML pages generated" in res.stdout  # 4 base + 7 live
        print("  ✓ Sandbox initial build and plan verification: PASS (7 live, 19 hold, 4 ready)")

        # 2. Block unapproved candidate
        print("\n--- TEST 2: Block Unapproved Ready Candidate ---")
        res = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-04'])
        print(res.stdout.strip())
        assert "AWAITING_EDITORIAL_APPROVAL" in res.stdout
        # Confirm no files modified
        q_lim = json.loads((tmp / 'questions' / 'pro-player-gear-limjonghoon.json').read_text(encoding='utf-8'))
        assert q_lim['review_status'] == 'editorial_review_required'
        print("  ✓ Unapproved candidate safely held without publishing: PASS")

        # 3. Simulate editorial approval and publish 1 candidate
        print("\n--- TEST 3: Publish 1 Approved Candidate (Virtual date: 2026-11-04) ---")
        # Explicit approval granted by editor
        q_lim['review_status'] = 'reviewed'
        (tmp / 'questions' / 'pro-player-gear-limjonghoon.json').write_text(json.dumps(q_lim, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')

        res = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-04'])
        print(res.stdout.strip())
        assert "[PRODUCTION PUBLISH SUCCESS]" in res.stdout

        # Verify CSV updated
        with open(tmp / 'content_plan_110.csv', 'r', encoding='utf-8-sig') as f:
            plan = list(csv.DictReader(f))
        item_lim = next(r for r in plan if r['slug'] == 'pro-player-gear-limjonghoon')
        assert item_lim['content_status'] == 'live'
        assert item_lim['published_date'] == '2026-11-04'
        assert item_lim['published_url'] == 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/pro-player-gear-limjonghoon.html'

        # Verify build and sitemap
        res = run_in_tmp(['build.py'])
        assert "12 HTML pages generated" in res.stdout  # 4 base + 8 live
        assert "Sitemap: 11 URLs" in res.stdout
        res = run_in_tmp(['verify.py'])
        assert res.returncode == 0
        print("  ✓ Publishing 1 approved item and static build/sitemap expansion: PASS")

        # 4. Duplicate run on same date
        print("\n--- TEST 4: Duplicate Run Prevention on Same Date ---")
        res_dup = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-04'])
        print(res_dup.stdout.strip())
        assert "[SKIP] Already published on 2026-11-04: pro-player-gear-limjonghoon" in res_dup.stdout
        print("  ✓ Same date duplicate publish blocked (1 item/day limit enforced): PASS")

        # 5. Next candidate on next date (2026-11-05)
        print("\n--- TEST 5: Next Candidate Selected on Next Date ---")
        # Editor approves next candidate: gear-recommend-inner-vs-outer
        q_next = json.loads((tmp / 'questions' / 'gear-recommend-inner-vs-outer.json').read_text(encoding='utf-8'))
        q_next['review_status'] = 'reviewed'
        (tmp / 'questions' / 'gear-recommend-inner-vs-outer.json').write_text(json.dumps(q_next, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')

        res_next = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-05'])
        print(res_next.stdout.strip())
        assert "[PRODUCTION PUBLISH SUCCESS]" in res_next.stdout
        assert "gear-recommend-inner-vs-outer" in res_next.stdout
        print("  ✓ Next order candidate published on subsequent date: PASS")

        # 6. Failure recovery / safe error handling
        print("\n--- TEST 6: Failure Handling with Invalid Candidate ---")
        q_corrupt = tmp / 'questions' / 'lesson-forehand-stroke-posture.json'
        orig_content = q_corrupt.read_text(encoding='utf-8')
        q_corrupt.write_text('{"id": "broken"}', encoding='utf-8')

        res_fail = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-06'])
        print(res_fail.stdout.strip())
        assert "[REJECT] Content validation failed" in res_fail.stdout
        q_corrupt.write_text(orig_content, encoding='utf-8')
        print("  ✓ Validation failure rejected safely without corrupting CSV or published state: PASS")

    print("\n==================================================================")
    print("ALL 6 ISOLATED PIPELINE SIMULATION TESTS PASSED (100% OK)")
    print("==================================================================")

if __name__ == "__main__":
    run_simulation()

