#!/usr/bin/env python3
"""
YoFournisseur Scraper V2 — Scrape + download images
Produit: data/products.json + images/photos/ (fichiers locaux pour GitHub Pages)
"""
import re, json, os, time, hashlib, sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# === CONFIG ===
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")
IMG_DIR = os.path.join(OUTPUT_DIR, "data", "images")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

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

MAX_IMAGES = 120  # Max total images  
MAX_IMG_PER_SUPPLIER = 5  # Max images per supplier
MAX_PROD_PER_SUPPLIER = 10  # Max products per supplier
IMAGE_RETENTION_DAYS = 7   # Delete images older than this

def fetch(url, timeout=20):
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

def download_image(url, output_path, max_retries=2):
    """Download image with proper referer, return True on success"""
    # Force .jpg extension even if source is .jpeg
    original_path = output_path
    if output_path.endswith('.jpeg'):
        output_path = output_path.replace('.jpeg', '.jpg')
    referer = "https://dongshanstore.x.yupoo.com/"
    if "zhidian" in url:
        referer = "https://ronaldo97.x.zhidian-inc.cn/"
    
    for attempt in range(max_retries):
        req = Request(url, headers={
            "User-Agent": UA,
            "Referer": referer,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        })
        try:
            with urlopen(req, timeout=20) as resp:
                data = resp.read()
                if len(data) < 1000:
                    return False  # Too small = error page
                with open(output_path, "wb") as f:
                    f.write(data)
                return True
        except Exception as e:
            if attempt == max_retries - 1:
                return False
            time.sleep(1)
    return False

