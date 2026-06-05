#!/usr/bin/env python3
"""
yoMayssa Scraper — Scrape Dongshan + Jersey Dong + JetLife Fashion
"""
import re, json, os, time, hashlib, subprocess
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")
IMG_DIR = os.path.join(OUTPUT_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"

SUPPLIERS = [
    {
        "id": "dongshan",
        "name": "Dongshan Sports",
        "url": "https://dongshanstore.x.yupoo.com/categories",
        "whatsapp": "",
        "whatsapp_name": "",
        "desc": "Training sportif — adultes",
        "categories": [
            # All categories from the page
            ("322332", "Short Sleeve Training"),
            ("322331", "Long-sleeved Training"),
            ("322329", "Jacket"),
            ("347310", "Hoodie Long Zip"),
            ("4912757", "Hoodie Half Zip"),
            ("5109931", "Windbreaker"),
            ("817047", "Cotton Padded"),
            ("4932378", "Trench Coat"),
            ("4912753", "Vest Set"),
            ("653120", "Polo"),
            ("322330", "Kids"),
            ("3217172", "NBA Winter"),
            ("4540246", "New Models 2425"),
            ("3498460", "NBA Jerseys"),
            ("479733", "Size Chart"),
        ]
    },
    {
        "id": "jerseydong",
        "name": "Jersey Dong",
        "url": "https://junhaoqiumi.x.yupoo.com/",
        "whatsapp": "+861****5009",
        "whatsapp_name": "Jersey Dong",
        "desc": "Maillots concept",
        "categories": []
    },
    {
        "id": "aaaajersey",
        "name": "AAAA Jersey",
        "url": "https://aaaajersey.x.yupoo.com/categories?page=2",
        "whatsapp": "",
        "whatsapp_name": "",
        "desc": "Habit Foot complet",
        "categories": []
    },
    {
        "id": "jetlife",
        "name": "0832CLUB (JetLife)",
        "url": "http://www.jetlifefashion.com/",
        "whatsapp": "",
        "whatsapp_name": "",
        "desc": "Marques streetwear/luxe — 21k+ produits",
        "categories": []
    },
]

MAX_PER_CATEGORY = 20
MAX_TOTAL = 50

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
        return None

def download_image(url, output_path):
    try:
        req = Request(url, headers={
            "User-Agent": UA,
            "Referer": "https://dongshanstore.x.yupoo.com/",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        })
        with urlopen(req, timeout=20) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False
            with open(output_path, "wb") as f:
                f.write(data)
            return True
    except:
        return False

def download_image_static(url):
    """Download image without supplier-specific Referer"""
    try:
        req = Request(url, headers={
            "User-Agent": UA,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        })
        with urlopen(req, timeout=20) as resp:
            data = resp.read()
            if len(data) < 1000:
                return None
            return data
    except:
        return None


def get_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


# Catégories déduites du nom du produit (patterns)
JETLIFE_CATEGORY_MAP = [
    (r"HOODIE|SWEATSHIRT|CREWNECK|ZIP\s*UP|SWEAT", "HOODIE/SWEATER"),
    (r"JACKET|COAT|BOMBER|PUFFER|VARSITY|TRACK\s*TOP|WINDBREAKER|SHELL", "COAT/JACKET"),
    (r"TEE|T-SHIRT|TEE-SHIRT|SHIRT", "T-SHIRT/SHIRT"),
    (r"PANT|JEANS|CARGO|TROUSER|SWEATPANT|JOGGER|LEGGING|CHINO", "PANT/JEANS"),
    (r"SHORT|BERMUDA", "SHORT"),
    (r"CAP|HAT|BEANIE|BUCKET|VISOR|SNAPBACK", "HAT/CAP"),
    (r"SHOE|SNEAKER|TRAINER|BOOT|SLIDE|SANDAL|LOAFER", "SHOES"),
    (r"BAG|BACKPACK|DUFFLE|TOTE|WAIST\s*BAG|CROSSBODY", "BAG"),
    (r"VEST|GILET|WAISTCOAT", "VEST"),
    (r"DRESS|SKIRT", "Women's Dress"),
    (r"POLO", "POLO"),
    (r"FLEECE", "FLEECE"),
    (r"DOWN\s*JACKET|COTTON\s*JACKET|PUFFER|DOWN\s*VEST", "DOWN JACKET"),
    (r"SOCK", "SOCK"),
    (r"GLOVE", "GLOVES"),
    (r"SCARF", "SCARF"),
    (r"GLASSES|SUNGLASSES|EYEWEAR", "GLASSES"),
    (r"TOY|PLUSH|FIGURE|BEAR|DOLL", "TOYS"),
    (r"JEWELRY|RING|NECKLACE|BRACELET|CHAIN|PENDANT", "JEWELRY"),
    (r"FOOTBALL|SOCCER|JERSEY|KIT", "FOOTBALL"),
    (r"NBA|BASKETBALL", "NBA"),
    (r"NFL|FOOTBALL\s*JERSEY", "NFL"),
    (r"MLB|BASEBALL", "MLB"),
    (r"ROCK|ROLL|BAND|MUSIC|CONCERT", "ROCK N ROLL"),
    (r"DIGITAL|PHONE|CASE|CHARGER|HEADPHONE|EARPHONE|SPEAKER", "Digital Products"),
    (r"BRA|UNDERWEAR|BRIEF|BOXER|PANTY|LINGERIE|UNDERPANTS", "UNDERPANTS"),
    (r"BELT", "OTHERS"),
]


def guess_jetlife_category(name):
    """Déduit la catégorie d'un produit JetLife depuis son nom"""
    name_upper = name.upper()
    for pattern, category in JETLIFE_CATEGORY_MAP:
        if re.search(pattern, name_upper):
            return category
    return "AUTRE"


def scrape_jetlife(supplier_id, max_total=50):
    """Scrape les 50 derniers produits de JetLife Fashion via API REST"""
    base = "http://www.jetlifefashion.com/api"
    headers = {"User-Agent": UA, "Accept": "application/json"}
    products = []
    seen = set()

    # 1. Récupérer les catégories JetLife pour référence
    cat_map = {}
    try:
        req = Request(f"{base}/category/getOptions", headers=headers)
        with urlopen(req, timeout=10) as resp:
            cats_data = json.loads(resp.read().decode())
            for c in cats_data.get("data", {}).get("list", []):
                cat_map[c["id"]] = c["name"]
    except:
        pass  # On utilisera le guess si l'API catégorie ne répond pas

    # 2. Récupérer les 50 derniers produits (triés par createdAt)
    url = f"{base}/album/getList?pageIndex=1&pageSize={max_total}"
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return []

    items = data.get("data", {}).get("list", [])
    if not items:
        print(f"   ❌ No items returned")
        return []

    print(f"   📦 {len(items)} produits récupérés")

    for item in items:
        pid = item.get("id")
        name = item.get("name", "").strip()
        cover = item.get("cover", "")
        price = item.get("price", 0)
        currency = item.get("cSymbol", "$")
        cprice = item.get("cPrice", 0)
        created = item.get("createdAt", "")

        if not name or not cover:
            continue

        # Déduire la catégorie depuis le nom
        category = guess_jetlife_category(name)

        # Télécharger l'image cover
        img_url = f"http://www.jetlifefashion.com/{cover}"
        img_hash = get_hash(img_url)
        img_filename = f"{supplier_id}_{img_hash}.jpg"
        img_local = f"images/{img_filename}"
        img_abs = os.path.join(IMG_DIR, img_filename)

        if not os.path.exists(img_abs):
            img_data = download_image_static(img_url)
            if img_data:
                with open(img_abs, "wb") as f:
                    f.write(img_data)
            else:
                continue

        # Deduplicate
        if img_local in seen:
            continue
        seen.add(img_local)

        products.append({
            "supplier_id": supplier_id,
            "supplier_name": "0832CLUB (JetLife)",
            "ref": str(pid),
            "title": name,
            "category": category,
            "image_url": img_local,
            "price": price,
            "currency": currency,
            "cPrice": cprice,
        })

    print(f"   ✅ {len(products)} articles avec image")
    return products[:max_total]

def scrape_category(supplier_id, cat_id, cat_name):
    """Scrape a single category page"""
    url = f"https://dongshanstore.x.yupoo.com/categories/{cat_id}"
    html = fetch(url)
    if not html:
        return []
    
    titles = re.findall(r'title="([^"]+)"', html)
    imgs = re.findall(r'(?:data-src|src)="(https://photo\.yupoo\.com/[^"]+/(?:medium|small)\.[a-z]+)"', html)
    
    skip = {"dongshanstore", "进入后台", "前一页", "后一页", "加密相册"}
    product_titles = [t for t in titles if t not in skip and len(t) > 5]
    
    products = []
    seen = set()
    img_count = 0
    
    for i, title in enumerate(product_titles):
        if title in seen:
            continue
        seen.add(title)
        
        if img_count >= MAX_PER_CATEGORY:
            break
        if len(products) >= MAX_TOTAL:
            break
        
        img_url = imgs[i] if i < len(imgs) else ""
        if not img_url:
            continue
        
        if "medium" not in img_url:
            img_url = img_url.replace("/small.jpg", "/medium.jpg")
        
        img_hash = get_hash(img_url)
        img_filename = f"{supplier_id}_{img_hash}.jpg"
        img_local = f"images/{img_filename}"
        img_abs = os.path.join(IMG_DIR, img_filename)
        
        if not os.path.exists(img_abs):
            ok = download_image(img_url, img_abs)
            if not ok:
                continue
        
        img_count += 1
        
        ref = ""
        m = re.match(r'([A-Z]\d+)#', title)
        if m:
            ref = m.group(1)
        
        products.append({
            "supplier_id": supplier_id,
            "supplier_name": "Dongshan Sports",
            "ref": ref,
            "title": title.strip(),
            "category": cat_name,
            "image_url": img_local,
            "price": None,
            "currency": "",
        })
    
    return products


def scrape_supplier(supplier):
    """Scrape a supplier (Dongshan = all categories, Jersey Dong = main page)"""
    print(f"\n🔍 {supplier['name']}")
    
    if supplier["id"] == "dongshan":
        # Scrape each category
        all_products = []
        seen_urls = set()
        
        for cat_id, cat_name in supplier["categories"]:
            print(f"   📂 {cat_name}...", end=" ", flush=True)
            products = scrape_category(supplier["id"], cat_id, cat_name)
            print(f"{len(products)} articles")
            
            for p in products:
                key = p["image_url"]
                if key and key not in seen_urls:
                    seen_urls.add(key)
                    all_products.append(p)
            
            if len(all_products) >= MAX_TOTAL:
                break
            time.sleep(0.5)
        
        print(f"   ✅ Total: {len(all_products)} articles avec image")
        return all_products[:MAX_TOTAL]
    
    elif supplier["id"] == "jetlife":
        # JetLife — via API REST
        return scrape_jetlife(supplier["id"], MAX_TOTAL)
    
    else:
        # Jersey Dong — just contacts, no scraping
        return []


def main():
    print("=" * 60)
    print("📦 yoMayssa — Scraper")
    print(f"📅 {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    all_products = []
    
    for supplier in SUPPLIERS:
        try:
            prods = scrape_supplier(supplier)
            all_products.extend(prods)
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Save JSON
    ts = datetime.now(timezone.utc).isoformat()
    output = {
        "last_updated": ts,
        "total_products": len(all_products),
        "suppliers": [
            {
                "id": s["id"],
                "name": s["name"],
                "url": s["url"],
                "whatsapp": s["whatsapp"],
                "whatsapp_name": s["whatsapp_name"],
                "desc": s["desc"],
            }
            for s in SUPPLIERS
        ],
        "products": all_products
    }
    
    with open(os.path.join(DATA_DIR, "products.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Stats
    img_count = len([f for f in os.listdir(IMG_DIR) if f.endswith('.jpg')])
    img_size = sum(os.path.getsize(os.path.join(IMG_DIR, f)) for f in os.listdir(IMG_DIR) if f.endswith('.jpg')) / 1024 / 1024
    
    print(f"\n{'=' * 60}")
    print(f"✅ Scraping terminé !")
    print(f"   Produits : {len(all_products)}")
    print(f"   Images   : {img_count} ({img_size:.1f} MB)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
