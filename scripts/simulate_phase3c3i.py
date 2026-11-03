#!/usr/bin/env python3
"""
scripts/simulate_phase3c3i.py
Comprehensive Isolated Simulation for Phase 3C-3I:
Scenarios Tested:
A. Normal publishing and deployment success
B. Git state recorded as live, but Pages deployment failed (simulated 404/network failure)
C. Re-running after failure: identifies unverified live item and triggers recovery instead of advancing
D. Blocks advancing to next candidate until recovery succeeds
E. Unapproved candidate blocking maintained
F. Duplicate publish prevention on same date maintained
"""
import sys
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
    print("PHASE 3C-3I: DEPLOYMENT FAILURE RECOVERY & ISOLATION SIMULATION")
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

        def run_in_tmp(cmd_list):
            return subprocess.run(
                [sys.executable] + cmd_list,
                cwd=str(tmp),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

        # -----------------------------------------------------------------
        # TEST A: Normal Publishing & Deployment Success
        # -----------------------------------------------------------------
        print("\n--- TEST A: Normal Publishing & Deployment Verification ---")
        # Editor approves gear-recommend-inner-vs-outer for 2026-11-04
        q_file = tmp / 'questions' / 'gear-recommend-inner-vs-outer.json'
        d = json.loads(q_file.read_text(encoding='utf-8'))
        d['review_status'] = 'reviewed'
        q_file.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')

        res = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-04'])
        print(res.stdout.strip())
        assert "[PRODUCTION PUBLISH SUCCESS]" in res.stdout
        assert "gear-recommend-inner-vs-outer" in res.stdout
        print("  ✓ Test A PASS: Approved candidate successfully published")

        # -----------------------------------------------------------------
        # TEST B: Git Recorded as Live, but Pages Deployment Failed
        # -----------------------------------------------------------------
        print("\n--- TEST B: Simulation of Git Updated Live + Pages Deploy Failure ---")
        # Suppose gear-recommend-inner-vs-outer was recorded as live in CSV,
        # but the deployment check failed (e.g. invalid URL or 404).
        res_verify_fail = run_in_tmp(['scripts/publish_daily_qa.py', '--verify-url', 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/non-existent-page-404.html'])
        print("Verification Output on 404:", res_verify_fail.stdout.strip())
        assert res_verify_fail.returncode != 0
        assert "FAIL" in res_verify_fail.stdout
        print("  ✓ Test B PASS: Deployment failure correctly detected and non-zero exit code returned")

        # -----------------------------------------------------------------
        # TEST C & D: Recovery Priority Check - Blocks Advancing to Next Candidate
        # -----------------------------------------------------------------
        print("\n--- TEST C & D: Recovery Check Blocks Next Candidate ---")
        # In find_next_candidate with check_network=True, if the latest live item fails verification,
        # it flags recovery needed and does NOT advance to the next ready candidate.
        sys.path.insert(0, str(ROOT))
        from scripts.publish_daily_qa import find_next_candidate, load_plan
        
        # Mock plan where latest live item points to an unreachable URL
        mock_plan = load_plan()
        latest_live = next(r for r in mock_plan if r['slug'] == 'gear-recommend-beginner-racket')
        orig_url = latest_live['published_url']
        latest_live['published_url'] = 'https://lsb-svg.github.io/sangsangtak-ai-web/questions/simulated-broken-link.html'
        
        cand, reason = find_next_candidate(mock_plan, '2026-11-05', dry_run=False, auto_approve=False, check_network=True)
        print("Candidate Returned:", cand['slug'] if cand else None, "| Reason:", reason)
        assert "[RECOVERY NEEDED]" in reason
        assert cand['slug'] == 'gear-recommend-beginner-racket'  # Did NOT advance to pro-player-gear-limjonghoon!
        print("  ✓ Test C & D PASS: Next candidate strictly blocked until previous live page is verified online")

        # Restore URL
        latest_live['published_url'] = orig_url

        # -----------------------------------------------------------------
        # TEST E: Unapproved Candidate Blocking
        # -----------------------------------------------------------------
        print("\n--- TEST E: Unapproved Candidate Blocking ---")
        res_e = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-05'])
        print(res_e.stdout.strip())
        assert "AWAITING_EDITORIAL_APPROVAL" in res_e.stdout
        print("  ✓ Test E PASS: Unapproved candidate blocked from publishing")

        # -----------------------------------------------------------------
        # TEST F: Duplicate Publish Prevention on Same Date
        # -----------------------------------------------------------------
        print("\n--- TEST F: Duplicate Publish Prevention ---")
        res_f = run_in_tmp(['scripts/publish_daily_qa.py', '--live', '--force-date', '2026-11-04'])
        print(res_f.stdout.strip())
        assert "[SKIP] Already published on 2026-11-04" in res_f.stdout
        print("  ✓ Test F PASS: Same date duplicate publish blocked")

    print("\n==================================================================")
    print("ALL 6 ISOLATED SAFETY & RECOVERY TESTS PASSED (100% OK)")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
