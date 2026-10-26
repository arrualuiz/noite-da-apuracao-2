// Funções comuns das páginas depois.html e curitiba.html: formatação em pt-BR, dica (tooltip), escalas de cor e botões
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const br = n => n == null ? "–" : Math.round(n).toLocaleString("pt-BR");
const pc = (n, c = 1) => n == null ? "–" : n.toFixed(c).replace(".", ",") + "%";
const sn = (n, f) => (n > 0 ? "+" : n < 0 ? "−" : "") + f(Math.abs(n));
const pts = (n, c = 1) => sn(n, x => x.toFixed(c).replace(".", ",")) + " pts";
const mi = n => Math.abs(n) >= 1e6 ? (n / 1e6).toFixed(2).replace(".", ",") + " mi" : br(n);

// dica (tooltip) única
const dica = document.getElementById("dica");
function mostrar(ev, html) {
  dica.innerHTML = html; dica.style.display = "block";
  const w = dica.offsetWidth, h = dica.offsetHeight;
  let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + w > innerWidth - 8) x = ev.clientX - w - 14;
  if (y + h > innerHeight - 8) y = ev.clientY - h - 14;
  dica.style.left = x + "px"; dica.style.top = y + "px";
}
const esconder = () => { dica.style.display = "none"; };

// escalas: divergente (Flávio · cinza · Lula) e sequencial (cinza → Lula)
const divergente = (min, max) => d3.scaleLinear().domain([min, (min + max) / 2, max])
  .range([css("--flavio"), css("--meio"), css("--lula")]).interpolate(d3.interpolateLab).clamp(true);
const sequencial = (min, max) => d3.scaleLinear().domain([min, max]).range([css("--meio"), css("--lula")]).interpolate(d3.interpolateLab).clamp(true);
const gradiente = (esc, ticks) => `linear-gradient(90deg, ${ticks.map(t => esc(t)).join(",")})`;

function botoes(id, aoMudar) {
  const caixa = document.getElementById(id);
  caixa.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    caixa.querySelectorAll("button").forEach(x => x.classList.toggle("ativo", x === b));
    aoMudar(b.dataset.modo);
  });
}
const largura = id => document.getElementById(id).clientWidth;

