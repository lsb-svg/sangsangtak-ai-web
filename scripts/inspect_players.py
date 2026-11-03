import json

data = json.loads(open("extracted_app_players.json", encoding="utf-8").read())
print(f"Total players in app data: {len(data)}")

targets = ["신유빈", "장우진", "마롱", "하리모토", "판전둥", "이준상"]
for t in targets:
    found = [p for p in data if t in p["name"]]
    print(f"\n[Target: {t}] (Found {len(found)}):")
    for f in found:
        print(f"  - ID: {f['id']}")
        print(f"    Name: {f['name']}")
        print(f"    Category: {f['category']}")
        print(f"    Blade: {f['blade']} ({f['bladeBrand']})")
        print(f"    FH: {f['forehandRubber']} ({f['forehandBrand']})")
        print(f"    BH: {f['backhandRubber']} ({f['backhandBrand']})")
        print(f"    Grip: {f['gripType']}")
        print(f"    Source: {f['sourceType']} ({f['sourceName']})")
        print(f"    VerifiedAt: {f['verifiedAt']}")

print("\n--- Summary by Category ---")
categories = {}
for p in data:
    cat = p["category"]
    categories[cat] = categories.get(cat, 0) + 1
for cat, cnt in categories.items():
    print(f"  Category '{cat}': {cnt} players")
