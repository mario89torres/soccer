/* ─── app.js — Soccer xG Analyzer ─── */

const form           = document.getElementById('analyze-form');
const btnText        = document.getElementById('btn-text');
const btnSpinner     = document.getElementById('btn-spinner');
const analyzeBtn     = document.getElementById('analyze-btn');
const errorBox       = document.getElementById('error-box');
const resultsSection = document.getElementById('results-section');

let chart1Instance = null;
let chart2Instance = null;
let donutInstance  = null;

// ── helpers ───────────────────────────────────────────────────────────────────

const setLoading = on => {
  analyzeBtn.disabled = on;
  btnText.textContent = on ? 'Analyzing…' : 'Analyze';
  btnSpinner.classList.toggle('hidden', !on);
};

const showError = msg => {
  errorBox.textContent = msg;
  errorBox.classList.remove('hidden');
  resultsSection.classList.add('hidden');
};

const hideError = () => errorBox.classList.add('hidden');

// ── match banner ──────────────────────────────────────────────────────────────

function buildBanner(d1, d2, pred) {
  const winner = pred?.predicted_winner ?? '—';

  const teamHtml = (d, side) => {
    const right = side === 'right';
    const statsHtml = [
      `<span class="banner-stat">Avg xG <strong style="color:var(--teal)">${d.avg_xg.toFixed(2)}</strong></span>`,
      `<span class="banner-stat">Avg xGA <strong style="color:var(--amber)">${d.avg_xga.toFixed(2)}</strong></span>`,
      `<span class="banner-stat">${d.league}</span>`,
    ].join('');
    return `
      <div class="banner-t-name ${right ? 'amber' : 'teal'}">${d.team}</div>
      <div class="banner-t-meta">${d.season} Season</div>
      <div class="banner-t-stats">${statsHtml}</div>`;
  };

  document.getElementById('banner-team1').innerHTML = teamHtml(d1, 'left');
  document.getElementById('banner-team2').innerHTML = teamHtml(d2, 'right');
  document.getElementById('banner-verdict').textContent =
    winner === 'Draw' ? 'Most likely: Draw' : `Predicted: ${winner}`;
  document.getElementById('banner-league').textContent =
    `${d1.league} · ${d2.league} · ${d1.season}/${d2.season}`;
}

// ── key players ───────────────────────────────────────────────────────────────

function playerStats(containerId, d) {
  const s = d.top_scorers || [];
  const a = d.top_assisters || [];
  
  const block = (title, list, key, accent) => {
    if (!list.length) return '';
    return `
      <div class="key-p-group">
        <div class="key-p-title"><span>${title}</span> <span>${key.toUpperCase()}</span></div>
        <div class="key-p-list">
          ${list.map(p => `
            <div class="key-p-row">
              <span class="key-p-name" title="${p.name}">${p.name}</span>
              <span class="key-p-stat" style="color:${accent}">${p[key]}</span>
            </div>`).join('')}
        </div>
      </div>`;
  };

  document.getElementById(containerId).innerHTML = 
    block('Top Scorers', s, 'goals', 'var(--teal)') + 
    block('Top Assisters', a, 'assists', 'var(--purple)');
}

// ── mini stat pills ───────────────────────────────────────────────────────────

function miniStats(containerId, d) {
  const games = d.games;
  const wins  = games.filter(g => g.result === 'W').length;
  const draws = games.filter(g => g.result === 'D').length;
  const losses= games.filter(g => g.result === 'L').length;
  const gf = games.reduce((a, g) => a + g.goals_scored, 0);
  const ga = games.reduce((a, g) => a + g.goals_conceded, 0);

  const cards = [
    { label:'Form (last 5)', value:`${wins}W ${draws}D ${losses}L`, cls:'teal',  sub:'' },
    { label:'Goals scored', value:gf, cls:'green',  sub:'last 5 games' },
    { label:'Goals conceded', value:ga, cls:'red',   sub:'last 5 games' },
    { label:'xG / xGA diff', value:(d.avg_xg - d.avg_xga).toFixed(2), cls: d.avg_xg >= d.avg_xga ? 'green' : 'red', sub:'positive = attack edge' },
  ];

  document.getElementById(containerId).innerHTML = cards.map(c => `
    <div class="mini-stat">
      <div class="mini-stat-label">${c.label}</div>
      <div class="mini-stat-value ${c.cls}">${c.value}</div>
      <div class="mini-stat-sub">${c.sub}</div>
    </div>`).join('');
}

// ── xG history chart ──────────────────────────────────────────────────────────

