/* ═══════════════════════════════════════════════════════════════
   QUIZFORGE v4.0 — app.js
   New: Search · Difficulty filter · Light/dark toggle ·
        30-worker SSE vis · Better mobile UX · Keyboard nav ·
        Answer history · Streak fire effect · Smart ads
═══════════════════════════════════════════════════════════════ */

/* ── Built-in JEE numerical bank ──────────────────────────── */
const JEE_NUM = [
  {question:"A ball thrown vertically up at 20 m/s. Max height? (g=10 m/s²)",numericalAnswer:20,unit:"m",subject:"JEE — Physics · Mechanics",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"v²=u²−2gh → 0=400−20h → h=20 m",chapter:"Mechanics",marks:4,negative_marks:0},
  {question:"KE (joules) of 4 kg mass moving at 5 m/s?",numericalAnswer:50,unit:"J",subject:"JEE — Physics · Work-Energy",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"KE = ½mv² = ½ × 4 × 25 = 50 J",chapter:"Work & Energy",marks:4,negative_marks:0},
  {question:"Centripetal acceleration (m/s²) for r=2 m, v=6 m/s?",numericalAnswer:18,unit:"m/s²",subject:"JEE — Physics · Circular Motion",exam:"JEE",difficulty:"Medium",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"a = v²/r = 36/2 = 18 m/s²",chapter:"Circular Motion",marks:4,negative_marks:0},
  {question:"Wave speed (m/s): frequency=50 Hz, wavelength=4 m?",numericalAnswer:200,unit:"m/s",subject:"JEE — Physics · Waves",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"v = fλ = 50 × 4 = 200 m/s",chapter:"Waves",marks:4,negative_marks:0},
  {question:"Equivalent resistance (Ω): 6 Ω and 3 Ω in parallel?",numericalAnswer:2,unit:"Ω",subject:"JEE — Physics · Electricity",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"1/R = 1/6 + 1/3 = 1/2 → R = 2 Ω",chapter:"Electricity",marks:4,negative_marks:0},
  {question:"Work done (J): Force=10 N, displacement=5 m, angle=60°?",numericalAnswer:25,unit:"J",subject:"JEE — Physics · Work-Energy",exam:"JEE",difficulty:"Medium",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"W = Fd cosθ = 10 × 5 × 0.5 = 25 J",chapter:"Work & Energy",marks:4,negative_marks:0},
  {question:"Range (m): projectile at 45°, speed=10√2 m/s, g=10 m/s²?",numericalAnswer:20,unit:"m",subject:"JEE — Physics · Projectile",exam:"JEE",difficulty:"Medium",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"R = v²sin2θ/g = 200/10 = 20 m",chapter:"Projectile Motion",marks:4,negative_marks:0},
  {question:"Current (A) through circuit: V=24 V, R=8 Ω?",numericalAnswer:3,unit:"A",subject:"JEE — Physics · Electricity",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"I = V/R = 24/8 = 3 A",chapter:"Electricity",marks:4,negative_marks:0},
  {question:"Moles of water molecules in 36 g of H₂O? (M=18 g/mol)",numericalAnswer:2,unit:"mol",subject:"JEE — Chemistry · Mole Concept",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"n = mass / molar mass = 36/18 = 2 mol",chapter:"Mole Concept",marks:4,negative_marks:0},
  {question:"pH of 0.001 M HCl solution at 25°C?",numericalAnswer:3,unit:"",subject:"JEE — Chemistry · Ionic Equilibrium",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"[H⁺] = 10⁻³ M → pH = −log(10⁻³) = 3",chapter:"Ionic Equilibrium",marks:4,negative_marks:0},
  {question:"f'(x) at x=2 for f(x) = 3x² + 2x?",numericalAnswer:14,unit:"",subject:"JEE — Mathematics · Calculus",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"f'(x) = 6x + 2; f'(2) = 12 + 2 = 14",chapter:"Calculus",marks:4,negative_marks:0},
  {question:"∫₀² 2x dx = ?",numericalAnswer:4,unit:"",subject:"JEE — Mathematics · Integration",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"[x²]₀² = 4 − 0 = 4",chapter:"Calculus",marks:4,negative_marks:0},
  {question:"5th term of AP: first term=3, common difference=4?",numericalAnswer:19,unit:"",subject:"JEE — Mathematics · Sequences",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"a₅ = a + (n−1)d = 3 + 4×4 = 19",chapter:"Sequences & Series",marks:4,negative_marks:0},
  {question:"Distance between origin (0,0) and point (5,12)?",numericalAnswer:13,unit:"",subject:"JEE — Mathematics · Geometry",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"d = √(5² + 12²) = √(25+144) = √169 = 13",chapter:"Coordinate Geometry",marks:4,negative_marks:0},
  {question:"det[[2,1],[1,2]] = ?",numericalAnswer:3,unit:"",subject:"JEE — Mathematics · Matrices",exam:"JEE",difficulty:"Medium",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"det = (2×2) − (1×1) = 4 − 1 = 3",chapter:"Matrices",marks:4,negative_marks:0},
  {question:"Escape velocity (km/s) from Earth? (g=9.8 m/s², R=6400 km)",numericalAnswer:11.2,unit:"km/s",subject:"JEE — Physics · Gravitation",exam:"JEE",difficulty:"Medium",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"v = √(2gR) = √(2×9.8×6.4×10⁶) ≈ 11.2 km/s",chapter:"Gravitation",marks:4,negative_marks:0},
  {question:"Power dissipated (W) in 10 Ω resistor carrying 2 A?",numericalAnswer:40,unit:"W",subject:"JEE — Physics · Electricity",exam:"JEE",difficulty:"Easy",year:"Practice",type:"numerical",source:"JEE Archive",explanation:"P = I²R = 4 × 10 = 40 W",chapter:"Electricity",marks:4,negative_marks:0},
];

/* ════════════════════════════════════════════════
   STATE
════════════════════════════════════════════════ */
let allQ       = [];
let filteredQ  = [];
let activeQ    = [];   // after search filter
let idx        = 0;
let selected   = null;
let answered   = false;
let score      = 0;
let streak     = 0;
let exam       = "ALL";
let chapter    = "ALL";
let diff       = "ALL";
let searchTerm = "";
let timerSec   = 30;
let timerInt   = null;
let sseSource  = null;

