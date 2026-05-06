import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont
import io, os, base64

st.set_page_config(page_title="Kalibrasi P&L", layout="wide")
st.title("🎯 Kalibrasi P&L Generator")
st.markdown("**Drag teks** langsung di gambar untuk atur posisi. Klik teks untuk select, lalu drag.")

TEMPLATE = "pnl_template.png"
if not os.path.exists(TEMPLATE):
    st.error("❌ pnl_template.png tidak ditemukan!")
    st.stop()

with open(TEMPLATE, "rb") as f:
    tmpl_b64 = base64.b64encode(f.read()).decode()

img = Image.open(TEMPLATE)
W, H = img.size

# Font size inputs
col1, col2, col3 = st.columns(3)
with col1:
    emiten_size = st.number_input("Font Emiten", value=28, min_value=8, max_value=500)
with col2:
    pct_size = st.number_input("Font Persentase", value=135, min_value=8, max_value=500)
with col3:
    val_size = st.number_input("Font Harga", value=50, min_value=8, max_value=500)

# Drag tool via HTML canvas
html_code = f"""
<style>
  body {{ margin:0; background:#1a1a1a; }}
  #wrap {{ position:relative; display:inline-block; }}
  canvas {{ display:block; cursor:default; }}
  #coords {{ 
    margin-top:10px; 
    background:#222; 
    color:#aaa; 
    padding:10px 14px; 
    border-radius:8px; 
    font-family:monospace; 
    font-size:13px;
    white-space:pre;
  }}
  #hint {{ color:#f6c90e; font-size:13px; margin-bottom:8px; font-family:sans-serif; }}
</style>

<div id="hint">👆 Klik teks untuk select → drag ke posisi yang benar</div>
<div id="wrap">
  <canvas id="c" width="{W}" height="{H}"></canvas>
</div>
<div id="coords">Loading...</div>

<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const img    = new Image();
img.src      = 'data:image/png;base64,{tmpl_b64}';

// State
const items = [
  {{ id:'emiten', label:'INET',   x:298, y:189, color:'#ffffff', fontSize:{emiten_size} }},
  {{ id:'pct',    label:'+8.00%', x:84,  y:250, color:'#22c55e', fontSize:{pct_size}   }},
  {{ id:'beli',   label:'Rp294',  x:84,  y:500, color:'#ffffff', fontSize:{val_size}   }},
  {{ id:'jual',   label:'Rp318',  x:410, y:500, color:'#ffffff', fontSize:{val_size}   }},
];

let selected = null;
let offsetX  = 0;
let offsetY  = 0;
let isDragging = false;

function getScaleFactor() {{
  return canvas.getBoundingClientRect().width / canvas.width;
}}

function getCanvasPos(e) {{
  const rect  = canvas.getBoundingClientRect();
  const scale = getScaleFactor();
  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  const clientY = e.touches ? e.touches[0].clientY : e.clientY;
  return {{
    x: (clientX - rect.left) / scale,
    y: (clientY - rect.top)  / scale,
  }};
}}

function draw() {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0);

  items.forEach(item => {{
    ctx.font      = `bold ${{item.fontSize}}px Poppins, Arial, sans-serif`;
    ctx.fillStyle = item.color;
    ctx.fillText(item.label, item.x, item.y + item.fontSize);

    if (item === selected) {{
      const m = ctx.measureText(item.label);
      ctx.strokeStyle = '#f6c90e';
      ctx.lineWidth   = 2;
      ctx.strokeRect(item.x - 4, item.y, m.width + 8, item.fontSize + 8);
    }}
  }});

  updateCoords();
}}

function hitTest(pos) {{
  for (let i = items.length - 1; i >= 0; i--) {{
    const item = items[i];
    ctx.font = `bold ${{item.fontSize}}px Poppins, Arial, sans-serif`;
    const m  = ctx.measureText(item.label);
    if (
      pos.x >= item.x - 4 &&
      pos.x <= item.x + m.width + 8 &&
      pos.y >= item.y &&
      pos.y <= item.y + item.fontSize + 8
    ) return item;
  }}
  return null;
}}

function updateCoords() {{
  const el = document.getElementById('coords');
  el.textContent = items.map(i =>
    `${{i.id.padEnd(8)}}: x=${{Math.round(i.x).toString().padStart(4)}}, y=${{Math.round(i.y).toString().padStart(4)}}`
  ).join('\\n');
}}

canvas.addEventListener('mousedown', e => {{
  const pos = getCanvasPos(e);
  selected  = hitTest(pos);
  if (selected) {{
    isDragging = true;
    offsetX    = pos.x - selected.x;
    offsetY    = pos.y - selected.y;
    canvas.style.cursor = 'grabbing';
  }}
  draw();
}});

canvas.addEventListener('mousemove', e => {{
  const pos = getCanvasPos(e);
  if (isDragging && selected) {{
    selected.x = pos.x - offsetX;
    selected.y = pos.y - offsetY;
    draw();
  }} else {{
    canvas.style.cursor = hitTest(pos) ? 'grab' : 'default';
  }}
}});

canvas.addEventListener('mouseup', () => {{
  isDragging = false;
  canvas.style.cursor = 'default';
}});

canvas.addEventListener('mouseleave', () => {{
  isDragging = false;
}});

img.onload = () => draw();

// Responsive canvas
canvas.style.maxWidth  = '100%';
canvas.style.height    = 'auto';
</script>
"""

components.html(html_code, height=H + 120, scrolling=False)

st.divider()
st.markdown("### 📋 Setelah posisi pas, screenshot koordinat di atas dan kirim ke Claude!")