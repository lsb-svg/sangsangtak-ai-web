#!/usr/bin/env python3
"""
scripts/simulate_phase3c3j.py
Phase 3C-3J: Verification of Deployment Failure Detection and Auto-Recovery Execution
Validates:
1. When latest live question fails online verification, it triggers RECOVERY_INITIATED.
2. It outputs has_published=true so build and deploy-pages execute, but is_recovery=true so it skips redundant git commit/push.
3. New candidate selection is blocked until the recovery succeeds.
4. When online check passes, normal candidate selection and duplicate prevention resume.
"""
import sys
import os
import shutil
import tempfile
import subprocess
import json
import csv
from pathlib import Path

def run_tests():
    sys.stdout.reconfigure(encoding="utf-8")
    ROOT = Path(__file__).resolve().parent.parent

    print("==================================================================")
    print("PHASE 3C-3J: RECOVERY EXECUTION & REDEPLOYMENT PATH TEST")
    print("==================================================================")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        print(f"[SETUP] Sandbox directory: {tmp}")

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

        def run_in_tmp(cmd_list, env=None):
            e = os.environ.copy()
            if env:
                e.update(env)
            return subprocess.run(
                [sys.executable] + cmd_list,
                cwd=str(tmp),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=e
            )

        # -------------------------------------------------------------
        # TEST 1: Baseline Online Check with current live site
        # -------------------------------------------------------------
        print("\n--- TEST 1: Baseline Online Check on Current Live Site ---")
        res1 = run_in_tmp(['scripts/publish_daily_qa.py', '--dry-run', '--check-network'])
        print(res1.stdout.strip())
        assert "[!] INITIATING DEPLOYMENT RECOVERY" not in res1.stdout
        print("  ✓ Test 1 PASS: Healthy live deployment does not trigger recovery")

        # -------------------------------------------------------------
        # TEST 2: Simulated Deployment Failure Triggers Actual Recovery Path
        # -------------------------------------------------------------
        print("\n--- TEST 2: Simulated Broken Live URL Triggers Recovery Execution ---")
        # In mock plan, point latest live item (gear-recommend-beginner-racket) to a 404 URL
        csv_file = tmp / 'content_plan_110.csv'
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            plan = list(csv.DictReader(f))
        for r in plan:
            if r['slug'] == 'gear-recommend-beginner-racket':
                r['published_url'] = 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/non-existent-broken-404.html'
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(plan[0].keys()))
            writer.writeheader()
            writer.writerows(plan)

        # Create a mock GITHUB_OUTPUT file
        gh_output = tmp / 'mock_github_output.txt'
        gh_output.write_text('', encoding='utf-8')

        res2 = run_in_tmp(
            ['scripts/publish_daily_qa.py', '--live', '--check-network'],
            env={'GITHUB_OUTPUT': str(gh_output)}
        )
        print("Recovery Execution Output:")
        print(res2.stdout.strip())
        assert "[!] INITIATING DEPLOYMENT RECOVERY" in res2.stdout
        assert "gear-recommend-beginner-racket" in res2.stdout

        # Verify GITHUB_OUTPUT received recovery signals
        out_content = gh_output.read_text(encoding='utf-8')
        print("Captured GITHUB_OUTPUT:\n", out_content.strip())
        assert "has_published=true" in out_content
        assert "is_recovery=true" in out_content
        assert "published_slug=gear-recommend-beginner-racket" in out_content
        print("  ✓ Test 2 PASS: Actual recovery path initiated with CI deploy signals")

        # -------------------------------------------------------------
        # TEST 3: Confirm New Candidates Blocked During Recovery
        # -------------------------------------------------------------
        print("\n--- TEST 3: Next Candidates Strictly Blocked During Recovery ---")
        # Ensure it did NOT advance to pro-player-gear-limjonghoon or inner-vs-outer
        assert "pro-player-gear-limjonghoon" not in res2.stdout
        assert "gear-recommend-inner-vs-outer" not in res2.stdout
        print("  ✓ Test 3 PASS: Next candidates blocked while recovery is in progress")

        # -------------------------------------------------------------
        # TEST 4: No Duplicate CSV Live Record Generated on Recovery
        # -------------------------------------------------------------
        print("\n--- TEST 4: No Duplicate CSV Live Record Generated ---")
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            plan_after = list(csv.DictReader(f))
        live_count = sum(1 for r in plan_after if r['content_status'] == 'live')
        assert live_count == 7, f"Expected 7 live records, got {live_count}"
        print("  ✓ Test 4 PASS: Plan integrity and live count preserved without duplication")

    print("\n==================================================================")
    print("ALL 4 RECOVERY & ISOLATION TESTS PASSED (100% OK)")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