// Timer mode
let tmLimit = 0, tmRemain = 0, tmInt = null;

// Answer history & bookmarks
let history   = [];
let bookmarks = JSON.parse(localStorage.getItem("qf_bk") || "[]");

// Wrong answers list for review
let wrongs = [];

/* ════════════════════════════════════════════════
   DOM HELPERS
════════════════════════════════════════════════ */
const $id = id => document.getElementById(id);
function $$id(id){ return $id(id) }

const $load      = $id("loadScreen");
const $loadRing  = $id("loadRing");
const $loadLog   = $id("loadLog");
const $fetchBtn  = $id("fetchBtn");
const $quizArea  = $id("quizArea");
const $ssePanel  = $id("ssePanel");
const $sseFill   = $id("sseFill");
const $ssePct    = $id("ssePct");
const $sseMsg    = $id("sseMsg");
const $sseLog    = $id("sseLog");
const $examTabs  = $id("examTabs");
const $chapterSel= $id("chapterSel");
const $diffSel   = $id("diffSel");
const $progFill  = $id("progFill");
const $progLabel = $id("progLabel");
const $progPct   = $id("progPct");
const $qCard     = $id("qCard");
const $qNum      = $id("qNum");
const $qMeta     = $id("qMeta");
const $qText     = $id("qText");
const $ansArea   = $id("ansArea");
const $expBox    = $id("expBox");
const $expBody   = $id("expBody");
const $expAns    = $id("expAns");
const $btnCheck  = $id("btnCheck");
const $btnNext   = $id("btnNext");
const $btnSkip   = $id("btnSkip");
const $qCounter  = $id("qCounter");
const $results   = $id("resultsBox");
const $scoreVal  = $id("scoreVal");
const $streakVal = $id("streakVal");
const $totalCnt  = $id("totalCount");
const $chartWrap = $id("chartWrap");
const $chartBars = $id("chartBars");
const $bkPanel   = $id("bkPanel");
const $bkList    = $id("bkList");
const $timerBar  = $id("timerBar");
const $timerCD   = $id("timerCountdown");

/* ── Theme ──────────────────────────────────────────────── */
const _th = localStorage.getItem("qf_theme");
if (_th === "light") document.body.classList.add("light");
function toggleTheme() {
  document.body.classList.toggle("light");
  localStorage.setItem("qf_theme", document.body.classList.contains("light") ? "light" : "dark");
  $id("btnTheme") && ($id("btnTheme").textContent = document.body.classList.contains("light") ? "🌙" : "☀");
}

/* ── Logging ────────────────────────────────────────────── */
function log(msg, type = "") {
  const el = document.createElement("div");
  el.className = `log-line log-${type}`;
  el.textContent = msg;
  $loadLog.appendChild(el);
  $loadLog.scrollTop = $loadLog.scrollHeight;
}
function sseAppend(msg, cls = "") {
  const el = document.createElement("div");
  el.textContent = msg;
  if (cls) el.className = cls;
  $sseLog.appendChild(el);
  $sseLog.scrollTop = $sseLog.scrollHeight;
}

/* ════════════════════════════════════════════════
   WORKER DOTS (visual for 30 workers)
════════════════════════════════════════════════ */
function initWorkerDots() {
  const grid = $id("workerGrid");
  if (!grid) return;
  grid.innerHTML = "";
  for (let i = 0; i < 30; i++) {
    const d = document.createElement("div");
    d.className = "worker-dot";
    d.id = `wd${i}`;
    grid.appendChild(d);
  }
}
let _workerActive = 0;
function activateWorker() {
  if (_workerActive < 30) {
    const d = $id(`wd${_workerActive++}`);
    if (d) d.classList.add("active");
  }
}
function doneWorker(n) {
  for (let i = 0; i < Math.min(n, 30); i++) {
    const d = $id(`wd${i}`);
    if (d) { d.classList.remove("active"); d.classList.add("done"); }
  }
}

/* ════════════════════════════════════════════════
   INIT
════════════════════════════════════════════════ */
async function init() {
  log("> QuizForge v4.0 initialising…", "info");
  log("> Checking /api/questions…", "info");
  try {
    const res  = await fetch("/api/questions?per_page=200");
    const data = await res.json();
    if (data.questions && data.questions.length > 0) {
      log(`> Found ${data.questions.length} cached questions ✓`, "ok");
      setTimeout(() => launch(data.questions), 500);
    } else {
      log("> No cached questions found.", "");
      log("> Click below to fetch live questions.", "info");
      _stopRing();
      $fetchBtn.style.display = "flex";
    }
  } catch (e) {
    log(`> Server error: ${e.message}`, "err");
    log("> Make sure Flask is running: python app.py", "err");
    _stopRing();
    $fetchBtn.style.display = "flex";
  }
}

function _stopRing() {
  $loadRing.style.animation = "none";
  $loadRing.style.opacity = "0.3";
}

