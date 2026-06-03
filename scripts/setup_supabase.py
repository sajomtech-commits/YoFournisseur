#!/usr/bin/env python3
"""Setup Supabase bucket yofournisseur + upload test"""
import subprocess, json, base64, re, os

# Get key
with open("/workspace/budget/index.html") as f:
    src = f.read()
m = re.search(r"SUPABASE_KEY = '([^']+)'", src)
key_raw = m.group(1)
try:
    key = base64.b64decode(key_raw).decode()
except:
    key = key_raw

BASE = "https://supabase.sagetech.vip"
AUTH = f"Authorization: Bearer {key}"
C = ["curl", "-sk", "--max-time", "15", "-H", f"apikey: {key}", "-H", AUTH]

# 1. List buckets
print("📦 Vérification des buckets...")
r = subprocess.run(C + [f"{BASE}/storage/v1/bucket"], capture_output=True, text=True, timeout=20)
print(f"   Status: {r.returncode}")
bs = r.stdout.strip()
if bs:
    try:
        buckets = [b["name"] for b in json.loads(bs)]
        print(f"   Buckets: {buckets}")
        if "yofournisseur" in buckets:
            print("   ✅ 'yofournisseur' existe déjà")
        else:
            r2 = subprocess.run(C + ["-X", "POST", "-H", "Content-Type: application/json",
                "-d", json.dumps({"name":"yofournisseur","public":True}),
                f"{BASE}/storage/v1/bucket"], capture_output=True, text=True, timeout=20)
            print(f"   Création: {r2.stdout[:200]}")
    except:
        print(f"   Brut: {bs[:200]}")
else:
    print(f"   Stderr: {r.stderr[:200]}")

# 2. Upload one test image
print("\n📤 Upload test...")
img = "/workspace/YoFournisseur/data/images/junhaoqiumi_208fa96898d2.jpg"
if os.path.exists(img):
    with open(img, "rb") as f:
        data = f.read()
    r = subprocess.run(C + ["-X", "PUT", "-H", "Content-Type: image/jpeg",
        f"{BASE}/storage/v1/object/yofournisseur/test.jpg"],
        input=data, capture_output=True, timeout=20)
    print(f"   Upload: {r.returncode}, {r.stdout[:200] if r.stdout else r.stderr[:200]}")
else:
    print(f"   Fichier manquant: {img}")

# 3. Public URL
print("\n🔗 URL publique test:")
print(f"   {BASE}/storage/v1/object/public/yofournisseur/test.jpg")
r = subprocess.run(["curl", "-sk", "--max-time", "10",
    f"{BASE}/storage/v1/object/public/yofournisseur/test.jpg"], 
    capture_output=True, timeout=15)
print(f"   HTTP: file de sortie, {len(r.stdout)} bytes")
