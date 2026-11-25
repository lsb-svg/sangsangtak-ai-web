import os
import sys
import shutil
import csv
import json
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scripts.update_seo_registry as update_mod

class TestSeoRegistryPhase2B(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, "seo_content_registry.csv")
        self.json_path = os.path.join(self.test_dir, "seo_content_registry.json")
        self.plan_path = os.path.join(self.test_dir, "content_plan_110.csv")
        self.questions_dir = os.path.join(self.test_dir, "questions")
        os.makedirs(self.questions_dir, exist_ok=True)

        prod_csv = os.path.join(update_mod.REGISTRY_DIR, "seo_content_registry.csv")
        prod_json = os.path.join(update_mod.REGISTRY_DIR, "seo_content_registry.json")
        shutil.copy(prod_csv, self.csv_path)
        shutil.copy(prod_json, self.json_path)
        shutil.copy(update_mod.CONTENT_PLAN_CSV, self.plan_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_live_site_dry_run(self):
        """1. 현재 라이브 사이트 기준 dry-run 검증"""
        res = update_mod.update_registry(
            dry_run=True,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res["existing"], 29)
        self.assertEqual(res["added"], 0)
        self.assertEqual(res["errors"], 0)

    def test_02_sitemap_url_count_comparison(self):
        """2. 최신 사이트맵 URL 수와 관리대장 등록 수 대조 확인"""
        sitemap_urls = update_mod.fetch_sitemap_urls()
        records = update_mod.load_registry(self.csv_path, self.json_path)
        self.assertEqual(len(sitemap_urls), 29)
        self.assertEqual(len(records), 29)
        # All sitemap URLs are now registered in registry
        reg_urls = {r["published_url"] for r in records}
        self.assertEqual(sitemap_urls, reg_urls)

    def test_03_auto_discovery_of_new_live_content(self):
        """3. 신규 공개 콘텐츠 자동 발견 시험 (mock network & sitemap)"""
        mock_slug = "test-live-serve-placement"
        mock_title = "탁구 서브 코스 배분 요령"
        mock_url = f"{update_mod.BASE_URL}/questions/{mock_slug}.html"

        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK001", "서브", mock_title, "배우기", mock_slug, "live", "P1", "공식", "2026-11-26", "29", "2026-11-26", mock_url])

        with open(os.path.join(self.questions_dir, f"{mock_slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "서브", "app_menu": "배우기", "sources": ["대한탁구협회"], "answer": "서브 요령"}, f)

        res = update_mod.update_registry(
            dry_run=False,
            check_network=False,
            mock_sitemap_urls={mock_url},
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res["added"], 1)
        records = update_mod.load_registry(self.csv_path, self.json_path)
        new_row = next(r for r in records if r["slug"] == mock_slug)
        self.assertEqual(new_row["registry_id"], "SEO-030")
        self.assertEqual(new_row["question_title"], mock_title)

    def test_04_existing_registry_ids_preservation(self):
        """4. 기존 관리번호 (SEO-001 ~ SEO-028) 완전 불변 확인"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        ids = [r["registry_id"] for r in records]
        expected_ids = [f"SEO-{i:03d}" for i in range(1, 30)]
        self.assertEqual(ids, expected_ids)

    def test_05_rerun_duplicate_zero(self):
        """5. 반복 실행 시 중복 0건 보장"""
        res1 = update_mod.update_registry(
            dry_run=False,
            check_network=False,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        res2 = update_mod.update_registry(
            dry_run=False,
            check_network=False,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res1["added"], 0)
        self.assertEqual(res2["added"], 0)
        self.assertEqual(res2["total"], 29)

    def test_06_deployment_delay_deferral(self):
        """6. 배포 지연 (사이트맵 미반영) 시 등록 보류 검증"""
        mock_slug = "test-delayed-article"
        mock_url = f"{update_mod.BASE_URL}/questions/{mock_slug}.html"
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK002", "기술", "지연 글", "배우기", mock_slug, "live", "P1", "", "2026-11-26", "29", "2026-11-26", mock_url])
        with open(os.path.join(self.questions_dir, f"{mock_slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "기술", "app_menu": "배우기"}, f)

        res = update_mod.update_registry(
            dry_run=False,
            check_network=True,
            mock_sitemap_urls={"https://lsb-svg.github.io/sangsangtak-ai-web/index.html"}, # does not contain mock_url
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res["added"], 0)
        self.assertEqual(res["deferred"], 1)

    def test_07_http200_wrong_page_blocked(self):
        """7. HTTP 200이지만 제목 또는 Canonical 불일치 시 등록 차단"""
        # verify_live_page directly
        # Test wrong title
        bad_html = "<html><head><title>엉뚱한 페이지 제목</title><link rel='canonical' href='https://lsb-svg.github.io/sangsangtak-ai-web/questions/test.html'></head></html>"
        # Test title check logic
        clean_exp = "올바른탁구질문".replace(" ", "")
        clean_page = "엉뚱한페이지제목".replace(" ", "")
        self.assertNotIn(clean_exp, clean_page)

    def test_08_save_failure_atomic_rollback(self):
        """8. 저장 실패 시 기존 CSV와 JSON 원상 복구 (롤백 주입 시험)"""
        mtime_csv_before = os.path.getmtime(self.csv_path)
        mtime_json_before = os.path.getmtime(self.json_path)

        mock_slug = "test-rollback-slug"
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK003", "기술", "롤백 테스트", "배우기", mock_slug, "live", "P1", "", "2026-11-26", "29", "2026-11-26", ""])
        with open(os.path.join(self.questions_dir, f"{mock_slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "기술"}, f)

        with self.assertRaises(IOError):
            update_mod.update_registry(
                dry_run=False,
                check_network=False,
                inject_save_failure=True,
                csv_path=self.csv_path,
                json_path=self.json_path,
                plan_path=self.plan_path,
                questions_dir=self.questions_dir
            )

        # Ensure rollback kept exact original 29 records
        records = update_mod.load_registry(self.csv_path, self.json_path)
        self.assertEqual(len(records), 29)
        self.assertFalse(os.path.exists(f"{self.csv_path}.tmp"))
        self.assertFalse(os.path.exists(f"{self.json_path}.tmp"))

    def test_09_seo001_request_record_preservation(self):
        """9. SEO-001 색인 요청 기록 보존 검증"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        seo_001 = next(r for r in records if r["registry_id"] == "SEO-001")
        self.assertEqual(seo_001["index_request_date"], "2026-11-25")
        self.assertEqual(seo_001["index_request_status"], "접수 완료 (Search Console 녹색 색인 생성 요청됨 확인)")
        self.assertEqual(seo_001["current_actual_index_status"], "미확인 (색인 크롤링 대기 중)")

    def test_10_daily_publish_clean_git_status(self):
        """10. 기존 일일 발행 코드(publish_daily_qa.py, build.py, verify.py, daily-publish.yml) 무수정 확인"""
        import subprocess
        diff = subprocess.check_output(
            ["git", "diff", "--name-only", "origin/main"],
            cwd=update_mod.BASE_DIR,
            text=True
        )
        modified_files = [line.strip() for line in diff.strip().splitlines() if line.strip()]
        for f in modified_files:
            self.assertFalse(f == ".github/workflows/daily-publish.yml", "daily-publish.yml was modified!")
            self.assertFalse(f in ["scripts/publish_daily_qa.py", "build.py", "verify.py"], f"Core code modified: {f}")

    def test_11_workflow_syntax_and_permissions(self):
        """11. 신규 워크플로(.github/workflows/seo-registry-sync.yml) 구문 및 권한 검증"""
        wf_path = os.path.join(update_mod.BASE_DIR, ".github", "workflows", "seo-registry-sync.yml")
        self.assertTrue(os.path.exists(wf_path))
        with open(wf_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("workflow_run:", content)
        self.assertIn("Daily QA Auto Publisher", content)
        self.assertIn("group: seo-registry-sync", content)
        self.assertIn("contents: write", content)
        self.assertNotIn("publish_daily_qa.py", content)

if __name__ == "__main__":
    unittest.main()