/* ════════════════════════════════════════════════
   SSE SCRAPE
════════════════════════════════════════════════ */
async function startScrape() {
  $fetchBtn.disabled = true;
  $loadRing.style.animation = "";
  $loadRing.style.opacity = "1";

  try {
    const r = await fetch("/api/scrape", { method: "POST" });
    if (!r.ok && r.status !== 202) {
      const d = await r.json().catch(() => ({}));
      log(`> ❌ ${d.message || "Failed"}`, "err");
      $fetchBtn.disabled = false;
      return;
    }
  } catch (e) {
    log(`> ❌ Network error: ${e.message}`, "err");
    $fetchBtn.disabled = false;
    return;
  }

  initWorkerDots();
  $ssePanel.classList.add("show");
  log("> Scrape started — 30 workers active…", "info");

  // Animate worker dots on
  let dotTimer = 0;
  for (let i = 0; i < 30; i++) {
    setTimeout(activateWorker, dotTimer);
    dotTimer += 80;
  }

  sseSource = new EventSource("/api/scrape/stream");

  sseSource.addEventListener("progress", e => {
    const d = JSON.parse(e.data);
    $sseFill.style.width = d.pct + "%";
    $ssePct.textContent  = d.pct + "%";
    $sseMsg.textContent  = d.msg || "";
    sseAppend(d.msg || "", "info");
    if (d.stage && d.stage.includes("done")) {
      doneWorker(Math.round(30 * d.pct / 100));
    }
  });

  sseSource.addEventListener("done", e => {
    const d = JSON.parse(e.data);
    sseSource.close();
    $sseFill.style.width = "100%";
    $ssePct.textContent  = "100%";
    doneWorker(30);
    sseAppend(`✅ Complete — ${d.count} questions`, "ok");
    log(`> ✅ ${d.count} questions fetched!`, "ok");
    setTimeout(() => {
      $ssePanel.classList.remove("show");
      launch(d.questions || []);
    }, 900);
  });

  sseSource.addEventListener("error", e => {
    let msg = "Unknown error";
    try { msg = JSON.parse(e.data).msg; } catch {}
    sseSource.close();
    sseAppend(`❌ ${msg}`, "err");
    log(`> ❌ ${msg}`, "err");
    $fetchBtn.disabled = false;
  });
}

/* ════════════════════════════════════════════════
   LAUNCH
════════════════════════════════════════════════ */
function launch(questions) {
  allQ = [...questions, ...JEE_NUM];
  $load.classList.remove("show");
  buildTabs();
  buildChapterDropdown();
  applyFilters();
  $quizArea.classList.add("show");
  $totalCnt.textContent = allQ.length;
  $id("dlHdrBtn").style.display = "flex";

  const sources = [...new Set(allQ.map(q => q.source).filter(Boolean))];
  const label = `LIVE — ${sources.length ? sources.slice(0,3).join(" · ") : "ExamSIDE + PW Live + IndiaBix"}`;
  $id("srcLabel").textContent = label;
}

/* ════════════════════════════════════════════════
   TABS
════════════════════════════════════════════════ */
const EXAM_ICONS = {ALL:"🎯",JEE:"⚛",NEET:"🧬",UPSC:"🏛",CAT:"📐",SAT:"🌍",GK:"💡"};
function buildTabs() {
  const order = ["ALL","JEE","NEET","UPSC","CAT","SAT","GK"];
  const available = [...new Set(["ALL", ...allQ.map(q=>q.exam).filter(Boolean)])];
  available.sort((a,b)=>(order.indexOf(a)+1||99)-(order.indexOf(b)+1||99));
  $examTabs.innerHTML = "";
  available.forEach(ex => {
    const count = ex==="ALL" ? allQ.length : allQ.filter(q=>q.exam===ex).length;
    const btn = document.createElement("button");
    btn.className = "tab" + (ex===exam?" active":"");
    btn.dataset.exam = ex;
    btn.setAttribute("role","tab");
    btn.setAttribute("aria-selected", ex===exam ? "true":"false");
    btn.textContent = `${EXAM_ICONS[ex]||"📚"} ${ex} (${count})`;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t=>{ t.classList.remove("active"); t.setAttribute("aria-selected","false"); });
      btn.classList.add("active");
      btn.setAttribute("aria-selected","true");
      exam = ex;
      buildChapterDropdown();
      applyFilters();
    });
    $examTabs.appendChild(btn);
  });
}

function buildChapterDropdown() {
  const pool = exam==="ALL" ? allQ : allQ.filter(q=>q.exam===exam);
  const chs = ["ALL", ...new Set(pool.map(q=>q.chapter||"General").filter(Boolean))].sort((a,b)=>a==="ALL"?-1:a.localeCompare(b));
  $chapterSel.innerHTML = chs.map(c=>`<option value="${c}">${c==="ALL"?"All Chapters":c}</option>`).join("");
  $chapterSel.value = "ALL";
  chapter = "ALL";
}

/* ════════════════════════════════════════════════
   FILTERS
════════════════════════════════════════════════ */
function onChapter() { chapter = $chapterSel.value||"ALL"; applyFilters(); }
function onDiff()    { diff    = $diffSel.value||"ALL";    applyFilters(); }
function onSearch(v) { searchTerm = v.toLowerCase().trim(); applyFilters(); }

function applyFilters() {
  let pool = exam==="ALL" ? [...allQ] : allQ.filter(q=>q.exam===exam);
  if (chapter !== "ALL") pool = pool.filter(q=>(q.chapter||"General")===chapter);
  if (diff    !== "ALL") pool = pool.filter(q=>q.difficulty===diff);
  if (searchTerm)        pool = pool.filter(q=>q.question.toLowerCase().includes(searchTerm));

  // Shuffle
  for (let i=pool.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[pool[i],pool[j]]=[pool[j],pool[i]];}
  filteredQ = pool;
  score = 0; streak = 0; idx = 0; history = []; wrongs = [];
  $scoreVal.textContent  = 0;
  $streakVal.textContent = 0;
  $streakVal.classList.remove("fire");
  $results.classList.remove("show");
  $chartWrap.classList.remove("show");
  $bkPanel.classList.remove("show");
  startTimerMode();
  renderQ();
}

/* ════════════════════════════════════════════════
   TIMER MODE
════════════════════════════════════════════════ */
function onTimerMode() {
  const v = parseInt($id("timerSel").value)||0;
  tmLimit = v * 60;
  applyFilters();
}
function stopTimerMode() {
  clearInterval(tmInt);
  tmLimit = 0;
  $timerBar.classList.remove("show");
  if ($id("timerSel")) $id("timerSel").value = "0";
}
function startTimerMode() {
  clearInterval(tmInt);
  if (!tmLimit) { $timerBar.classList.remove("show"); return; }
  tmRemain = tmLimit;
  $timerBar.classList.add("show");
  _updateTM();
  tmInt = setInterval(() => {
    tmRemain--;
    _updateTM();
    if (tmRemain <= 0) { clearInterval(tmInt); toast("⏰ Time's up!"); showResults(); }
  }, 1000);
}
function _updateTM() {
  const mm = String(Math.floor(tmRemain/60)).padStart(2,"0");
  const ss = String(tmRemain%60).padStart(2,"0");
  $timerCD.textContent = `${mm}:${ss}`;
  $timerCD.classList.toggle("urgent", tmRemain <= 60);
  $id("timerLabel").textContent = `/${Math.floor(tmLimit/60)} min mode`;
}

