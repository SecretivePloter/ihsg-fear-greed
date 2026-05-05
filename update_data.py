"""
update_data.py
Dijalankan otomatis tiap hari via GitHub Actions.
Google Trends di-fetch di sini (bukan di app) untuk hindari rate limit.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pytrends.request import TrendReq
from datetime import datetime
import os
import time

def hitung_rsi(data, period=14):
    delta     = data.diff()
    naik      = delta.clip(lower=0)
    turun     = -delta.clip(upper=0)
    avg_naik  = naik.ewm(com=period-1, adjust=False).mean()
    avg_turun = turun.ewm(com=period-1, adjust=False).mean()
    rs        = avg_naik / avg_turun
    return 100 - (100 / (1 + rs))

def normalisasi(series, window=90):
    recent  = series.dropna().tail(window)
    min_val = float(recent.min())
    max_val = float(recent.max())
    nilai   = float(series.dropna().iloc[-1])
    if max_val == min_val:
        return 50.0
    return round((nilai - min_val) / (max_val - min_val) * 100, 1)

# ── DOWNLOAD DATA ─────────────────────────────────────────────
print("📥 Downloading IHSG & Rupiah...")
ihsg = yf.download("^JKSE", period="5y", progress=False)
idr  = yf.download("IDR=X", period="5y", progress=False)["Close"].squeeze()
print("✅ IHSG & Rupiah berhasil")

# ── GOOGLE TRENDS ─────────────────────────────────────────────
print("📥 Fetching Google Trends...")
trends_ok = False
try:
    time.sleep(5)
    pytrends = TrendReq(hl='id-ID', tz=420)
    pytrends.build_payload(
        ["IHSG","rupiah","saham","investasi","bursa"],
        timeframe='today 5-y', geo='ID'
    )
    trends_data = pytrends.interest_over_time()
    if 'isPartial' in trends_data.columns:
        trends_data = trends_data.drop(columns=['isPartial'])
    bobot_kw  = {"IHSG":0.30,"rupiah":0.30,"saham":0.20,"investasi":0.15,"bursa":0.05}
    tr_skor   = sum(trends_data[kw]*b for kw,b in bobot_kw.items())
    trends_ok = True
    print("✅ Google Trends berhasil")
except Exception as e:
    print(f"⚠️  Google Trends gagal: {e}")

# ── HITUNG INDIKATOR ──────────────────────────────────────────
close  = ihsg["Close"].squeeze()
volume = ihsg["Volume"].squeeze()
idr_ch = idr.pct_change(10)

ma50     = close.rolling(50).mean()
momentum = (close - ma50) / ma50 * 100
rsi      = hitung_rsi(close)
vol_r    = volume.rolling(5).mean() / volume.rolling(90).mean()
idr_inv  = -idr_ch

s_mom = normalisasi(momentum)
s_rsi = normalisasi(rsi)
s_vol = normalisasi(vol_r)
s_idr = normalisasi(idr_inv)

# Skor trends — ambil dari CSV lama kalau Google Trends gagal
csv_path = "data/historis.csv"
if trends_ok:
    tr_daily = tr_skor.resample("D").ffill()
    tr_align = tr_daily.reindex(close.index, method="ffill")
    s_tr     = normalisasi(tr_align)
else:
    if os.path.exists(csv_path):
        df_ex = pd.read_csv(csv_path, index_col="date", parse_dates=True)
        s_tr  = float(df_ex["s_tr"].dropna().iloc[-1]) if "s_tr" in df_ex.columns and len(df_ex) > 0 else 50.0
        print(f"   Pakai skor trends terakhir dari CSV: {s_tr}")
    else:
        s_tr = 50.0

skor_hari_ini = round(s_mom*0.25 + s_rsi*0.20 + s_vol*0.20 + s_idr*0.20 + s_tr*0.15, 1)
tanggal       = close.index[-1].date()
harga_ihsg    = float(close.iloc[-1])

print(f"\n📊 Skor hari ini ({tanggal}): {skor_hari_ini}")
print(f"   Momentum:{s_mom} | RSI:{s_rsi} | Volume:{s_vol} | Rupiah:{s_idr} | Trends:{s_tr}")

# ── UPDATE CSV ────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
if os.path.exists(csv_path):
    df_hist = pd.read_csv(csv_path, index_col="date", parse_dates=True)
else:
    df_hist = pd.DataFrame(columns=["skor","close","s_mom","s_rsi","s_vol","s_idr","s_tr"])
    df_hist.index.name = "date"

tanggal_ts = pd.Timestamp(tanggal)
baris_baru = {"skor":skor_hari_ini,"close":harga_ihsg,"s_mom":s_mom,"s_rsi":s_rsi,"s_vol":s_vol,"s_idr":s_idr,"s_tr":s_tr}

if tanggal_ts in df_hist.index:
    for k, v in baris_baru.items():
        df_hist.loc[tanggal_ts, k] = v
    print(f"🔄 Data {tanggal} diupdate")
else:
    df_baru = pd.DataFrame(baris_baru, index=pd.DatetimeIndex([tanggal_ts], name="date"))
    df_hist = pd.concat([df_hist, df_baru])
    print(f"➕ Data {tanggal} ditambahkan")

df_hist.sort_index(inplace=True)
df_hist.to_csv(csv_path)
print(f"✅ Selesai! Total {len(df_hist)} hari data tersimpan")