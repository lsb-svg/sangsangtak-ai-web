#!/usr/bin/env python3
"""
scripts/simulate_phase3c3k.py
Phase 3C-3K Verification of DRY-RUN Full Isolation & Strict Content Verification
Tests:
A. DRY-RUN + Normal Live State -> 0 deployment outputs, no publish trigger
B. DRY-RUN + 404 Broken Live State -> Outputs warning log, but STRICTLY 0 deployment signals (has_published=false)
C. LIVE + Recovery Needed -> Initiates recovery with has_published=true & is_recovery=true
D. URL 200 + Content Mismatch -> verify_live_url_online strictly FAILS
E. URL 200 + Accurate Content -> verify_live_url_online PASSES
F. 110 Content plan integrity: Live 7, Ready 4, Hold 15, Planned 84
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
    print("PHASE 3C-3K: DRY-RUN ISOLATION & CONTENT VERIFICATION TESTS")
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

        gh_output = tmp / 'mock_github_output.txt'

        # -------------------------------------------------------------
        # TEST A: DRY-RUN + Normal Live State -> 0 deploy signals
        # -------------------------------------------------------------
        print("\n--- TEST A: DRY-RUN + Healthy Live State ---")
        gh_output.write_text('', encoding='utf-8')
        res_a = run_in_tmp(
            ['scripts/publish_daily_qa.py', '--dry-run', '--check-network'],
            env={'GITHUB_OUTPUT': str(gh_output)}
        )
        print(res_a.stdout.strip())
        captured_a = gh_output.read_text(encoding='utf-8').strip()
        assert "has_published" not in captured_a
        assert "AWAITING_EDITORIAL_APPROVAL" in res_a.stdout
        print("  ✓ Test A PASS: No deployment signals triggered in healthy DRY-RUN")

        # -------------------------------------------------------------
        # TEST B: DRY-RUN + 404 Broken Live State -> Warning only, 0 deploy signals
        # -------------------------------------------------------------
        print("\n--- TEST B: DRY-RUN + 404 Live State -> Absolute Deploy Isolation ---")
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

        gh_output.write_text('', encoding='utf-8')
        res_b = run_in_tmp(
            ['scripts/publish_daily_qa.py', '--dry-run', '--check-network'],
            env={'GITHUB_OUTPUT': str(gh_output)}
        )
        print(res_b.stdout.strip())
        captured_b = gh_output.read_text(encoding='utf-8').strip()
        assert "has_published" not in captured_b
        assert "is_recovery" not in captured_b
        assert "DRY-RUN: Deployment recovery needed" in res_b.stdout
        print("  ✓ Test B PASS: DRY-RUN detects recovery need but STRICTLY isolates deployment (0 deploy signals)")

        # -------------------------------------------------------------
        # TEST C: LIVE + Recovery Needed -> Executes deploy signals
        # -------------------------------------------------------------
        print("\n--- TEST C: LIVE Mode + Recovery Needed -> Executes Recovery Signals ---")
        gh_output.write_text('', encoding='utf-8')
        res_c = run_in_tmp(
            ['scripts/publish_daily_qa.py', '--live', '--check-network'],
            env={'GITHUB_OUTPUT': str(gh_output)}
        )
        print(res_c.stdout.strip())
        captured_c = gh_output.read_text(encoding='utf-8').strip()
        assert "has_published=true" in captured_c
        assert "is_recovery=true" in captured_c
        assert "published_slug=gear-recommend-beginner-racket" in captured_c
        print("  ✓ Test C PASS: Live mode correctly triggers recovery deploy signals")

        # -------------------------------------------------------------
        # TEST D: URL 200 + Content Mismatch -> Strict Failure
        # -------------------------------------------------------------
        print("\n--- TEST D: URL 200 + Content Mismatch Verification ---")
        sys.path.insert(0, str(ROOT))
        from scripts.publish_daily_qa import verify_live_url_online
        
        ok_d, msg_d = verify_live_url_online(
            "https://lsb-svg.github.io/sangsangtak-ai-web/questions/gear-recommend-beginner-racket.html",
            expected_slug="pro-player-gear-limjonghoon",
            retries=1,
            delay=1
        )
        print(f"Content Mismatch Check Result: {ok_d} | {msg_d}")
        assert not ok_d
        assert "Content mismatch" in msg_d
        print("  ✓ Test D PASS: Mismatched content correctly rejected")

        # -------------------------------------------------------------
        # TEST E: URL 200 + Accurate Content -> Success
        # -------------------------------------------------------------
        print("\n--- TEST E: URL 200 + Accurate Content Verification ---")
        ok_e, msg_e = verify_live_url_online(
            "https://lsb-svg.github.io/sangsangtak-ai-web/questions/gear-recommend-beginner-racket.html",
            expected_slug="gear-recommend-beginner-racket",
            retries=1,
            delay=1
        )
        print(f"Accurate Content Check Result: {ok_e} | {msg_e}")
        assert ok_e
        print("  ✓ Test E PASS: Correct page and question title successfully verified")

        # -------------------------------------------------------------
        # TEST F: Plan Status Count Integrity
        # -------------------------------------------------------------
        print("\n--- TEST F: Plan Status Count Integrity ---")
        res_f = run_in_tmp(['scripts/verify_content_plan.py'])
        assert res_f.returncode == 0
        print("  ✓ Test F PASS: Plan integrity intact: Live 7, Ready 4, Hold 15, Planned 84 (Total 110)")

    print("\n==================================================================")
    print("ALL 6 TESTS PASSED WITH 100% SUCCESS")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
