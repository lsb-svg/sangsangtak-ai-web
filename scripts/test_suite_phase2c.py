import os
import sys
import shutil
import csv
import json
import tempfile
import unittest
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scripts.update_seo_registry as update_mod

class TestPhase2CFinalVerification(unittest.TestCase):
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

    def test_01_total_registry_count_and_sitemap_match(self):
        """1. 최신 실제 공개 사이트맵(29개)과 관리대장(29개) 100% 일치 확인"""
        sitemap_urls = update_mod.fetch_sitemap_urls()
        records = update_mod.load_registry(self.csv_path, self.json_path)
        self.assertEqual(len(sitemap_urls), 29)
        self.assertEqual(len(records), 29)
        reg_urls = {r["published_url"] for r in records}
        self.assertEqual(sitemap_urls, reg_urls)

    def test_02_seo029_attributes_and_discrepancy_tracking(self):
        """2. SEO-029 속성 및 내부 승인 상태 불일치(ready vs 공개 확인) 추적 검증"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        seo_029 = next(r for r in records if r["registry_id"] == "SEO-029")
        self.assertEqual(seo_029["slug"], "largeball-senior-division-classes")
        self.assertEqual(seo_029["content_id"], "C071")
        self.assertEqual(seo_029["question_title"], "라지볼 탁구대회 연령별 참가 자격과 신청 방법은?")
        self.assertEqual(seo_029["actual_publish_status"], "공개 확인")
        self.assertEqual(seo_029["internal_publish_status"], "ready")
        self.assertEqual(seo_029["approval_discrepancy"], "검토 필요")
        self.assertEqual(seo_029["current_actual_index_status"], "미확인")

    def test_03_preservation_of_all_existing_ids_seo001_to_seo028(self):
        """3. 기존 관리번호 SEO-001 ~ SEO-028 및 영구 고유성 100% 보존 확인"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        ids = [r["registry_id"] for r in records]
        expected_ids = [f"SEO-{i:03d}" for i in range(1, 30)]
        self.assertEqual(ids, expected_ids)

    def test_04_seo001_gsc_request_history_preservation(self):
        """4. SEO-001 2026-11-25 색인 요청 접수 이력 완벽 보존 확인"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        seo_001 = next(r for r in records if r["registry_id"] == "SEO-001")
        self.assertEqual(seo_001["index_request_date"], "2026-11-25")
        self.assertEqual(seo_001["index_request_status"], "접수 완료 (Search Console 녹색 색인 생성 요청됨 확인)")
        self.assertEqual(seo_001["current_actual_index_status"], "미확인 (색인 크롤링 대기 중)")

    def test_05_dry_run_and_repeat_run_zero_duplicates(self):
        """5. dry-run 및 반복 실행 시 무중복(0건 추가, 29건 유지) 보장"""
        res1 = update_mod.update_registry(
            dry_run=True,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res1["added"], 0)
        self.assertEqual(res1["existing"], 29)

        res2 = update_mod.update_registry(
            dry_run=False,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res2["added"], 0)
        self.assertEqual(res2["total"], 29)

    def test_06_new_live_auto_discovery_max_id_plus_1(self):
        """6. 신규 live 원고 발생 시 max_id + 1 (SEO-030) 채번 및 일치 등록 검증"""
        mock_slug = "test-phase2c-forehand-drive"
        mock_title = "포어핸드 드라이브 궤적 분석"
        mock_url = f"{update_mod.BASE_URL}/questions/{mock_slug}.html"

        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK999", "기술", mock_title, "배우기", mock_slug, "live", "P1", "공식", "2026-11-26", "30", "2026-11-26", mock_url])

        with open(os.path.join(self.questions_dir, f"{mock_slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "기술", "app_menu": "배우기", "sources": ["대한탁구협회"], "answer": "답변"}, f)

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
        self.assertEqual(res["total"], 30)
        records = update_mod.load_registry(self.csv_path, self.json_path)
        new_rec = next(r for r in records if r["slug"] == mock_slug)
        self.assertEqual(new_rec["registry_id"], "SEO-030")
        self.assertEqual(new_rec["approval_discrepancy"], "일치")

    def test_07_git_push_conflict_safety_exit(self):
        """7. Git Push 충돌 시 강제 Push 금지 및 안전 종료 스크립트 로직 검증"""
        wf_path = os.path.join(update_mod.BASE_DIR, ".github", "workflows", "seo-registry-sync.yml")
        with open(wf_path, "r", encoding="utf-8") as f:
            wf_content = f.read()
        self.assertIn("git pull --rebase origin main ||", wf_content)
        self.assertIn("exit 1", wf_content)
        self.assertNotIn("--force", wf_content)
        self.assertNotIn("-f ", wf_content)

    def test_08_save_failure_atomic_rollback(self):
        """8. 저장 실패 시 기존 CSV 및 JSON 원상 복구 (롤백 주입) 검증"""
        mock_slug = "test-phase2c-rollback"
        mock_url = f"{update_mod.BASE_URL}/questions/{mock_slug}.html"
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK888", "기술", "롤백 검증", "배우기", mock_slug, "live", "P1", "", "2026-11-26", "31", "2026-11-26", mock_url])
        with open(os.path.join(self.questions_dir, f"{mock_slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "기술", "app_menu": "배우기"}, f)

        with self.assertRaises(IOError):
            update_mod.update_registry(
                dry_run=False,
                check_network=False,
                mock_sitemap_urls={mock_url},
                inject_save_failure=True,
                csv_path=self.csv_path,
                json_path=self.json_path,
                plan_path=self.plan_path,
                questions_dir=self.questions_dir
            )
        records = update_mod.load_registry(self.csv_path, self.json_path)
        self.assertEqual(len(records), 29)
        self.assertFalse(os.path.exists(f"{self.csv_path}.tmp"))
        self.assertFalse(os.path.exists(f"{self.json_path}.tmp"))

    def test_09_production_core_files_unmodified(self):
        """9. 기존 핵심 발행 파일(daily-publish.yml, publish_daily_qa.py, build.py, verify.py) 무수정 확인"""
        diff = subprocess.check_output(
            ["git", "diff", "--name-only", "origin/main"],
            cwd=update_mod.BASE_DIR,
            text=True
        )
        modified_files = [line.strip() for line in diff.strip().splitlines() if line.strip()]
        for f in modified_files:
            self.assertFalse(f == ".github/workflows/daily-publish.yml", "daily-publish.yml modified!")
            self.assertFalse(f in ["scripts/publish_daily_qa.py", "build.py", "verify.py"], f"Core code modified: {f}")

    def test_10_csv_json_encoding_and_synchronization(self):
        """10. CSV(utf-8-sig BOM) 및 JSON(utf-8) 1:1 일치 및 무결성 확인"""
        with open(self.csv_path, "rb") as f:
            self.assertEqual(f.read(3), b'\xef\xbb\xbf')
        with open(self.csv_path, "r", encoding="utf-8-sig") as f:
            c_rows = list(csv.DictReader(f))
        with open(self.json_path, "r", encoding="utf-8") as f:
            j_rows = json.load(f)
        self.assertEqual(len(c_rows), len(j_rows))
        for c, j in zip(c_rows, j_rows):
            self.assertEqual(c["registry_id"], j["registry_id"])
            self.assertEqual(c["published_url"], j["published_url"])
            self.assertEqual(c["approval_discrepancy"], j["approval_discrepancy"])

if __name__ == "__main__":
    unittest.main()
