import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os

st.set_page_config(
    page_title="P&L Generator",
    page_icon="📈",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'DM Sans', sans-serif;
}
.block-container { padding: 2rem 2rem !important; max-width: 680px !important; }
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
}
div[data-testid="stButton"] button {
    background: #238636 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    width: 100% !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── FONT ─────────────────────────────────────────────────────
def get_font(size, bold=False):
    paths = [
        "C:/Windows/Fonts/arialbd.ttf"   if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf"  if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/verdanab.ttf"  if bold else "C:/Windows/Fonts/verdana.ttf",
        "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf" if bold else "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# ── GENERATE ──────────────────────────────────────────────────
def generate_pnl(emiten, harga_beli, harga_jual):
    TEMPLATE = "pnl_template.png"
    if not os.path.exists(TEMPLATE):
        st.error("❌ pnl_template.png tidak ditemukan!")
        return None

    img  = Image.open(TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Hitung return
    pct    = (harga_jual - harga_beli) / harga_beli * 100
    profit = pct >= 0
    tanda  = "+" if profit else ""
    GREEN  = (34, 197, 94)
    RED    = (239, 68, 68)
    WHITE  = (255, 255, 255)
    warna  = GREEN if profit else RED

    # ── Koordinat dari kalibrasi ──
    # Emiten
    f_emiten = get_font(142, bold=True)
    draw.text((1347, 724), emiten.upper(), font=f_emiten, fill=WHITE)

    # Persentase — angka besar, simbol % lebih kecil
    angka_str = f"{tanda}{abs(pct):.2f}"
    persen_str = "%"
    f_angka  = get_font(550, bold=True)
    f_persen = get_font(380, bold=True)  # % lebih kecil dari angka

    # Tulis angka dulu, lalu % di sebelahnya
    w_angka = draw.textbbox((0,0), angka_str, font=f_angka)[2]
    draw.text((279, 1014), angka_str,  font=f_angka,  fill=warna)
    draw.text((279 + w_angka + 10, 1014 + 120), persen_str, font=f_persen, fill=warna)

    # Harga beli
    f_val = get_font(240, bold=True)
    draw.text((1830, 2095), f"Rp{int(harga_beli):,}", font=f_val, fill=WHITE)

    # Harga jual
    draw.text((271, 2112), f"Rp{int(harga_jual):,}", font=f_val, fill=WHITE)

    # Watermark
    f_wm = get_font(40)
    draw.text((80, img.height - 55), "mugenworklabs • for entertainment only", font=f_wm, fill=(80,80,80))

    return img

# ── UI ────────────────────────────────────────────────────────
st.markdown("## 📈 P&L Generator")
st.markdown('<p style="color:#8b949e;font-size:0.83rem;">Generate kartu P&L ala Stockbit · Untuk hiburan komunitas</p>', unsafe_allow_html=True)
st.divider()

emiten     = st.text_input("Nama Emiten", placeholder="Contoh: BBCA, TLKM, GOTO")
col1, col2 = st.columns(2)
with col1:
    harga_beli = st.number_input("Harga Beli (Rata-rata)", min_value=1, value=294, step=1)
with col2:
    harga_jual = st.number_input("Harga Sekarang / Harga Jual", min_value=1, value=318, step=1)

if harga_beli > 0:
    pct   = (harga_jual - harga_beli) / harga_beli * 100
    tanda = "+" if pct >= 0 else ""
    icon  = "🟢" if pct >= 0 else "🔴"
    st.markdown(f"**Return:** {icon} `{tanda}{pct:.2f}%`")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🎨 Generate Gambar"):
    if not emiten.strip():
        st.error("Nama emiten tidak boleh kosong!")
    else:
        with st.spinner("Generating..."):
            img = generate_pnl(emiten.strip(), harga_beli, harga_jual)
            if img:
                # Resize untuk preview (biar tidak terlalu besar di layar)
                preview = img.copy()
                preview.thumbnail((800, 600))
                st.image(preview, use_container_width=True)

                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                st.download_button(
                    label="⬇️ Download PNG (Full Size)",
                    data=buf,
                    file_name=f"pnl_{emiten.upper()}.png",
                    mime="image/png"
                )

st.divider()
st.markdown('<p style="color:#8b949e;font-size:0.72rem;text-align:center;">Disclaimer: Generator ini hanya untuk hiburan komunitas. Bukan merupakan bukti transaksi resmi.</p>', unsafe_allow_html=True)