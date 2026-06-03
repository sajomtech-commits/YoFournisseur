# YoFournisseur 🏪

Dashboard de monitoring pour fournisseurs Yupoo / Zhidian. Scraping automatique quotidien, catalogue visuel avec photos, catégories et marqueurs de nouveauté.

## Architecture

```
YoFournisseur/
├── index.html           ← SPA frontend (GitHub Pages)
├── data/
│   └── products.json    ← Données scrapées (générées par cron)
├── scripts/
│   └── scrape.py        ← Scraper fournisseurs → data/products.json
└── README.md
```

## Fonctionnalités

- 📸 **Catalogue visuel** — grille de produits avec photos, triés par fournisseur
- 🔍 **Recherche & Filtres** — par nom, fournisseur, catégorie
- ⭐ **Badge NEW** — repère les nouveaux articles automatiquement
- 🏪 **12 fournisseurs** — maillots, training, accessoires, NBA, etc.
- 🔐 **Accès protégé** — login par mot de passe hashé
- 📱 **Responsive** — mobile et desktop

## Fournisseurs suivis

| Fournisseur | Type | URL |
|------------|------|-----|
| Jersey Dong | Maillot concept | junhaoqiumi.x.yupoo.com |
| Ronaldo97 | Enfants | ronaldo97.x.zhidian-inc.cn |
| Baocheng | Maillot joueurs | baocheng3f888.x.zhidian-inc.cn |
| Classic Football | Maillot classique | classic-football-fhirts052.x.yupoo.com |
| TZ Sports | Ensemble classique | tz583276982.x.yupoo.com |
| Dongshan Sports | Training adultes | dongshanstore.x.yupoo.com |
| Xunmei | Accessoires foot | xunmei.x.yupoo.com |
| AX2084 | Training enfants | x.yupoo.com/photos/ax2084 |
| AAAA Jersey | Habit Foot complet | aaaajersey.x.yupoo.com |
| AAAA Bull | Baskets | aaaabull.x.yupoo.com |
| OK Jersey | Basketball/Rugby/F1 | okjersey.x.yupoo.com |
| Taurus Reps | Vêtements | deateath.x.yupoo.com |

## Usage

### Scraper manuel
```bash
python3 scripts/scrape.py
```

### Scraper automatique (cron Hermes)
Le cron est configuré pour tourner tous les jours à 9h (heure française).

## Tech Stack

- Frontend : Vanilla JS SPA — 1 fichier HTML
- Données : JSON statique (GitHub Pages) + Supabase (optionnel)
- Scraping : Python + curl
- Hébergement : GitHub Pages
- Auth : SHA-256 hash (Web Crypto API) + sessionStorage

## Déploiement

```bash
git push origin main
# → https://sajomtech-commits.github.io/YoFournisseur/
```
