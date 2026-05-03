"""
update_data.py
Dijalankan otomatis tiap hari via GitHub Actions.
Tugasnya: hitung skor Fear & Greed hari ini dan append ke historis.csv
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pytrends.request import TrendReq
from datetime import datetime, timedelta
import os

# ── HELPERS ──────────────────────────────────────────────────
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

# ── DOWNLOAD DATA ────────────────────────────────────────────
print("📥 Downloading data...")

ihsg = yf.download("^JKSE", period="5y", progress=False)
idr  = yf.download("IDR=X", period="5y", progress=False)["Close"].squeeze()

try:
    pytrends = TrendReq(hl='id-ID', tz=420)
    pytrends.build_payload(
        ["IHSG","rupiah","saham","investasi","bursa"],
        timeframe='today 5-y', geo='ID'
    )
    trends_data = pytrends.interest_over_time()
    if 'isPartial' in trends_data.columns:
        trends_data = trends_data.drop(columns=['isPartial'])
    trends_ok = True
    print("✅ Google Trends berhasil")
except Exception as e:
    print(f"⚠️  Google Trends gagal: {e} — pakai skor netral 50")
    trends_ok = False

# ── HITUNG INDIKATOR ─────────────────────────────────────────
close  = ihsg["Close"].squeeze()
volume = ihsg["Volume"].squeeze()
idr_ch = idr.pct_change(10)

ma50     = close.rolling(50).mean()
momentum = (close - ma50) / ma50 * 100
rsi      = hitung_rsi(close)
vol_r    = volume.rolling(5).mean() / volume.rolling(90).mean()
idr_inv  = -idr_ch

if trends_ok:
    bobot_kw = {"IHSG":0.30,"rupiah":0.30,"saham":0.20,"investasi":0.15,"bursa":0.05}
    tr_skor  = sum(trends_data[kw]*b for kw,b in bobot_kw.items())
    tr_daily = tr_skor.resample("D").ffill()
    tr_align = tr_daily.reindex(close.index, method="ffill")
    s_tr     = normalisasi(tr_align)
else:
    s_tr = 50.0

s_mom = normalisasi(momentum)
s_rsi = normalisasi(rsi)
s_vol = normalisasi(vol_r)
s_idr = normalisasi(idr_inv)

skor_hari_ini = round(
    s_mom * 0.25 +
    s_rsi * 0.20 +
    s_vol * 0.20 +
    s_idr * 0.20 +
    s_tr  * 0.15,
    1
)

tanggal    = close.index[-1].date()
harga_ihsg = float(close.iloc[-1])

print(f"📊 Skor hari ini ({tanggal}): {skor_hari_ini}")

# ── UPDATE CSV ───────────────────────────────────────────────
csv_path = "data/historis.csv"
os.makedirs("data", exist_ok=True)

# Load CSV yang udah ada
if os.path.exists(csv_path):
    df_hist = pd.read_csv(csv_path, index_col="date", parse_dates=True)
else:
    df_hist = pd.DataFrame(columns=["skor","close"])
    df_hist.index.name = "date"

# Cek apakah tanggal hari ini udah ada (hindari duplikat)
tanggal_ts = pd.Timestamp(tanggal)
if tanggal_ts in df_hist.index:
    # Update kalau udah ada (bisa aja skor berubah kalau dirun ulang)
    df_hist.loc[tanggal_ts, "skor"]  = skor_hari_ini
    df_hist.loc[tanggal_ts, "close"] = harga_ihsg
    print(f"🔄 Data {tanggal} diupdate")
else:
    # Append baris baru
    baris_baru = pd.DataFrame(
        {"skor": [skor_hari_ini], "close": [harga_ihsg]},
        index=pd.DatetimeIndex([tanggal_ts], name="date")
    )
    df_hist = pd.concat([df_hist, baris_baru])
    print(f"➕ Data {tanggal} ditambahkan")

# Simpan
df_hist.sort_index(inplace=True)
df_hist.to_csv(csv_path)

print(f"✅ historis.csv diupdate — total {len(df_hist)} hari data")
print(f"   Momentum : {s_mom}")
print(f"   RSI      : {s_rsi}")
print(f"   Volume   : {s_vol}")
print(f"   Rupiah   : {s_idr}")
print(f"   Trends   : {s_tr}")
