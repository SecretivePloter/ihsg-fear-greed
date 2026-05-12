const state = {
  rows: [],
  latest: null,
  currentPeriod: 365,
  pnlTemplate: null,
  usdIdr: null,
};

const scoreBands = [
  { max: 24, label: 'Extreme Fear', color: '#e53e3e' },
  { max: 44, label: 'Fear', color: '#ed8936' },
  { max: 54, label: 'Neutral', color: '#ecc94b' },
  { max: 74, label: 'Greed', color: '#68d391' },
  { max: 100, label: 'Extreme Greed', color: '#38a169' },
];

const indicators = [
  ['Momentum (MA50)', 's_mom', 0.25, 'Jarak IHSG dari MA50 — di bawah MA = fear'],
  ['RSI 14 Hari', 's_rsi', 0.20, 'RSI < 30 oversold (fear), > 70 overbought (greed)'],
  ['Volume Pasar', 's_vol', 0.20, 'Volume 5 hari vs 90 hari — volume rendah = lesu'],
  ['Kurs Rupiah', 's_idr', 0.20, 'Rupiah melemah = investor asing cabut = fear'],
  ['Sentimen Publik', 's_tr', 0.15, 'Google Trends: IHSG, rupiah, saham, investasi, bursa'],
  ['USD/IDR', 'usd_idr_score', 0, 'Kurs USD/IDR harian untuk konteks pergerakan rupiah'],
];

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(',');
  return lines
    .filter(Boolean)
    .map((line) => {
      const values = line.split(',');
      const row = {};
      headers.forEach((header, index) => {
        const value = values[index] ?? '';
        row[header] = header === 'date' ? value : (value === '' ? null : Number(value));
      });
      row.timestamp = new Date(`${row.date}T00:00:00+07:00`).getTime();
      return row;
    })
    .filter((row) => Number.isFinite(row.skor) && Number.isFinite(row.timestamp));
}

