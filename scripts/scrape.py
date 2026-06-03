#!/usr/bin/env python3
"""
YoFournisseur Scraper — Scrape les fournisseurs Yupoo/Zhidian
Produit: data/products.json (pour GitHub Pages)
Option: upload Supabase storage
"""
import re, json, os, time, base64
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SUPABASE_URL = ""
SERVICE_KEY = "eyJ0eX...muIk"

SUPABASE_HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json"
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

SUPPLIERS = [
    {"id": "junhaoqiumi", "name": "Jersey Dong", "url": "https://junhaoqiumi.x.yupoo.com/", "desc": "Maillot concept"},
    {"id": "ronaldo97", "name": "Ronaldo97", "url": "https://ronaldo97.x.zhidian-inc.cn/", "desc": "Ensemble enfants maillot"},
    {"id": "baocheng3f888", "name": "Baocheng", "url": "https://baocheng3f888.x.zhidian-inc.cn/", "desc": "Maillot joueurs"},
    {"id": "classic-football", "name": "Classic Football", "url": "https://classic-football-fhirts052.x.yupoo.com/albums", "desc": "Maillot classique"},
    {"id": "tz583276982", "name": "TZ Sports", "url": "https://tz583276982.x.yupoo.com/albums", "desc": "Ensemble classique par equipe"},
    {"id": "dongshanstore", "name": "Dongshan Sports", "url": "https://dongshanstore.x.yupoo.com/albums", "desc": "Training adultes"},
    {"id": "xunmei", "name": "Xunmei", "url": "https://xunmei.x.yupoo.com/albums", "desc": "Accessoires foot"},
    {"id": "ax2084", "name": "AX2084", "url": "https://x.yupoo.com/photos/ax2084/albums", "desc": "Training enfants"},
    {"id": "aaaajersey", "name": "AAAA Jersey", "url": "https://aaaajersey.x.yupoo.com/categories?page=2", "desc": "Habit Foot complet"},
    {"id": "aaaabull", "name": "AAAA Bull", "url": "https://aaaabull.x.yupoo.com/", "desc": "Baskets chaussures"},
    {"id": "okjersey", "name": "OK Jersey", "url": "https://okjersey.x.yupoo.com/", "desc": "Basketball, Rugby, F1"},
    {"id": "taurus-reps", "name": "Taurus Reps", "url": "https://deateath.x.yupoo.com/categories/4571155", "desc": "Vetements"},
]


def fetch(url, timeout=20):
    """Fetch a URL with proper headers"""
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7",
    })
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"    ⚠ FETCH ERROR: {e}")
        return None


def fetch_image(url, timeout=15):
    """Download image with referer header"""
    req = Request(url, headers={
        "User-Agent": UA,
        "Referer": "https://dongshanstore.x.yupoo.com/",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    })
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"    ⚠ IMG ERROR: {e}")
        return None