/* ════════════════════════════════════════════════
   RENDER QUESTION
════════════════════════════════════════════════ */
function renderQ() {
  clearInterval(timerInt);
  if (idx >= filteredQ.length) { showResults(); return; }
  const q = filteredQ[idx];
  selected = null; answered = false;

  const isNum = q.type === "numerical";
  const bk    = bookmarks.includes(bkKey(q));
  const accentColor = examColor(q.exam);

  $qCard.style.setProperty("--card-accent", accentColor);

  // Progress
  const pct = Math.round((idx / filteredQ.length) * 100);
  $progFill.style.width  = pct + "%";
  $progLabel.textContent = `Q ${idx+1} / ${filteredQ.length}`;
  $progPct.textContent   = pct + "%";

  $qNum.textContent = `Question ${idx+1} of ${filteredQ.length}`;

  const diffClass = {Easy:"b-easy",Medium:"b-medium",Hard:"b-hard"}[q.difficulty||"Medium"]||"b-medium";
  const yearClass = (q.year && q.year !== "Practice") ? "b-year real" : "b-year";

  $qMeta.innerHTML = `
    <span class="badge b-exam" style="background:${accentColor}18;border-color:${accentColor}40;color:${accentColor}">${q.exam||"GK"}</span>
    ${isNum ? '<span class="badge b-num">🔢 Numerical</span>' : ""}
    <span class="badge b-subj">${(q.subject||"").split("—").pop().trim().slice(0,28)}</span>
    <span class="badge ${yearClass}">${q.year||"Practice"}</span>
    <span class="badge ${diffClass}">${q.difficulty||"Medium"}</span>
    <button class="btn-bookmark${bk?" on":""}" onclick="toggleBk(event,this)" data-qkey="${encodeURIComponent(bkKey(q))}" title="Save question" aria-label="Bookmark">🔖</button>
    <span class="t-badge" id="tBadge">⏱ <span id="tNum">30</span>s</span>
  `;

  $qText.textContent = q.question;
  $expBox.classList.remove("show");
  $expAns.style.display = "none";
  $btnCheck.disabled = true;
  $btnCheck.style.display = "";
  $btnNext.style.display  = "none";
  $qCounter.textContent   = `${idx+1} of ${filteredQ.length} · ${filteredQ.length-idx-1} remaining`;

  isNum ? renderNum(q) : renderMCQ(q);
  injectAd(q.subject||q.exam||"");

  // Card animation
  $qCard.style.display = "";
  $qCard.style.animation = "none";
  void $qCard.offsetWidth;
  $qCard.style.animation = "";

  // Per-question countdown timer
  timerSec = isNum ? 50 : 30;
  updateTicker(timerSec);
  timerInt = setInterval(() => {
    timerSec--;
    updateTicker(timerSec);
    if (timerSec <= 0) {
      clearInterval(timerInt);
      if (!answered) { streak=0; $streakVal.textContent=0; revealAndNext(); }
    }
  }, 1000);
}

/* ── MCQ ─────────────────────────────────────────────────── */
function renderMCQ(q) {
  $ansArea.innerHTML = '<div class="options" id="optList"></div>';
  const list = $id("optList");
  Object.keys(q.options||{}).forEach(ltr => {
    const div = document.createElement("div");
    div.className = "option";
    div.dataset.ltr = ltr;
    div.innerHTML = `<div class="opt-key">${ltr}</div><div class="opt-txt">${escapeHTML(q.options[ltr])}</div>`;
    div.addEventListener("click", () => selectOpt(ltr));
    list.appendChild(div);
  });
}

/* ── Numerical ───────────────────────────────────────────── */
function renderNum(q) {
  const unit = q.unit ? `<strong style="color:var(--purple-light)">${q.unit}</strong>` : "";
  $ansArea.innerHTML = `
    <div class="num-wrap">
      <div class="num-label">🔢 Enter your answer ${unit}</div>
      <input type="number" id="numIn" class="num-input" step="any"
             placeholder="Type answer…" autocomplete="off" aria-label="Numerical answer"/>
      <div class="num-hint">Tolerance ±0.01. Press <kbd>Enter</kbd> to check.</div>
    </div>
  `;
  const ni = $id("numIn");
  ni.addEventListener("input", () => { $btnCheck.disabled = ni.value.trim()===""; });
  ni.addEventListener("keydown", e => { if(e.key==="Enter" && !$btnCheck.disabled && !answered) checkAnswer(); });
  ni.focus();
}

function updateTicker(sec) {
  const el = $id("tNum"), badge = $id("tBadge");
  if (el) el.textContent = sec;
  if (badge) badge.className = "t-badge" + (sec<=8?" urgent":"");
}

/* ════════════════════════════════════════════════
   SELECT / CHECK
════════════════════════════════════════════════ */
function selectOpt(ltr) {
  if (answered) return;
  selected = ltr;
  document.querySelectorAll(".option").forEach(o => {
    o.classList.toggle("sel", o.dataset.ltr === ltr);
  });
  $btnCheck.disabled = false;
}

/* Keyboard shortcuts */
document.addEventListener("keydown", e => {
  if (answered) {
    if (e.key === "ArrowRight" || e.key === "Enter") nextQ();
    return;
  }
  const keyMap = {"1":"A","2":"B","3":"C","4":"D"};
  if (keyMap[e.key]) {
    const q = filteredQ[idx];
    if (q && q.type !== "numerical") selectOpt(keyMap[e.key]);
  }
  if (e.key === "Enter" && selected && !answered) checkAnswer();
  if (e.key === " " && !answered) { e.preventDefault(); skipQ(); }
});