function formatNumber(value, digits = 1) {
  if (!Number.isFinite(value)) return 'N/A';
  return value.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatSignedPercent(value) {
  if (!Number.isFinite(value)) return 'N/A';
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function formatDate(dateString, options = { day: '2-digit', month: 'short', year: 'numeric' }) {
  return new Intl.DateTimeFormat('en-US', options).format(new Date(`${dateString}T00:00:00+07:00`));
}

function bandFor(score) {
  return scoreBands.find((band) => score <= band.max) ?? scoreBands[scoreBands.length - 1];
}

function card(label, score, sublabel = '') {
  const band = bandFor(score);
  const subtitle = sublabel ? `<br><span style="font-size:0.72rem;">(${sublabel})</span>` : '';
  return `
    <div class="metric-card row-between">
      <span style="color:#8b949e;font-size:0.83rem;">${label}${subtitle}</span>
      <span class="badge" style="background:${band.color}22;color:${band.color};border:1px solid ${band.color}55;">${band.label} — ${formatNumber(score, 1)}</span>
    </div>
  `;
}

function filterByDays(rows, days) {
  if (days >= 9999 || rows.length === 0) return rows;
  const latestTime = rows[rows.length - 1].timestamp;
  const cutoff = latestTime - days * 24 * 60 * 60 * 1000;
  return rows.filter((row) => row.timestamp >= cutoff);
}

function nearestScore(daysAgo) {
  const target = state.latest.timestamp - daysAgo * 24 * 60 * 60 * 1000;
  return state.rows.reduce((best, row) => (
    Math.abs(row.timestamp - target) < Math.abs(best.timestamp - target) ? row : best
  ), state.rows[0]).skor;
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function latestUsdIdr() {
  if (Number.isFinite(state.latest?.usd_idr)) return state.latest.usd_idr;
  if (Number.isFinite(state.usdIdr)) return state.usdIdr;
  const row = [...state.rows].reverse().find((item) => Number.isFinite(item.usd_idr));
  return row?.usd_idr ?? null;
}

function setGauge(score) {
  const band = bandFor(score);
  const arc = document.getElementById('gaugeArc');
  const needle = document.getElementById('gaugeNeedle');
  const badge = document.getElementById('scoreBadge');
  const value = document.getElementById('scoreValue');
  const clamped = Math.max(0, Math.min(100, score));
  const angle = -90 + (clamped / 100) * 180;
  const radians = (angle - 90) * (Math.PI / 180);
  const x2 = 160 + 115 * Math.cos(radians);
  const y2 = 170 + 115 * Math.sin(radians);

  arc.style.stroke = band.color;
  arc.style.strokeDasharray = `${clamped} ${100 - clamped}`;
  arc.style.strokeDashoffset = '0';
  needle.style.stroke = band.color;
  needle.setAttribute('x2', String(x2));
  needle.setAttribute('y2', String(y2));
  badge.style.background = `${band.color}22`;
  badge.style.border = `1px solid ${band.color}55`;
  badge.style.color = band.color;
  badge.textContent = band.label;
  value.style.color = band.color;
  value.textContent = formatNumber(score, 1);
}

function renderHistoricalCards() {
  document.getElementById('historicalCards').innerHTML = [
    ['Yesterday', 1],
    ['Last Week', 7],
    ['Last Month', 30],
  ].map(([label, days]) => card(label, nearestScore(days))).join('');

  const yearRows = filterByDays(state.rows, 365);
  const high = yearRows.reduce((best, row) => (row.skor > best.skor ? row : best), yearRows[0]);
  const low = yearRows.reduce((best, row) => (row.skor < best.skor ? row : best), yearRows[0]);
  document.getElementById('yearlyCards').innerHTML = [
    card('Yearly High', high.skor, formatDate(high.date)),
    card('Yearly Low', low.skor, formatDate(low.date)),
  ].join('');
}

function renderMetrics() {
  setGauge(state.latest.skor);
  setText('ihsgValue', formatNumber(state.latest.close, 2));
  const usdIdr = latestUsdIdr();
  setText('idrValue', Number.isFinite(usdIdr) ? formatNumber(usdIdr, 0) : 'Memuat...');
  setText('updateValue', formatDate(state.latest.date));
}

function renderIndicators() {
  const usdIdr = latestUsdIdr();
  document.getElementById('indicatorCards').innerHTML = indicators.map(([name, key, weight, desc]) => {
    const score = key === 'usd_idr_score' ? state.latest.s_idr : state.latest[key];
    const value = Number.isFinite(score) ? score : 50;
    const displayValue = key === 'usd_idr_score' ? usdIdr : value;
    const band = bandFor(value);
    return `
      <div class="metric-card">
        <div class="row-between" style="margin-bottom:6px;">
          <span style="font-weight:500;font-size:0.9rem;">${name}</span>
          <div>
            <span class="badge" style="background:${band.color}22;color:${band.color};border:1px solid ${band.color}55;margin-right:4px;">${band.label}</span>
            <span style="font-family:'Space Mono',monospace;font-size:0.9rem;color:${band.color};">${formatNumber(displayValue, key === 'usd_idr_score' ? 0 : 1)}</span>
          </div>
        </div>
        <div class="progress"><div class="progress-bar" style="background:${band.color};width:${Math.round(value)}%;"></div></div>
        <span style="font-size:0.75rem;color:#8b949e;">Bobot ${Math.round(weight * 100)}% · ${desc}</span>
      </div>
    `;
  }).join('');
}

async function hydrateUsdIdrFallback() {
  const usdIdr = latestUsdIdr();
  if (Number.isFinite(usdIdr)) {
    state.usdIdr = usdIdr;
    renderMetrics();
    renderIndicators();
    return;
  }

  try {
    const response = await fetch('https://open.er-api.com/v6/latest/USD', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const rate = Number(data?.rates?.IDR);
    if (!Number.isFinite(rate)) throw new Error('IDR rate missing');
    state.usdIdr = rate;
    renderMetrics();
    renderIndicators();
  } catch (error) {
    console.warn('USD/IDR fallback failed', error);
    setText('idrValue', 'N/A');
  }
}

function renderChart() {
  const rows = filterByDays(state.rows, state.currentPeriod);
  const shapes = [
    [0, 25, 'rgba(229,62,62,0.08)'],
    [25, 45, 'rgba(237,137,54,0.06)'],
    [45, 55, 'rgba(236,201,75,0.06)'],
    [55, 75, 'rgba(104,211,145,0.06)'],
    [75, 100, 'rgba(56,161,105,0.08)'],
  ].map(([y0, y1, color]) => ({
    type: 'rect',
    xref: 'paper',
    x0: 0,
    x1: 1,
    y0,
    y1,
    fillcolor: color,
    line: { width: 0 },
    layer: 'below',
  }));

  const annotations = [12, 35, 50, 65, 87].map((y, index) => ({
    x: rows[rows.length - 1].date,
    y,
    text: ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'][index],
    showarrow: false,
    xanchor: 'right',
    font: { size: 9, color: '#8b949e' },
  }));

  Plotly.react('historyChart', [
    {
      x: rows.map((row) => row.date),
      y: rows.map((row) => row.skor),
      name: 'Fear & Greed',
      mode: 'lines',
      line: { width: 2.5, color: '#f6c90e' },
      fill: 'tozeroy',
      fillcolor: 'rgba(246,201,14,0.06)',
    },
    {
      x: rows.map((row) => row.date),
      y: rows.map((row) => row.close),
      name: 'IHSG',
      mode: 'lines',
      yaxis: 'y2',
      line: { width: 1.5, color: '#8b949e', dash: 'dot' },
    },
  ], {
    paper_bgcolor: '#0d1117',
    plot_bgcolor: '#161b22',
    font: { color: '#e6edf3' },
    height: 420,
    margin: { t: 10, b: 20, l: 0, r: 50 },
    legend: {
      bgcolor: '#161b22',
      bordercolor: '#30363d',
      borderwidth: 1,
      orientation: 'h',
      yanchor: 'bottom',
      y: 1.02,
      xanchor: 'right',
      x: 1,
    },
    xaxis: { gridcolor: '#21262d', fixedrange: false },
    yaxis: { gridcolor: '#21262d', range: [0, 100], title: 'Skor F&G', fixedrange: false },
    yaxis2: { overlaying: 'y', side: 'right', showgrid: false, title: 'IHSG', fixedrange: false },
    hovermode: 'x unified',
    dragmode: 'pan',
    shapes,
    annotations,
  }, {
    scrollZoom: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['select2d', 'lasso2d'],
    responsive: true,
  });
}

function showTab(tab) {
  const history = tab === 'history';
  document.getElementById('historyTab').classList.toggle('active', history);
  document.getElementById('breakdownTab').classList.toggle('active', !history);
  document.getElementById('historyPanel').hidden = !history;
  document.getElementById('breakdownPanel').hidden = history;
  if (history) setTimeout(renderChart, 0);
}

function showRoute() {
  const isPnl = location.hash === '#/pnl';
  const isCalculator = location.hash === '#/calculator';
  document.getElementById('homePage').classList.toggle('active', !isPnl && !isCalculator);
  document.getElementById('pnlPage').classList.toggle('active', isPnl);
  document.getElementById('calculatorPage').classList.toggle('active', isCalculator);
  if (isPnl) renderPnl();
  if (isCalculator) renderCalculators();
  if (!isPnl && !isCalculator && state.rows.length > 0) setTimeout(renderChart, 0);
}

async function initHome() {
  try {
    const response = await fetch('data/historis.csv', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.rows = parseCsv(await response.text());
    state.latest = state.rows[state.rows.length - 1];
    renderMetrics();
    renderHistoricalCards();
    renderIndicators();
    renderChart();
    hydrateUsdIdrFallback();
    document.getElementById('loading').hidden = true;
    document.getElementById('homeContent').hidden = false;
  } catch (error) {
    document.getElementById('loading').outerHTML = `<div class="error">Gagal memuat data historis. ${error.message}</div>`;
  }
}

function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ');
  let line = '';
  for (const word of words) {
    const test = `${line}${word} `;
    if (ctx.measureText(test).width > maxWidth && line !== '') {
      ctx.fillText(line, x, y);
      line = `${word} `;
      y += lineHeight;
    } else {
      line = test;
    }
  }
  ctx.fillText(line, x, y);
}

function rupiah(value) {
  return `Rp${Math.round(value).toLocaleString('en-US')}`;
}

function numberFromInput(id) {
  return Number(document.getElementById(id).value);
}

function resultRow(label, value, tone = '') {
  return `
    <div class="result-row">
      <span>${label}</span>
      <strong style="${tone ? `color:${tone};` : ''}">${value}</strong>
    </div>
  `;
}

function renderAverageCalculator() {
  const buy1 = numberFromInput('avgBuy1Price');
  const lot1 = numberFromInput('avgBuy1Lot');
  const buy2 = numberFromInput('avgBuy2Price');
  const lot2 = numberFromInput('avgBuy2Lot');
  const current = numberFromInput('avgCurrentPrice');
  const fee = numberFromInput('avgBuyFee') / 100;
  const shares1 = lot1 * 100;
  const shares2 = lot2 * 100;
  const totalShares = shares1 + shares2;
  const grossCost = buy1 * shares1 + buy2 * shares2;
  const totalCost = grossCost * (1 + fee);
  const average = totalShares > 0 ? totalCost / totalShares : 0;
  const marketValue = current * totalShares;
  const pnl = marketValue - totalCost;
  const pnlPct = totalCost > 0 ? (pnl / totalCost) * 100 : 0;
  const color = pnl >= 0 ? '#06ab6d' : '#ef4444';

  document.getElementById('averageResult').innerHTML = [
    resultRow('Total Lot', formatNumber(lot1 + lot2, 0)),
    resultRow('Total Modal + Fee', rupiah(totalCost)),
    resultRow('Average Price', rupiah(average)),
    resultRow('Nilai Sekarang', rupiah(marketValue)),
    resultRow('Estimasi P/L', `${rupiah(pnl)} (${formatSignedPercent(pnlPct)})`, color),
  ].join('');
}

function renderDividendCalculator() {
  const lot = numberFromInput('divLot');
  const avgPrice = numberFromInput('divAvgPrice');
  const dividendPerShare = numberFromInput('divPerShare');
  const tax = numberFromInput('divTax') / 100;
  const shares = lot * 100;
  const gross = shares * dividendPerShare;
  const taxAmount = gross * tax;
  const net = gross - taxAmount;
  const invested = shares * avgPrice;
  const yieldPct = invested > 0 ? (net / invested) * 100 : 0;

  document.getElementById('dividendResult').innerHTML = [
    resultRow('Jumlah Saham', formatNumber(shares, 0)),
    resultRow('Dividen Kotor', rupiah(gross)),
    resultRow('Pajak', rupiah(taxAmount)),
    resultRow('Dividen Bersih', rupiah(net), '#06ab6d'),
    resultRow('Dividend Yield', formatSignedPercent(yieldPct), '#06ab6d'),
  ].join('');
}

function renderRightIssueCalculator() {
  const lot = numberFromInput('rightLot');
  const marketPrice = numberFromInput('rightMarketPrice');
  const oldRatio = numberFromInput('rightOldRatio');
  const newRatio = numberFromInput('rightNewRatio');
  const exercisePrice = numberFromInput('rightExercisePrice');
  const currentShares = lot * 100;
  const rightsShares = oldRatio > 0 ? currentShares * (newRatio / oldRatio) : 0;
  const totalShares = currentShares + rightsShares;
  const exerciseCost = rightsShares * exercisePrice;
  const terp = totalShares > 0 ? ((currentShares * marketPrice) + exerciseCost) / totalShares : 0;

  document.getElementById('rightResult').innerHTML = [
    resultRow('Hak Saham Baru', `${formatNumber(rightsShares, 0)} saham`),
    resultRow('Dana Tebus', rupiah(exerciseCost)),
    resultRow('Total Saham Setelah Tebus', formatNumber(totalShares, 0)),
    resultRow('TERP Teoritis', rupiah(terp)),
    resultRow('Diskon/Premium vs Pasar', formatSignedPercent(marketPrice > 0 ? ((terp - marketPrice) / marketPrice) * 100 : 0)),
  ].join('');
}

function renderCalculators() {
  renderAverageCalculator();
  renderDividendCalculator();
  renderRightIssueCalculator();
}

function renderPnl() {
  const canvas = document.getElementById('pnlCanvas');
  const ctx = canvas.getContext('2d');
  const emiten = document.getElementById('emitenInput').value.trim().toUpperCase() || 'EMITEN';
  const buy = Number(document.getElementById('buyInput').value);
  const sell = Number(document.getElementById('sellInput').value);
  const message = document.getElementById('pnlMessage');
  if (!Number.isFinite(buy) || !Number.isFinite(sell) || buy <= 0 || sell <= 0) {
    message.textContent = 'Harga beli dan harga jual harus lebih dari 0.';
    return;
  }
  message.textContent = '';

  const pct = ((sell - buy) / buy) * 100;
  const profit = pct >= 0;
  const color = profit ? '#06ab6d' : '#ef4444';
  if (state.pnlTemplate) {
    canvas.width = state.pnlTemplate.naturalWidth;
    canvas.height = state.pnlTemplate.naturalHeight;
    canvas.style.aspectRatio = `${canvas.width} / ${canvas.height}`;
    ctx.drawImage(state.pnlTemplate, 0, 0);

    ctx.fillStyle = '#ffffff';
    ctx.font = '700 142px "DM Sans", sans-serif';
    ctx.fillText(emiten.slice(0, 8), 1347, 850);

    ctx.fillStyle = '#1d1d1d';
    ctx.fillRect(240, 930, 1550, 610);

    ctx.fillStyle = color;
    ctx.font = '800 550px "DM Sans", sans-serif';
    const pctText = `${profit ? '+' : '-'}${Math.abs(pct).toFixed(2)}`;
    ctx.fillText(pctText, 279, 1450);
    const pctWidth = ctx.measureText(pctText).width;
    ctx.font = '800 380px "DM Sans", sans-serif';
    ctx.fillText('%', 289 + pctWidth, 1570);

    ctx.fillStyle = '#ffffff';
    ctx.font = '800 240px "DM Sans", sans-serif';
    ctx.fillText(rupiah(buy), 271, 2320);
    ctx.fillText(rupiah(sell), 1830, 2337);

    ctx.fillStyle = '#505050';
    ctx.font = '40px "DM Sans", sans-serif';
    ctx.fillText('mugenworklabs • for entertainment only', 80, canvas.height - 55);
  } else {
    canvas.width = 1440;
    canvas.height = 1800;
    canvas.style.aspectRatio = `${canvas.width} / ${canvas.height}`;
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#121924');
    gradient.addColorStop(1, '#05070a');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#273244';
    ctx.lineWidth = 3;
    for (let x = -canvas.height; x < canvas.width; x += 90) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + canvas.height, canvas.height);
      ctx.stroke();
    }

    ctx.fillStyle = '#e6edf3';
    ctx.font = '700 92px "DM Sans", sans-serif';
    ctx.fillText('P&L RESULT', 95, 175);

    ctx.fillStyle = '#8b949e';
    ctx.font = '500 42px "DM Sans", sans-serif';
    ctx.fillText('mugenworklabs • for entertainment only', 98, 240);

    ctx.fillStyle = '#ffffff';
    ctx.font = '700 180px "DM Sans", sans-serif';
    ctx.fillText(emiten.slice(0, 8), 95, 470);

    ctx.fillStyle = color;
    ctx.font = '800 330px "DM Sans", sans-serif';
    const pctText = `${profit ? '+' : '-'}${Math.abs(pct).toFixed(2)}`;
    ctx.fillText(pctText, 85, 830);
    const pctWidth = ctx.measureText(pctText).width;
    ctx.font = '800 190px "DM Sans", sans-serif';
    ctx.fillText('%', 100 + pctWidth, 805);

    ctx.fillStyle = '#161b22';
    ctx.strokeStyle = '#30363d';
    ctx.lineWidth = 2;
    ctx.roundRect(95, 1030, 540, 270, 32);
    ctx.fill();
    ctx.stroke();
    ctx.roundRect(805, 1030, 540, 270, 32);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#8b949e';
    ctx.font = '600 42px "DM Sans", sans-serif';
    ctx.fillText('Harga Beli', 145, 1115);
    ctx.fillText('Harga Jual', 855, 1115);

    ctx.fillStyle = '#ffffff';
    ctx.font = '800 78px "DM Sans", sans-serif';
    drawWrappedText(ctx, rupiah(buy), 145, 1215, 420, 86);
    drawWrappedText(ctx, rupiah(sell), 855, 1215, 420, 86);

    ctx.fillStyle = color;
    ctx.font = '700 58px "DM Sans", sans-serif';
    ctx.fillText(profit ? 'PROFIT' : 'LOSS', 95, 1460);

    ctx.fillStyle = '#8b949e';
    ctx.font = '500 38px "DM Sans", sans-serif';
    drawWrappedText(ctx, 'Data yang dimasukkan pengguna tidak disimpan. Bukan rekomendasi investasi.', 95, 1535, 1150, 54);
  }

  document.getElementById('downloadPnl').href = canvas.toDataURL('image/png');
}

function initPnlTemplate() {
  const template = new Image();
  template.addEventListener('load', () => {
    state.pnlTemplate = template;
    renderPnl();
  });
  template.src = 'pnl_template.png';
}

document.getElementById('footerYear').textContent = new Date().getFullYear();
document.getElementById('periodSelect').addEventListener('change', (event) => {
  state.currentPeriod = Number(event.target.value);
  renderChart();
});
document.getElementById('historyTab').addEventListener('click', () => showTab('history'));
document.getElementById('breakdownTab').addEventListener('click', () => showTab('breakdown'));
document.getElementById('generatePnl').addEventListener('click', renderPnl);
['emitenInput', 'buyInput', 'sellInput'].forEach((id) => {
  document.getElementById(id).addEventListener('input', renderPnl);
});
[
  'avgBuy1Price',
  'avgBuy1Lot',
  'avgBuy2Price',
  'avgBuy2Lot',
  'avgCurrentPrice',
  'avgBuyFee',
].forEach((id) => {
  document.getElementById(id).addEventListener('input', renderAverageCalculator);
});
['divLot', 'divAvgPrice', 'divPerShare', 'divTax'].forEach((id) => {
  document.getElementById(id).addEventListener('input', renderDividendCalculator);
});
[
  'rightLot',
  'rightMarketPrice',
  'rightOldRatio',
  'rightNewRatio',
  'rightExercisePrice',
].forEach((id) => {
  document.getElementById(id).addEventListener('input', renderRightIssueCalculator);
});
window.addEventListener('hashchange', showRoute);
window.addEventListener('resize', () => {
  if (document.getElementById('homePage').classList.contains('active') && state.rows.length > 0) renderChart();
});

initHome();
showRoute();
initPnlTemplate();
renderPnl();
renderCalculators();