def get_image_hash(url):
    """Get a stable short hash for a URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def detect_category(title, default_desc):
    if "短袖" in title or "training" in title.lower():
        return "Maillot Training"
    elif "长袖" in title or "long" in title.lower():
        return "Training Manches Longues"
    elif "夹克" in title or "jacket" in title.lower() or "hood" in title.lower():
        return "Veste / Hoodie"
    elif "风衣" in title:
        return "Coupe-Vent"
    elif "POLO" in title or "polo" in title.lower():
        return "Polo"
    elif "背心" in title:
        return "Gilet / Débardeur"
    elif "棉衣" in title:
        return "Doudoune"
    elif "NBA" in title:
        return "NBA"
    elif "童装" in title or "kids" in title.lower():
        return "Enfants"
    elif "尺寸" in title or "size" in title.lower():
        return "Guide des Tailles"
    elif "篮球" in title or "basketball" in title.lower():
        return "Basketball"
    elif "鞋" in title or "chaussure" in title.lower() or "shoe" in title.lower():
        return "Chaussures"
    return default_desc

def scrape_supplier(supplier):
    """Scrape a supplier and download images — only keep products WITH images"""
    print(f"\n🔍 {supplier['name']} ({supplier['url']})")
    html = fetch(supplier["url"])
    if not html:
        print("    ❌ No HTML fetched")
        return []
    
    products = []
    seen_titles = set()
    
    # Extract ALL image URLs from data-src AND src= attributes
    imgs = re.findall(
        r'(?:data-src|src)="(https://photo\.yupoo\.com/[^"]+/(?:medium|small)\.[a-z]+)"',
        html
    )
    # Extract titles
    titles = re.findall(r'title="([^"]+)"', html)
    
    skip_titles = {"dongshanstore", "deateath", "进入后台", "前一页", "后一页", "加密相册"}
    product_titles = [t for t in titles if t not in skip_titles and len(t) > 5]
    
    # Also extract from Zhidian format
    if "zhidian-inc" in supplier["url"]:
        items = re.findall(r'data-title="([^"]*)"[^>]*(?:data-src|src)="([^"]*)"', html)
        for title, img_url in items:
            if title and len(title) > 3 and title not in seen_titles:
                seen_titles.add(title)
                img_hash = get_image_hash(img_url)
                img_filename = f"{supplier['id']}_{img_hash}.jpg"
                img_local_path = f"images/{img_filename}"
                img_abs_path = os.path.join(IMG_DIR, img_filename)
                
                if not os.path.exists(img_abs_path):
                    download_image(img_url, img_abs_path)
                
                if os.path.exists(img_abs_path):
                    cat = detect_category(title, supplier["desc"])
                    ref_match = re.match(r'([A-Z]\d+)#', title)
                    ref = ref_match.group(1) if ref_match else ""
                    
                    products.append({
                        "supplier_id": supplier["id"],
                        "supplier_name": supplier["name"],
                        "ref": ref,
                        "title": title.strip(),
                        "image_url": img_local_path,
                        "category": cat,
                        "url": supplier["url"],
                        "price": None,
                    })
    
    # Standard Yupoo — only keep products where image downloads successfully
    img_count = 0
    for i, title in enumerate(product_titles):
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        if img_count >= MAX_IMG_PER_SUPPLIER:
            break
        
        img_url = imgs[i] if i < len(imgs) else ""
        if img_url and "medium" not in img_url:
            img_url = img_url.replace("/small.jpg", "/medium.jpg")
        
        if not img_url:
            continue
        
        img_hash = get_image_hash(img_url)
        img_filename = f"{supplier['id']}_{img_hash}.jpg"
        img_local_path = f"images/{img_filename}"
        img_abs_path = os.path.join(IMG_DIR, img_filename)
        
        # Download or check if exists
        if not os.path.exists(img_abs_path):
            ok = download_image(img_url, img_abs_path)
            if not ok:
                continue
        
        img_count += 1
        ref_match = re.match(r'([A-Z]\d+)#', title)
        ref = ref_match.group(1) if ref_match else ""
        cat = detect_category(title, supplier["desc"])
        
        products.append({
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "ref": ref,
            "title": title.strip(),
            "image_url": img_local_path,
            "category": cat,
            "url": supplier["url"],
            "price": None,
        })
    
    print(f"    ✅ {len(products)} produits avec image")
    
    # Limit to MAX_PROD_PER_SUPPLIER total
    return products[:MAX_PROD_PER_SUPPLIER]


def clean_old_images():
    """Delete images older than IMAGE_RETENTION_DAYS"""
    if not os.path.exists(IMG_DIR):
        return 0, 0
    
    now = time.time()
    cutoff = now - (IMAGE_RETENTION_DAYS * 86400)
    deleted = 0
    kept = 0
    
    for fname in os.listdir(IMG_DIR):
        fpath = os.path.join(IMG_DIR, fname)
        if not fname.endswith('.jpg'):
            continue
        mtime = os.path.getmtime(fpath)
        if mtime < cutoff:
            os.remove(fpath)
            deleted += 1
        else:
            kept += 1
    
    return deleted, kept


def main():
    print("=" * 60)
    print(f"🏪 YoFournisseur — Scraper V2")
    print(f"📅 {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    all_products = []
    total_imgs = 0
    
    for supplier in SUPPLIERS:
        try:
            products = scrape_supplier(supplier)
            all_products.extend(products)
            time.sleep(0.3)
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Deduplicate
    seen = set()
    unique_products = []
    for p in all_products:
        key = f"{p['supplier_id']}|{p['title']}"
        if key not in seen:
            seen.add(key)
            unique_products.append(p)
    
    # Keep max N per supplier
    from collections import defaultdict
    by_sup = defaultdict(list)
    for p in unique_products:
        by_sup[p['supplier_id']].append(p)
    
    trimmed = []
    total_imgs = 0
    for sid, prods in by_sup.items():
        keep = prods[:MAX_PROD_PER_SUPPLIER]
        trimmed.extend(keep)
        for p in keep:
            if p.get('image_url'):
                total_imgs += 1
    unique_products = trimmed
    
    # Save products.json
    timestamp = datetime.now(timezone.utc).isoformat()
    output = {
        "last_updated": timestamp,
        "total_products": len(unique_products),
        "total_images": total_imgs,
        "suppliers": len(SUPPLIERS),
        "products": unique_products
    }
    
    output_path = os.path.join(DATA_DIR, "products.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Count images on disk
    img_count_disk = len([f for f in os.listdir(IMG_DIR) if f.endswith('.jpg')])
    img_size_mb = sum(os.path.getsize(os.path.join(IMG_DIR, f)) for f in os.listdir(IMG_DIR) if f.endswith('.jpg')) / 1024 / 1024
    
    # Clean old images (retention: 7 days)
    deleted, kept = clean_old_images()
    if deleted > 0:
        print(f"   🧹 Images nettoyées : {deleted} supprimées (>{IMAGE_RETENTION_DAYS} jours)")
    
    print(f"\n{'=' * 60}")
    print(f"✅ Scraping terminé !")
    print(f"   Produits uniques  : {len(unique_products)}")
    print(f"   Images référencées : {total_imgs}")
    print(f"   Images sur disque  : {img_count_disk} ({img_size_mb:.1f} MB)")
    print(f"   Fournisseurs       : {len(SUPPLIERS)}")
    print(f"   Fichier JSON       : {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