function checkAnswer() {
  if (answered) return;
  clearInterval(timerInt);
  answered = true;
  const q = filteredQ[idx];
  const isNum = q.type === "numerical";
  let correct = false;

  if (isNum) {
    const ni = $id("numIn");
    const val = parseFloat(ni.value);
    const tol = Math.max(0.01, Math.abs(q.numericalAnswer || 0) * 0.001 + 0.01);
    correct = !isNaN(val) && Math.abs(val - q.numericalAnswer) <= tol;
    ni.disabled = true;
    ni.classList.add(correct ? "ok" : "fail");
    $expAns.textContent = `✓ Correct: ${q.numericalAnswer}${q.unit ? " " + q.unit : ""}`;
    $expAns.style.display = "block";
  } else {
    if (!selected) return;
    correct = selected === q.answer;
    document.querySelectorAll(".option").forEach(o => {
      o.classList.add("locked");
      o.classList.remove("sel");
      if (o.dataset.ltr === q.answer) o.classList.add("correct");
      else if (o.dataset.ltr === selected && !correct) o.classList.add("wrong");
    });
  }

  history.push(correct ? "correct" : "wrong");
  if (!correct) wrongs.push(q);

  if (correct) {
    score++; streak++;
    $scoreVal.textContent  = score;
    $streakVal.textContent = streak;
    if (streak >= 3) {
      $streakVal.classList.add("fire");
      spawnConfetti($qCard);
    }
  } else {
    streak = 0;
    $streakVal.textContent = 0;
    $streakVal.classList.remove("fire");
  }

  $expBody.textContent = q.explanation || "No explanation available.";
  $expBox.classList.add("show");
  $btnCheck.style.display = "none";
  $btnNext.style.display  = "";
  updateChart();
}

function revealAndNext() {
  answered = true;
  const q = filteredQ[idx];
  history.push("skipped");
  if (q.type !== "numerical") {
    document.querySelectorAll(".option").forEach(o => {
      o.classList.add("locked");
      if (o.dataset.ltr === q.answer) o.classList.add("reveal");
    });
  } else {
    const ni = $id("numIn");
    if (ni) ni.disabled = true;
    $expAns.textContent = `✓ Correct: ${q.numericalAnswer}${q.unit ? " "+q.unit : ""}`;
    $expAns.style.display = "block";
  }
  $expBody.textContent = q.explanation || "";
  $expBox.classList.add("show");
  $btnCheck.style.display = "none";
  $btnNext.style.display  = "";
  streak = 0; $streakVal.textContent = 0; $streakVal.classList.remove("fire");
  updateChart();
}

function nextQ()  { idx++; renderQ(); }
function skipQ()  {
  clearInterval(timerInt);
  history.push("skipped");
  streak = 0; $streakVal.textContent = 0; $streakVal.classList.remove("fire");
  idx++; renderQ();
}

/* ════════════════════════════════════════════════
   SEARCH TOGGLE
════════════════════════════════════════════════ */
function toggleSearch() {
  const wrap = $id("searchWrap");
  const btn  = $id("searchToggleBtn");
  const hidden = wrap.style.display === "none";
  wrap.style.display = hidden ? "block" : "none";
  btn.classList.toggle("active", hidden);
  if (hidden) $id("searchInput").focus();
  else { $id("searchInput").value = ""; searchTerm = ""; applyFilters(); }
}

/* ════════════════════════════════════════════════
   BOOKMARKS
════════════════════════════════════════════════ */
function bkKey(q) { return String(q.id || q.question.slice(0,50)); }

function toggleBk(e, btn) {
  e.stopPropagation();
  const key = decodeURIComponent(btn.dataset.qkey);
  const pos = bookmarks.indexOf(key);
  if (pos === -1) {
    bookmarks.push(key);
    btn.classList.add("on");
    toast("🔖 Saved!");
  } else {
    bookmarks.splice(pos, 1);
    btn.classList.remove("on");
    toast("Bookmark removed");
  }
  localStorage.setItem("qf_bk", JSON.stringify(bookmarks));
}

function showBookmarks() {
  $bkPanel.classList.toggle("show");
  if (!$bkPanel.classList.contains("show")) return;

  const list = allQ.filter(q => bookmarks.includes(bkKey(q)));
  if (!list.length) {
    $bkList.innerHTML = '<div class="bm-empty">No saved questions yet. Click 🔖 on any question!</div>';
    return;
  }
  $bkList.innerHTML = list.map((q, i) => `
    <div class="bm-item" onclick="jumpTo('${encodeURIComponent(bkKey(q))}')">
      <strong>Q${i+1}.</strong> ${escapeHTML(q.question.slice(0,90))}…
    </div>
  `).join("");
}

function jumpTo(encoded) {
  const key = decodeURIComponent(encoded);
  const i   = filteredQ.findIndex(q => bkKey(q) === key);
  if (i >= 0) { idx = i; renderQ(); }
  $bkPanel.classList.remove("show");
}

/* ════════════════════════════════════════════════
   CHART
════════════════════════════════════════════════ */
function updateChart() {
  if (!$chartWrap) return;
  const last10 = history.slice(-10);
  if (!last10.length) return;
  $chartWrap.classList.add("show");
  const max = last10.length;
  $chartBars.innerHTML = last10.map((r, i) => `
    <div class="c-bar-wrap">
      <div class="c-bar ${r}" style="height:${Math.round(50*(i+1)/max)}px" title="${r}"></div>
      <div class="c-bar-n">${i+1}</div>
    </div>
  `).join("");
}

