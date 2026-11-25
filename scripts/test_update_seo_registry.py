import os
import sys
import shutil
import csv
import json
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scripts.update_seo_registry as update_mod

class TestSeoRegistryPhase2A(unittest.TestCase):
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

    def test_01_existing_ids_and_seo001_preservation(self):
        """Test 1: 기존 29개 관리번호 및 SEO-001 접수 기록 완전 보존 확인"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        self.assertEqual(len(records), 29)
        seo_001 = next(r for r in records if r["registry_id"] == "SEO-001")
        self.assertEqual(seo_001["index_request_date"], "2026-11-25")
        self.assertEqual(seo_001["index_request_status"], "접수 완료 (Search Console 녹색 색인 생성 요청됨 확인)")
        self.assertEqual(seo_001["current_actual_index_status"], "미확인 (색인 크롤링 대기 중)")

    def test_02_dry_run_simulation(self):
        """Test 2: --dry-run 옵션 시 실제 파일 수정 없이 시뮬레이션 동작 확인"""
        mtime_csv_before = os.path.getmtime(self.csv_path)
        mtime_json_before = os.path.getmtime(self.json_path)
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
        self.assertEqual(os.path.getmtime(self.csv_path), mtime_csv_before)
        self.assertEqual(os.path.getmtime(self.json_path), mtime_json_before)

    def test_03_mock_single_new_live_item_max_id_plus_1(self):
        """Test 3: 신규 live 1건 발생 시 max_id + 1 (SEO-030) 채번 검증 (len+1 사용 금지)"""
        mock_slug = "test-new-swing-technique"
        mock_url = f"{update_mod.BASE_URL}/questions/{mock_slug}.html"
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK101", "test-cat", "테스트 스윙 기술", "배우기", mock_slug, "live", "P1", "공식협회", "2026-11-26", "30", "2026-11-26", mock_url])
        
        with open(os.path.join(self.questions_dir, f"{mock_slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "기본자세", "app_menu": "배우기", "sources": ["대한탁구협회"], "answer": "테스트 답변"}, f)

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
        self.assertEqual(new_rec["content_id"], "MOCK101")
        self.assertEqual(new_rec["discipline"], "기본자세")

    def test_04_rerun_duplicate_prevention(self):
        """Test 4: 동일 상태에서 반복 실행 시 0건 추가 및 무중복 보장"""
        res1 = update_mod.update_registry(
            dry_run=False,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        res2 = update_mod.update_registry(
            dry_run=False,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res1["added"], 0)
        self.assertEqual(res2["added"], 0)
        self.assertEqual(res2["total"], 29)

    def test_05_mock_batch_recovery_two_items(self):
        """Test 5: 2건 이상 신규 원고 발생 시 순차 고유번호 부여 (SEO-030, SEO-031)"""
        slugs = ["test-batch-1", "test-batch-2"]
        mock_urls = {f"{update_mod.BASE_URL}/questions/{s}.html" for s in slugs}
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK102", "cat1", "배치 테스트 1", "맞춤진단", slugs[0], "live", "P1", "", "2026-11-26", "30", "2026-11-26", f"{update_mod.BASE_URL}/questions/{slugs[0]}.html"])
            writer.writerow(["MOCK103", "cat2", "배치 테스트 2", "맞춤진단", slugs[1], "live", "P1", "", "2026-11-27", "31", "2026-11-27", f"{update_mod.BASE_URL}/questions/{slugs[1]}.html"])

        for s in slugs:
            with open(os.path.join(self.questions_dir, f"{s}.json"), "w", encoding="utf-8") as f:
                json.dump({"discipline": "드라이브", "app_menu": "맞춤진단", "answer": "답변"}, f)

        res = update_mod.update_registry(
            dry_run=False,
            check_network=False,
            mock_sitemap_urls=mock_urls,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res["added"], 2)
        records = update_mod.load_registry(self.csv_path, self.json_path)
        r1 = next(r for r in records if r["slug"] == slugs[0])
        r2 = next(r for r in records if r["slug"] == slugs[1])
        self.assertEqual(r1["registry_id"], "SEO-030")
        self.assertEqual(r2["registry_id"], "SEO-031")

    def test_06_block_unreleased_articles(self):
        """Test 6: 사이트맵에 없는 미공개(ready, planned, hold) 원고 자동 유입 원천 차단 검증"""
        unreleased_slugs = [("slug-ready", "ready"), ("slug-planned", "planned"), ("slug-hold", "hold")]
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            for s, st in unreleased_slugs:
                writer.writerow(["MOCK999", "cat", "미공개 글", "기타", s, st, "P2", "", "", "", "", ""])
                with open(os.path.join(self.questions_dir, f"{s}.json"), "w", encoding="utf-8") as qf:
                    json.dump({"discipline": "기타"}, qf)

        res = update_mod.update_registry(
            dry_run=False,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res["added"], 0)
        self.assertEqual(res["total"], 29)

    def test_07_network_failure_handling(self):
        """Test 7: check_network 활성화 시 사이트맵 미응답/오류 URL 등록 보류 처리"""
        slug = "non-existent-network-slug"
        with open(self.plan_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["MOCK104", "cat", "미배포 글", "기타", slug, "live", "P1", "", "2026-11-26", "30", "2026-11-26", ""])
        with open(os.path.join(self.questions_dir, f"{slug}.json"), "w", encoding="utf-8") as f:
            json.dump({"discipline": "기타"}, f)

        res = update_mod.update_registry(
            dry_run=False,
            check_network=True,
            csv_path=self.csv_path,
            json_path=self.json_path,
            plan_path=self.plan_path,
            questions_dir=self.questions_dir
        )
        self.assertEqual(res["added"], 0)
        self.assertEqual(res["deferred"], 1)

    def test_08_csv_json_synchronization_and_encoding(self):
        """Test 8: CSV(utf-8-sig) 및 JSON(utf-8) 데이터 일치성 및 인코딩 무결성 검증"""
        with open(self.csv_path, "rb") as f:
            header_bytes = f.read(3)
            self.assertEqual(header_bytes, b'\xef\xbb\xbf', "CSV must have UTF-8 BOM")

        with open(self.csv_path, "r", encoding="utf-8-sig") as f:
            csv_rows = list(csv.DictReader(f))
        with open(self.json_path, "r", encoding="utf-8") as f:
            json_rows = json.load(f)

        self.assertEqual(len(csv_rows), len(json_rows))
        for c_row, j_row in zip(csv_rows, json_rows):
            self.assertEqual(c_row["registry_id"], j_row["registry_id"])
            self.assertEqual(c_row["published_url"], j_row["published_url"])

    def test_09_atomic_save_safety(self):
        """Test 9: 원자적 쓰기 기능 확인 및 임시 파일 잔류 없음 검증"""
        records = update_mod.load_registry(self.csv_path, self.json_path)
        update_mod.save_atomic(records, self.csv_path, self.json_path)
        self.assertFalse(os.path.exists(f"{self.csv_path}.tmp"))
        self.assertFalse(os.path.exists(f"{self.json_path}.tmp"))

    def test_10_production_code_clean_git_status(self):
        """Test 10: 기존 자동 발행 코드 및 워크플로우에 변경이 전혀 없음을 확인"""
        import subprocess
        diff = subprocess.check_output(
            ["git", "diff", "--name-only", "origin/main"],
            cwd=update_mod.BASE_DIR,
            text=True
        )
        modified_files = [line.strip() for line in diff.strip().splitlines() if line.strip()]
        for f in modified_files:
            self.assertFalse(f == ".github/workflows/daily-publish.yml", "daily-publish.yml was modified!")
            self.assertFalse(f in ["scripts/publish_daily_qa.py", "build.py", "verify.py"], f"Core script changed: {f}")

if __name__ == "__main__":
    unittest.main()
