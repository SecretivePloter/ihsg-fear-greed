# IHSG Fear & Greed Index

Static website untuk menampilkan sentimen pasar saham Indonesia dari `data/historis.csv`.

## Kenapa static?

Render Free Web Service akan sleep setelah idle. Versi ini tidak menjalankan server Python untuk pengunjung, sehingga bisa dipasang sebagai Static Site gratis di Render, GitHub Pages, Cloudflare Pages, Netlify, atau Vercel tanpa cold start.

## Struktur

- `index.html` — UI utama dan P&L Generator.
- `assets/app.js` — logika chart, gauge, dan generator gambar.
- `data/historis.csv` — data historis yang dibaca langsung oleh browser.
- `update_data.py` — script update data harian dari GitHub Actions.
- `.github/workflows/update.yml` — update `data/historis.csv` setiap hari bursa.

## Jalankan lokal

```bash
python3 -m http.server 8000
```

Buka `http://localhost:8000`.

## Deploy gratis tanpa sleep

### Render Static Site

Jika memakai `render.yaml`, deploy sebagai Static Site:

- Runtime: `static`
- Build Command: `echo "Static site, no build required"`
- Static Publish Path: `.`

### GitHub Pages

Aktifkan dari repository settings:

1. Buka **Settings → Pages**.
2. Source: **Deploy from a branch**.
3. Branch: `main`, folder `/ (root)`.
4. Save.

GitHub Actions tetap meng-update `data/historis.csv` secara otomatis.