/* ════════════════════════════════════════════════
   RESULTS
════════════════════════════════════════════════ */
function showResults() {
  clearInterval(timerInt);
  clearInterval(tmInt);
  $qCard.style.display = "none";
  $results.classList.add("show");
  $progFill.style.width = "100%";

  const total = filteredQ.length;
  const pct   = total ? Math.round((score / total) * 100) : 0;
  const emoji = pct===100?"🏆":pct>=80?"🎉":pct>=60?"💪":pct>=40?"📚":"😤";
  const title = pct===100?"Perfect!":pct>=80?"Outstanding!":pct>=60?"Well Done!":pct>=40?"Keep Grinding!":"Back to Books!";

  $id("resEmoji").textContent = emoji;
  $id("resTitle").textContent = title;
  $id("resSub").textContent   = `${score} of ${total} correct · ${pct}% accuracy`;

  $id("ringArc").style.setProperty("--pct", pct);
  $id("ringN").textContent = `${score}/${total}`;

  const skipped = history.filter(h=>h==="skipped").length;
  const numQ    = filteredQ.filter(q=>q.type==="numerical").length;

  $id("statsRow").innerHTML = `
    <div class="stat"><span class="stat-v">${pct}%</span><div class="stat-l">Accuracy</div></div>
    <div class="stat"><span class="stat-v">${score}</span><div class="stat-l">Correct</div></div>
    <div class="stat"><span class="stat-v">${total-score-skipped}</span><div class="stat-l">Wrong</div></div>
    <div class="stat"><span class="stat-v">${skipped}</span><div class="stat-l">Skipped</div></div>
    ${numQ>0?`<div class="stat"><span class="stat-v">${numQ}</span><div class="stat-l">Numerical</div></div>`:""}
  `;

  if (pct === 100) setTimeout(() => spawnConfetti(null), 200);
}

function restartQuiz() {
  $results.classList.remove("show");
  applyFilters();
}

function confirmRefresh() {
  if (!confirm("Re-fetch questions from the internet? (~30–90s)")) return;
  allQ = []; filteredQ = [];
  $quizArea.classList.remove("show");
  $results.classList.remove("show");
  $load.classList.add("show");
  $loadLog.innerHTML = "";
  $loadRing.style.animation = ""; $loadRing.style.opacity = "1";
  $fetchBtn.disabled = false;
  $fetchBtn.style.display = "flex";
  log("> Ready to re-fetch…","info");
}

/* ════════════════════════════════════════════════
   DOWNLOAD / EXPORT
════════════════════════════════════════════════ */
function openDL()  {
  if (!filteredQ.length) { toast("⚠ No questions loaded yet."); return; }
  $id("dlModal").classList.add("open");
}
function closeDL() { $id("dlModal").classList.remove("open"); }
$id("dlModal").addEventListener("click", e => { if(e.target===$id("dlModal")) closeDL(); });

function dlJSON() {
  const examTag = exam==="ALL"?"All":exam;
  const blob = new Blob([JSON.stringify({
    generated: new Date().toISOString(),
    exam, count: filteredQ.length,
    questions: filteredQ.map((q,i)=>({
      number:i+1,exam:q.exam,subject:q.subject,
      chapter:q.chapter||"",year:q.year,
      difficulty:q.difficulty,type:q.type||"mcq",
      marks:q.marks||1,negative_marks:q.negative_marks||0,
      question:q.question,
      ...(q.type==="numerical"
        ?{answer:q.numericalAnswer,unit:q.unit||""}
        :{options:q.options,answer:q.answer}
      ),
      explanation:q.explanation||"",
    }))
  },null,2)],{type:"application/json"});
  triggerDL(blob, `QuizForge_${examTag}.json`);
  closeDL(); toast("✅ JSON downloaded!");
}

function dlCSV() {
  const examTag = exam==="ALL"?"All":exam;
  const rows = [["#","Exam","Chapter","Year","Difficulty","Type","Question","Answer","Explanation"]];
  filteredQ.forEach((q,i)=>{
    const ans = q.type==="numerical"
      ? `${q.numericalAnswer}${q.unit?" "+q.unit:""}`
      : `A:${q.options?.A||""} B:${q.options?.B||""} C:${q.options?.C||""} D:${q.options?.D||""} Correct:${q.answer}`;
    rows.push([i+1,q.exam,q.chapter||"",q.year,q.difficulty,q.type||"mcq",
      `"${(q.question||"").replace(/"/g,'""')}"`,
      `"${ans.replace(/"/g,'""')}"`,
      `"${(q.explanation||"").replace(/"/g,'""')}"`]);
  });
  const blob = new Blob([rows.map(r=>r.join(",")).join("\n")],{type:"text/csv"});
  triggerDL(blob, `QuizForge_${examTag}.csv`);
  closeDL(); toast("✅ CSV downloaded!");
}

/* WhatsApp gate PDF */
function dlPDF() {
  closeDL();
  const lastShare = parseInt(localStorage.getItem("qf_wa")||"0");
  if (Date.now() - lastShare < 86400000) { _printPDF(); return; }
  const ov = $id("waModal"); ov.classList.add("open");
  const fill = $id("waFill"); const btn = $id("waContinueBtn");
  btn.disabled = true; fill.style.width = "0";
  const txt = encodeURIComponent("📚 Practicing PYQs on QuizForge! Try it: http://localhost:5000");
  window.open(`https://wa.me/?text=${txt}`, "_blank");
  setTimeout(()=>{ fill.style.width="100%"; },50);
  setTimeout(()=>{ btn.disabled=false; btn.textContent="✅ Download PDF Now"; },4000);
}
function onWaContinue() {
  localStorage.setItem("qf_wa", String(Date.now()));
  $id("waModal").classList.remove("open");
  _printPDF();
}
function closeWA() { $id("waModal").classList.remove("open"); }