def scrape_yupoo(supplier):
    """Scrape a Yupoo supplier page and extract products"""
    print(f"\n🔍 {supplier['name']} ({supplier['url']})")
    html = fetch(supplier["url"])
    if not html:
        print("    ❌ No HTML fetched")
        return []
    
    products = []
    seen_titles = set()
    
    # Extract product entries
    # Pattern: title="TITLE..." data-src="https://photo.yupoo.com/..."
    pattern = re.compile(
        r'title="([^"]*)"[^>]*>?\s*(?:.*?data-src="(https://photo\.yupoo\.com/[^/]+/[a-f0-9]+/(?:medium|small)\.jpg)")?',
        re.DOTALL
    )
    
    # Simpler: find all title + img pairs
    titles = re.findall(r'title="([^"]+)"', html)
    imgs = re.findall(r'data-src="(https://photo\.yupoo\.com/[^"]+/(?:medium|small)\.jpg)"', html)
    
    # Filter out non-product titles
    skip_titles = {"dongshanstore", "进入后台", "前一页", "后一页", "加密相册"}
    
    product_titles = [t for t in titles if t not in skip_titles and len(t) > 5]
    
    # Also check for zhidian-inc pattern
    if "zhidian-inc" in supplier["url"]:
        # Different pattern
        items = re.findall(r'data-title="([^"]*)"[^>]*data-src="([^"]*)"', html)
        for title, img_url in items:
            if title and len(title) > 3:
                products.append({
                    "supplier_id": supplier["id"],
                    "supplier_name": supplier["name"],
                    "title": title.strip(),
                    "image_url": img_url,
                    "category": supplier["desc"],
                    "price": None,
                    "currency": "",
                    "url": supplier["url"],
                })
    
    # For standard Yupoo
    # Match titles with images (paired by order)
    for i, title in enumerate(product_titles):
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        img_url = imgs[i] if i < len(imgs) else ""
        if "medium" in img_url:
            img_url_full = img_url
        elif img_url:
            img_url_full = img_url.replace("/small.jpg", "/medium.jpg")
        else:
            img_url_full = ""
        
        # Extract ref number
        ref_match = re.match(r'([A-Z]\d+)#', title)
        ref = ref_match.group(1) if ref_match else ""
        
        # Detect category
        cat = supplier["desc"]
        if "短袖" in title or "training" in title.lower():
            cat = "Maillot Training"
        elif "长袖" in title or "long" in title.lower():
            cat = "Training Manches Longues"
        elif "夹克" in title or "jacket" in title.lower() or "hood" in title.lower():
            cat = "Veste / Hoodie"
        elif "风衣" in title:
            cat = "Coupe-Vent"
        elif "POLO" in title or "polo" in title.lower():
            cat = "Polo"
        elif "背心" in title:
            cat = "Gilet / Débardeur"
        elif "棉衣" in title:
            cat = "Doudoune"
        elif "NBA" in title:
            cat = "NBA"
        elif "童装" in title or "kids" in title.lower():
            cat = "Enfants"
        elif "尺寸" in title or "size" in title.lower():
            cat = "Guide des Tailles"
        
        products.append({
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "ref": ref,
            "title": title.strip(),
            "image_url": img_url_full,
            "category": cat,
            "url": supplier["url"],
            "price": None,
        })
    
    print(f"    ✅ {len(products)} produits trouvés")
    return products


def upload_to_supabase(all_products):
    """Upload products to Supabase products table"""
    if not SUPABASE_URL:
        print("⚠ Supabase URL not configured — skipping upload")
        return
    
    print(f"\n📤 Uploading {len(all_products)} products to Supabase...")
    # Will implement once URL is available


def main():
    print("=" * 60)
    print("🏪 YoFournisseur — Scraper V1")
    print(f"📅 {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    all_products = []
    
    for supplier in SUPPLIERS:
        try:
            products = scrape_yupoo(supplier)
            all_products.extend(products)
            # Be nice to Yupoo servers
            time.sleep(0.5)
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Deduplicate by title per supplier
    seen = set()
    unique_products = []
    for p in all_products:
        key = f"{p['supplier_id']}|{p['title']}"
        if key not in seen:
            seen.add(key)
            unique_products.append(p)
    
    # Save to data.json
    timestamp = datetime.now(timezone.utc).isoformat()
    output = {
        "last_updated": timestamp,
        "total_products": len(unique_products),
        "suppliers": len(SUPPLIERS),
        "products": unique_products
    }
    
    output_path = os.path.join(OUTPUT_DIR, "products.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Scraping terminé !")
    print(f"   Produits uniques : {len(unique_products)}")
    print(f"   Fournisseurs      : {len(SUPPLIERS)}")
    print(f"   Fichier           : {output_path}")
    print(f"{'=' * 60}")
    
    # Upload to Supabase
    upload_to_supabase(unique_products)


if __name__ == "__main__":
    main()
