#!/usr/bin/env python3
"""
Inspect and extract Star Player and Equipment data from the original STAI app.
READ-ONLY operations on external paths.
"""
from pathlib import Path
import re
import json

APP_PATH = Path(r"C:\STAI_WORK_20261019")
STAR_PLAYER_FILE = APP_PATH / "src" / "data" / "starPlayerData.ts"
EQUIPMENT_REGISTRY_FILE = APP_PATH / "src" / "data" / "starPlayerEquipmentRegistry.ts"

def parse_star_players():
    if not STAR_PLAYER_FILE.exists():
        print(f"File not found: {STAR_PLAYER_FILE}")
        return []
    
    content = STAR_PLAYER_FILE.read_text(encoding="utf-8")
    
    # Split by player object delimiters
    pattern = re.compile(
        r"\{\s*id:\s*['\"](?P<id>[^'\"]+)['\"],\s*"
        r"name:\s*['\"](?P<name>[^'\"]+)['\"],"
        r".*?category:\s*['\"](?P<category>[^'\"]+)['\"],"
        r".*?equipment:\s*\{(?P<equipment>.*?)\},"
        r".*?sourceType:\s*['\"](?P<sourceType>[^'\"]+)['\"],"
        r".*?sourceName:\s*['\"](?P<sourceName>[^'\"]+)['\"],"
        r".*?verifiedAt:\s*['\"](?P<verifiedAt>[^'\"]+)['\"]",
        re.DOTALL
    )
    
    players = []
    for match in pattern.finditer(content):
        p_id = match.group("id")
        p_name = match.group("name")
        p_category = match.group("category")
        p_eq_raw = match.group("equipment")
        p_source_type = match.group("sourceType")
        p_source_name = match.group("sourceName")
        p_verified_at = match.group("verifiedAt")
        
        # Extract playStyle, division, teamOrRegion if present
        play_style_m = re.search(r"playStyle:\s*['\"]([^'\"]+)['\"]", match.group(0))
        division_m = re.search(r"division:\s*['\"]([^'\"]+)['\"]", match.group(0))
        team_m = re.search(r"teamOrRegion:\s*['\"]([^'\"]+)['\"]", match.group(0))
        
        # Extract equipment details
        blade_m = re.search(r"blade:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        blade_brand_m = re.search(r"bladeBrand:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        fh_m = re.search(r"forehandRubber:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        fh_brand_m = re.search(r"forehandBrand:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        bh_m = re.search(r"backhandRubber:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        bh_brand_m = re.search(r"backhandBrand:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        grip_m = re.search(r"gripType:\s*['\"]([^'\"]+)['\"]", p_eq_raw)
        
        players.append({
            "id": p_id,
            "name": p_name,
            "category": p_category,
            "division": division_m.group(1) if division_m else "",
            "teamOrRegion": team_m.group(1) if team_m else "",
            "playStyle": play_style_m.group(1) if play_style_m else "",
            "blade": blade_m.group(1) if blade_m else "",
            "bladeBrand": blade_brand_m.group(1) if blade_brand_m else "",
            "forehandRubber": fh_m.group(1) if fh_m else "",
            "forehandBrand": fh_brand_m.group(1) if fh_brand_m else "",
            "backhandRubber": bh_m.group(1) if bh_m else "",
            "backhandBrand": bh_brand_m.group(1) if bh_brand_m else "",
            "gripType": grip_m.group(1) if grip_m else "",
            "sourceType": p_source_type,
            "sourceName": p_source_name,
            "verifiedAt": p_verified_at,
        })
    
    return players

if __name__ == "__main__":
    players = parse_star_players()
    print(f"Total players parsed: {len(players)}")
    for p in players:
        print(f" - [{p['category']}] {p['name']} | Blade: {p['blade']} | FH: {p['forehandRubber']} | BH: {p['backhandRubber']} | Source: {p['sourceType']} ({p['sourceName']}, {p['verifiedAt']})")
    
    out_file = Path("extracted_app_players.json")
    out_file.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved to {out_file.resolve()}")