function _printPDF() {
  const examTag = exam==="ALL"?"All Exams":exam;
  const win = window.open("","_blank");
  if (!win) { toast("⚠ Pop-ups blocked — please allow and retry."); return; }
  let html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>QuizForge — ${examTag}</title>
<style>
  body{font-family:'Georgia',serif;max-width:740px;margin:40px auto;padding:0 24px;color:#1A1614;line-height:1.7;background:#fff}
  h1{font-size:1.9rem;color:#1A1614;border-bottom:3px solid #F59E0B;padding-bottom:10px;margin-bottom:4px}
  .meta{font-size:.75rem;color:#78716C;margin-bottom:32px;font-family:monospace}
  .qb{margin-bottom:26px;padding-bottom:20px;border-bottom:1px solid #E7E5E4;page-break-inside:avoid}
  .qn{font-size:.65rem;font-family:monospace;color:#A8A29E;text-transform:uppercase;letter-spacing:.08em}
  .qt{font-size:1.02rem;font-weight:600;margin:5px 0 9px}
  .opt{margin:2px 0 2px 14px;font-size:.88rem}
  .opt .k{font-family:monospace;font-weight:700;min-width:20px;display:inline-block}
  .ans{margin-top:5px;font-size:.78rem;color:#16A34A;font-weight:700;font-family:monospace}
  .exp{margin-top:6px;font-size:.77rem;color:#57534E;background:#FFFBEB;padding:6px 10px;border-radius:4px;border-left:3px solid #F59E0B}
  @media print{body{margin:16px}}
</style></head><body>
<h1>🎯 QuizForge — ${examTag}</h1>
<div class="meta">Generated: ${new Date().toLocaleString()} · ${filteredQ.length} Questions · QuizForge v4.0</div>`;
  filteredQ.forEach((q,i)=>{
    html += `<div class="qb"><div class="qn">Q${i+1} · ${q.exam||""} · ${q.difficulty||""} · ${q.year||""} · ${q.chapter||""}</div>
<div class="qt">${escapeHTMLStr(q.question)}</div>`;
    if(q.type==="numerical"){
      html+=`<div class="opt">Numerical — enter value${q.unit?" ("+q.unit+")":""}</div>
<div class="ans">Answer: ${q.numericalAnswer}${q.unit?" "+q.unit:""}</div>`;
    }else if(q.options){
      html+=Object.entries(q.options).map(([k,v])=>`<div class="opt"><span class="k">${k}.</span> ${escapeHTMLStr(v)}${k===q.answer?" ✓":""}</div>`).join("");
      html+=`<div class="ans">Correct: ${q.answer}</div>`;
    }
    if(q.explanation) html+=`<div class="exp">${escapeHTMLStr(q.explanation)}</div>`;
    html+="</div>";
  });
  html+="</body></html>";
  win.document.open(); win.document.write(html); win.document.close();
  setTimeout(()=>win.print(),600);
  toast("🖨 Opening print dialog…");
}

function triggerDL(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"),{href:url,download:name});
  a.click(); URL.revokeObjectURL(url);
}

/* ════════════════════════════════════════════════
   RESOURCE AD
════════════════════════════════════════════════ */
const ADS = {
  jee:{emoji:"⚛",title:"Concepts of Physics",author:"H.C. Verma",why:"Gold-standard for JEE Physics — every concept from first principles.",url:"https://www.amazon.in/s?k=hc+verma+concepts+of+physics",bg:"linear-gradient(135deg,#1E3A8A,#3B82F6)"},
  neet:{emoji:"🧬",title:"NCERT at your Fingertips — Biology",author:"MTG Editorial",why:"Chapter-wise MCQs mapped to NCERT — the NEET bible.",url:"https://www.amazon.in/s?k=ncert+fingertips+biology+mtg",bg:"linear-gradient(135deg,#15803D,#22C55E)"},
  upsc:{emoji:"🏛",title:"Indian Polity",author:"M. Laxmikanth",why:"The single most important UPSC Polity book.",url:"https://www.amazon.in/s?k=laxmikanth+indian+polity",bg:"linear-gradient(135deg,#B91C1C,#EF4444)"},
  cat:{emoji:"📐",title:"Quantitative Aptitude",author:"Arun Sharma",why:"Definitive CAT Quant resource with graded practice.",url:"https://www.amazon.in/s?k=arun+sharma+quantitative+aptitude",bg:"linear-gradient(135deg,#B45309,#D97706)"},
  gk:{emoji:"🌐",title:"Manorama Yearbook 2026",author:"Mammen Mathew",why:"India's best-selling almanac for all competitive exams.",url:"https://www.amazon.in/s?k=manorama+yearbook+2026",bg:"linear-gradient(135deg,#6D28D9,#A78BFA)"},
};

function injectAd(subject) {
  const ad = $id("adArea");
  if (!ad) return;
  const s = subject.toUpperCase();
  let book;
  if (s.includes("JEE")||s.includes("PHYSICS")||s.includes("CHEM")||s.includes("MATH")) book=ADS.jee;
  else if (s.includes("NEET")||s.includes("BIOL")||s.includes("ZOO")) book=ADS.neet;
  else if (s.includes("UPSC")||s.includes("POLITY")||s.includes("HIST")||s.includes("GEO")) book=ADS.upsc;
  else if (s.includes("CAT")||s.includes("APTITUDE")||s.includes("QUANT")) book=ADS.cat;
  else book=ADS.gk;

  ad.innerHTML = `
    <div class="res-card" role="complementary">
      <button class="rc-dismiss" onclick="this.closest('.res-card').remove()" aria-label="Dismiss">✕</button>
      <div class="rc-cover" style="background:${book.bg}">${book.emoji}</div>
      <div class="rc-body">
        <div class="rc-label">✦ Recommended Resource</div>
        <div class="rc-title">${escapeHTML(book.title)}</div>
        <div class="rc-author">${escapeHTML(book.author)}</div>
        <div class="rc-why">${escapeHTML(book.why)}</div>
      </div>
      <a class="rc-cta" href="${book.url}" target="_blank" rel="noopener noreferrer">View →</a>
    </div>`;
}

/* ════════════════════════════════════════════════
   CONFETTI
════════════════════════════════════════════════ */
const CF_COLORS = ["#8B5CF6","#F97316","#A78BFA","#FB923C","#C4B5FD","#FED7AA","#6D28D9","#EA580C"];
function spawnConfetti(anchor) {
  const n = anchor ? 24 : 80;
  const f = document.createDocumentFragment();
  for (let i=0;i<n;i++){
    const p = document.createElement("div");
    p.className = "confetti-p";
    const rect = anchor ? anchor.getBoundingClientRect()
      : {left:window.innerWidth/2-100,top:window.innerHeight/4,width:200};
    const dur  = (1.8+Math.random()*1.4).toFixed(2);
    const del  = (Math.random()*.5).toFixed(2);
    p.style.cssText = `
      left:${rect.left+Math.random()*Math.max(rect.width||200,200)}px;
      top:${rect.top||100}px;
      background:${CF_COLORS[Math.floor(Math.random()*CF_COLORS.length)]};
      animation-duration:${dur}s;animation-delay:${del}s;
      transform:rotate(${Math.random()*360}deg);
      border-radius:${Math.random()>.5?"50%":"2px"};
      width:${6+Math.random()*6}px;height:${6+Math.random()*6}px;
    `;
    p.addEventListener("animationend",()=>p.remove(),{once:true});
    f.appendChild(p);
  }
  document.body.appendChild(f);
}

/* ════════════════════════════════════════════════
   MUSIC PLAYER
════════════════════════════════════════════════ */
const TRACKS = [
  {name:"Lo-Fi Study Beats",  src:"ilovemusicradio",url:"https://streams.ilovemusic.de/iloveradio17.mp3",type:"radio",emoji:"🎵"},
  {name:"Chill Jazz Café",    src:"JazzGroove",      url:"https://jzgroove.streamguys1.com/jazzgroove-dash",type:"radio",emoji:"🎷"},
  {name:"Classical Focus",    src:"Klassik Radio",   url:"https://stream.klassikradio.de/klassikradio/mp3-128/stream.klassikradio.de/",type:"radio",emoji:"🎻"},
  {name:"Ambient Synth",      src:"Built-in",        url:"SYNTH",type:"synth",emoji:"🌊"},
];

let tIdx=0, playing=false, actx=null, sGain=null, sInt=null;
const $audio  = $id("audioEl");
const $disc   = $id("disc");
const $tName  = $id("tName");
const $tSrc   = $id("tSrc");
const $eq     = $id("eq");
const $pBtn   = $id("playBtn");
const $pStat  = $id("pStatus");

$audio.volume = 0.5;

function _initCtx(){
  if(actx) return;
  actx  = new (window.AudioContext||window.webkitAudioContext)();
  sGain = actx.createGain(); sGain.gain.value=.18;
  const f=actx.createBiquadFilter();f.type="lowpass";f.frequency.value=900;
  sGain.connect(f);f.connect(actx.destination);
}
function _note(freq,st,dur,vol=.09){
  if(!actx)return;
  const o=actx.createOscillator(),g=actx.createGain();
  o.type="sine";o.frequency.setValueAtTime(freq,st);
  g.gain.setValueAtTime(0,st);g.gain.linearRampToValueAtTime(vol,st+.18);
  g.gain.setValueAtTime(vol,st+dur-.3);g.gain.linearRampToValueAtTime(0,st+dur);
  o.connect(g);g.connect(sGain);o.start(st);o.stop(st+dur);
}
const CHORDS=[[261.63,329.63,392],[220,261.63,329.63],[174.61,220,261.63],[196,246.94,293.66]];
let _ci=0;
function _synth(){
  _initCtx();if(actx.state==="suspended")actx.resume();
  function chord(){
    if(!playing)return;
    const now=actx.currentTime,c=CHORDS[_ci%4];
    c.forEach((f,i)=>_note(f*.5,now+i*.07,3.5));
    _note(c[2]*2,now+.5,1.2,.05);_note(c[0]*2,now+2,.9,.045);_ci++;
  }
  chord();sInt=setInterval(chord,4200);
}
function _stopSynth(){clearInterval(sInt);sInt=null;}

function loadTrack(i,auto=false){
  const t=TRACKS[i];
  $tName.textContent=t.name;$tSrc.textContent=t.src;
  $disc.textContent=t.emoji;
  if(t.type==="synth"){
    $audio.pause();$audio.src="";
    $pStat.textContent="SYNTH";$pStat.style.color="var(--amber)";
    if(auto){playing=true;_synth();_setUI(true);}
  }else{
    $pStat.textContent="RADIO";$pStat.style.color="var(--purple-light)";
    _stopSynth();$audio.src=t.url;
    if(auto)$audio.play().then(()=>_setUI(true)).catch(()=>{tIdx=TRACKS.length-1;loadTrack(tIdx,true);});
  }
}
function _setUI(p){
  playing=p;$pBtn.textContent=p?"⏸":"▶";
  $disc.classList.toggle("spinning",p);
  $eq.classList.toggle("on",p);
}
function playPause(){
  const t=TRACKS[tIdx];
  if(t.type==="synth"){playing?_stopSynth():_synth();_setUI(!playing);return;}
  if($audio.paused){
    if(!$audio.src)loadTrack(tIdx);
    $audio.play().then(()=>_setUI(true)).catch(()=>{tIdx=TRACKS.length-1;loadTrack(tIdx,true);});
  }else{$audio.pause();_setUI(false);}
}
function prevTrack(){_stopSynth();tIdx=(tIdx-1+TRACKS.length)%TRACKS.length;loadTrack(tIdx,playing);}
function nextTrack(){_stopSynth();tIdx=(tIdx+1)%TRACKS.length;loadTrack(tIdx,playing);}
function setVol(v){$audio.volume=v/100;if(sGain)sGain.gain.value=(v/100)*.22;}
$audio.addEventListener("ended",nextTrack);
$audio.addEventListener("error",()=>{if(tIdx<TRACKS.length-1){tIdx++;loadTrack(tIdx,true);}});
loadTrack(0,false);

/* ════════════════════════════════════════════════
   TOAST
════════════════════════════════════════════════ */
function toast(msg){
  document.querySelectorAll(".toast").forEach(t=>t.remove());
  const el=document.createElement("div");
  el.className="toast";el.textContent=msg;
  document.body.appendChild(el);
  setTimeout(()=>el.remove(),4000);
}

/* ════════════════════════════════════════════════
   HELPERS
════════════════════════════════════════════════ */
const EXAM_COLORS = {JEE:"#A78BFA",NEET:"#34D399",UPSC:"#FB923C",CAT:"#FBBF24",SAT:"#60A5FA",GK:"#F472B6"};
function examColor(ex){ return EXAM_COLORS[ex]||"#F59E0B"; }
function escapeHTML(str){ const d=document.createElement("div");d.textContent=str;return d.innerHTML; }
function escapeHTMLStr(str){ return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

/* ════════════════════════════════════════════════
   BOOT
════════════════════════════════════════════════ */
init();
setTimeout(()=>toast("⌨ Keys 1–4 select · Enter check · → next · Space skip"),2500);