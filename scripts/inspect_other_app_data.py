from pathlib import Path
import re

app_data = Path(r"C:\STAI_WORK_20261019\src\data")

files = [
    "rankingData.ts",
    "tournamentData.ts",
    "largeBallEquipmentData.ts",
    "largeBallTournamentData.ts",
    "largeBallLearningData.ts",
    "equipmentRecommendationData.ts",
    "paraRankingData.ts",
    "paraTournamentData.ts"
]

print("=== INSPECTING APP DATA FILES ===")
for fname in files:
    fpath = app_data / fname
    if fpath.exists():
        text = fpath.read_text(encoding="utf-8")
        print(f"\n[{fname}] Size: {len(text)} bytes, Lines: {len(text.splitlines())}")
        # Print first 20 lines
        for i, line in enumerate(text.splitlines()[:15]):
            print(f"  {line}")
    else:
        print(f"\n[{fname}] NOT FOUND")