function buildChart(canvasId, d, accentColor) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const labels  = d.games.map((g, i) => `G${i+1} ${g.home?'H':'A'}`);
  const xgVals  = d.games.map(g => g.xg);
  const xgaVals = d.games.map(g => g.xga);

  const g1 = ctx.createLinearGradient(0,0,0,220);
  g1.addColorStop(0, accentColor + 'bb'); g1.addColorStop(1, accentColor + '22');
  const g2 = ctx.createLinearGradient(0,0,0,220);
  g2.addColorStop(0,'rgba(245,166,35,.75)'); g2.addColorStop(1,'rgba(245,166,35,.15)');

  return new Chart(ctx, {
    type:'bar',
    data:{
      labels,
      datasets:[
        { label:'xG',  data:xgVals,  backgroundColor:g1, borderColor:accentColor,          borderWidth:1.5, borderRadius:5, borderSkipped:false },
        { label:'xGA', data:xgaVals, backgroundColor:g2, borderColor:'rgba(245,166,35,.8)', borderWidth:1.5, borderRadius:5, borderSkipped:false },
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      animation:{ duration:700, easing:'easeOutQuart' },
      plugins:{
        legend:{ labels:{ color:'#6b7080', font:{family:'Inter',size:10}, boxWidth:10, boxHeight:10 } },
        tooltip:{
          backgroundColor:'rgba(7,9,15,.95)', borderColor:'rgba(255,255,255,.09)', borderWidth:1,
          titleColor:'#e8eaf0', bodyColor:'#6b7080',
          callbacks:{ label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}` }
        }
      },
      scales:{
        x:{ grid:{color:'rgba(255,255,255,.04)'}, ticks:{color:'#6b7080',font:{family:'Inter',size:9}} },
        y:{ beginAtZero:true, grid:{color:'rgba(255,255,255,.05)'}, ticks:{color:'#6b7080',font:{family:'Inter',size:10},stepSize:.5} }
      }
    }
  });
}

// ── match log table ───────────────────────────────────────────────────────────

function buildTable(tableId, d) {
  document.getElementById(tableId).innerHTML = `
    <thead><tr><th>Date</th><th></th><th>Opponent</th><th>Score</th><th>xG</th><th>xGA</th><th></th></tr></thead>
    <tbody>${d.games.map(g => `
      <tr>
        <td>${g.date.slice(5)}</td>
        <td>${g.home ? '🏠' : '✈️'}</td>
        <td style="max-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${g.opponent}</td>
        <td>${g.goals_scored}–${g.goals_conceded}</td>
        <td class="xg-val">${g.xg.toFixed(2)}</td>
        <td class="xga-val">${g.xga.toFixed(2)}</td>
        <td><span class="result-badge result-${g.result}">${g.result}</span></td>
      </tr>`).join('')}
    </tbody>`;
}

// ── prediction center column ──────────────────────────────────────────────────

function probRowHtml(label, pct, barClass) {
  return `
    <div class="prob-row">
      <span class="prob-row-label">${label}</span>
      <div class="prob-row-bar-wrap"><div class="prob-row-bar ${barClass}" style="width:${pct}%"></div></div>
      <span class="prob-row-pct">${pct}%</span>
    </div>`;
}

function slGridHtml(scorelines) {
  return scorelines.map(s => `
    <div class="scoreline-chip">
      <span class="sc-score">${s.score}</span>
      <span class="sc-prob">${s.prob}%</span>
    </div>`).join('');
}

function buildCenter(pred, t1name, t2name) {
  if (!pred || pred.error) return;
  const mc = pred.monte_carlo;
  const po = pred.poisson;

  // xG display
  document.getElementById('xg-label1').textContent = t1name;
  document.getElementById('xg-val1').textContent    = pred.expected_goals_1;
  document.getElementById('xg-label2').textContent = t2name;
  document.getElementById('xg-val2').textContent    = pred.expected_goals_2;

  // Big prob bars (MC)
  document.getElementById('prob-bars').innerHTML = `
    <div class="prob-bar prob-bar-t1"   style="flex:${mc.p_team1_win}">${mc.p_team1_win > 9 ? mc.p_team1_win+'%' : ''}</div>
    <div class="prob-bar prob-bar-draw" style="flex:${mc.p_draw}">${mc.p_draw > 9 ? mc.p_draw+'%' : ''}</div>
    <div class="prob-bar prob-bar-t2"   style="flex:${mc.p_team2_win}">${mc.p_team2_win > 9 ? mc.p_team2_win+'%' : ''}`;

  document.getElementById('prob-legend').innerHTML = `
    <span style="color:var(--teal)">${t1name} <strong>${mc.p_team1_win}%</strong></span>
    <span style="color:var(--purple)">Draw <strong>${mc.p_draw}%</strong></span>
    <span style="color:var(--amber)">${t2name} <strong>${mc.p_team2_win}%</strong></span>`;

  // Poisson
  document.getElementById('poisson-probs').innerHTML =
    probRowHtml(t1name,  po.p_team1_win, 'prob-bar-t1-bar') +
    probRowHtml('Draw',  po.p_draw,      'prob-bar-draw-bar') +
    probRowHtml(t2name,  po.p_team2_win, 'prob-bar-t2-bar');
  document.getElementById('poisson-scorelines').innerHTML = slGridHtml(po.top_scorelines.slice(0,8));
  document.getElementById('poisson-extras').innerHTML = `
    <span class="extra-pill">O2.5 <strong>${po.p_over_25}%</strong></span>
    <span class="extra-pill">BTTS <strong>${po.p_btts}%</strong></span>`;

  // Monte Carlo
  document.getElementById('mc-sims').textContent = `(${mc.n_simulations.toLocaleString()} sims)`;
  document.getElementById('mc-probs').innerHTML =
    probRowHtml(t1name, mc.p_team1_win, 'prob-bar-t1-bar') +
    probRowHtml('Draw', mc.p_draw,      'prob-bar-draw-bar') +
    probRowHtml(t2name, mc.p_team2_win, 'prob-bar-t2-bar');
  document.getElementById('mc-scorelines').innerHTML = slGridHtml(mc.top_scorelines.slice(0,8));
  document.getElementById('mc-extras').innerHTML = `
    <span class="extra-pill">Avg G ${t1name.split(' ').pop()} <strong>${mc.avg_goals_team1}</strong></span>
    <span class="extra-pill">Avg G ${t2name.split(' ').pop()} <strong>${mc.avg_goals_team2}</strong></span>`;

  // Donut
  if (donutInstance) donutInstance.destroy();
  const ctx = document.getElementById('prob-donut').getContext('2d');
  donutInstance = new Chart(ctx, {
    type:'doughnut',
    data:{
      labels:[`${t1name} Win`, 'Draw', `${t2name} Win`],
      datasets:[{
        data:[mc.p_team1_win, mc.p_draw, mc.p_team2_win],
        backgroundColor:['rgba(14,240,212,.7)','rgba(130,80,255,.6)','rgba(245,166,35,.7)'],
        borderColor:['#0ef0d4','#8250ff','#f5a623'],
        borderWidth:2, hoverOffset:6,
      }]
    },
    options:{
      responsive:true, cutout:'70%',
      animation:{ animateRotate:true, duration:800, easing:'easeOutQuart' },
      plugins:{
        legend:{ position:'bottom', labels:{ color:'#6b7080', font:{family:'Inter',size:10}, padding:12, boxWidth:12, boxHeight:12 } },
        tooltip:{ backgroundColor:'rgba(7,9,15,.95)', borderColor:'rgba(255,255,255,.09)', borderWidth:1,
          callbacks:{ label: ctx => ` ${ctx.label}: ${ctx.parsed}%` } }
      }
    }
  });
}

// ── full render ───────────────────────────────────────────────────────────────

function renderResults(data) {
  const d1 = data.team1, d2 = data.team2, pred = data.prediction;

  buildBanner(d1, d2, pred);

  // Team 1 column
  document.getElementById('col-t1-name').textContent   = d1.team;
  document.getElementById('col-t1-league').textContent = `${d1.league} ${d1.season}`;
  playerStats('players-t1', d1);
  miniStats('mini-t1', d1);
  if (chart1Instance) chart1Instance.destroy();
  chart1Instance = buildChart('chart1', d1, '#0ef0d4');
  buildTable('table1', d1);

  // Team 2 column
  document.getElementById('col-t2-name').textContent   = d2.team;
  document.getElementById('col-t2-league').textContent = `${d2.league} ${d2.season}`;
  playerStats('players-t2', d2);
  miniStats('mini-t2', d2);
  if (chart2Instance) chart2Instance.destroy();
  chart2Instance = buildChart('chart2', d2, '#c084fc');
  buildTable('table2', d2);

  // Center prediction column
  buildCenter(pred, d1.team, d2.team);

  resultsSection.classList.remove('hidden');
  resultsSection.scrollIntoView({ behavior:'smooth', block:'start' });
}

// ── form submit ───────────────────────────────────────────────────────────────

form.addEventListener('submit', async e => {
  e.preventDefault();
  hideError();
  setLoading(true);

  const team1 = document.getElementById('team1').value.trim();
  const team2 = document.getElementById('team2').value.trim();

  try {
    const resp = await fetch('/api/analyze', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ team1, team2 }),
    });
    const data = await resp.json();
    if (!resp.ok || data.error) showError(data.error || 'Unknown error. Please try again.');
    else renderResults(data);
  } catch {
    showError('Network error — could not reach the server.');
  } finally {
    setLoading(false);
  }
});
