# IHSG Fear & Greed Index

Static website untuk menampilkan sentimen pasar saham Indonesia dari `data/historis.csv`.

## Kenapa static?

Render Free Web Service akan sleep setelah idle. Versi ini tidak menjalankan server Python untuk pengunjung, sehingga bisa dipasang sebagai Static Site gratis di Render, GitHub Pages, Cloudflare Pages, Netlify, atau Vercel tanpa cold start.

## Struktur

- `index.html` — UI utama dan P&L Generator.
- `assets/app.js` — logika chart, gauge, dan generator gambar.
- `data/historis.csv` — data historis yang dibaca langsung oleh browser.
- `update_data.py` — script update data otomatis dari GitHub Actions.
- `.github/workflows/update.yml` — update `data/historis.csv` tiap jam saat hari bursa.
- `package.json` — build script untuk platform seperti Vercel/Render.

## Jalankan lokal

```bash
python3 -m http.server 8000
```

Buka `http://localhost:8000`.

Untuk mengecek output build:

```bash
npm run build
python3 -m http.server 8000 --directory public
```

## Deploy gratis tanpa sleep

### Render Static Site

Jika memakai `render.yaml`, deploy sebagai Static Site:

- Runtime: `static`
- Build Command: `npm run build`
- Static Publish Path: `./public`

### GitHub Pages

Aktifkan dari repository settings:

1. Buka **Settings → Pages**.
2. Source: **Deploy from a branch**.
3. Branch: `main`, folder `/ (root)`.
4. Save.

GitHub Actions tetap meng-update `data/historis.csv` secara otomatis.

## Jadwal update data

GitHub Actions menjalankan update setiap hari kerja Senin–Jumat, tiap jam dari 10:00 sampai 17:00 WIB. Jika Google Trends gagal atau terkena limit, script tetap memperbarui indikator IHSG, volume, RSI, dan USD/IDR, lalu memakai skor Google Trends terakhir dari CSV sampai fetch berikutnya berhasil.
