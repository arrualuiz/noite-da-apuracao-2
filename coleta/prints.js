// Tira prints recortados das áreas de interesse do UOL e do g1.
// Uso: node coleta/prints.js <pasta_destino>
const path = require('path');
const puppeteer = require('puppeteer-core');

const destino = process.argv[2] || '.';
const espera = ms => new Promise(r => setTimeout(r, ms));

async function limpar(page) {
  // remove pop-ups, banners de cookie e elementos fixos que cobrem o conteúdo
  await page.evaluate(() => {
    document.querySelectorAll('.solar-modal').forEach(e => e.remove());
    for (const e of document.querySelectorAll('body *')) {
      const st = getComputedStyle(e);
      if ((st.position === 'fixed' || st.position === 'sticky') && e.getBoundingClientRect().height < 400) e.remove();
    }
  });
}

async function printElemento(page, seletor, arquivo, { ate } = {}) {
  const el = await page.$(seletor);
  if (!el) return console.log(`  ! não achei ${seletor}`);
  await el.scrollIntoView();
  await espera(800);
  if (ate) {
    // recorta do topo do elemento até o topo de outro elemento interno
    const box = await page.evaluate((s, a) => {
      const r = document.querySelector(s).getBoundingClientRect();
      const fim = document.querySelector(a);
      const h = fim ? fim.getBoundingClientRect().top - r.top : r.height;
      return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: h };
    }, seletor, ate);
    await page.screenshot({ path: arquivo, clip: box });
  } else {
    await el.screenshot({ path: arquivo });
  }
  console.log(`  ✔ ${path.basename(arquivo)}`);
}

async function uol(browser) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1000, deviceScaleFactor: 1.5 });
  const resp = await page.goto('https://noticias.uol.com.br/eleicoes/2026/apuracao/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  if (resp.status() >= 400) {
    // o UOL bloqueia navegador automatizado de tempos em tempos; não insistimos
    console.log(`  ! UOL bloqueou acesso automatizado (HTTP ${resp.status()}), pulando`);
    return page.close();
  }
  await espera(8000);
  await limpar(page);
  // placar de presidente: o role-card cujo título é "Presidente"
  await page.evaluate(() => {
    const h = [...document.querySelectorAll('.role-card h3')].find(e => e.textContent.trim() === 'Presidente');
    if (h) h.closest('.role-card').id = 'print-placar';
  });
  await printElemento(page, '#print-placar', path.join(destino, 'uol-placar.png'));
  await printElemento(page, '#evolucao-da-apuracao', path.join(destino, 'uol-evolucao.png'), { ate: '#evolucao-da-apuracao .territorial-content' });
  await printElemento(page, '#evolucao-da-apuracao .territorial-content', path.join(destino, 'uol-estados.png'));
  const aba = await page.evaluateHandle(() =>
    [...document.querySelectorAll('#evolucao-da-apuracao li.tab')].find(e => e.textContent.trim() === 'Regiões'));
  if (aba.asElement()) {
    await aba.asElement().click();
    await espera(1500);
    await printElemento(page, '#evolucao-da-apuracao .territorial-content', path.join(destino, 'uol-regioes.png'));
  }
  await page.close();
}

async function g1Placar(browser) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1700, deviceScaleFactor: 1 });
  await page.goto('https://g1.globo.com/politica/eleicoes/2026/apuracao/presidente.ghtml', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await espera(10000);
  await limpar(page);
  await page.screenshot({ path: path.join(destino, 'g1-placar.png') });
  console.log('  ✔ g1-placar.png');
  await page.close();
}

async function g1(browser) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1700, height: 900, deviceScaleFactor: 1 });
  await page.goto('https://g1.globo.com/politica/eleicoes/2026/mapas/mapa-de-apuracao/presidente/brasil.ghtml', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await espera(6000);
  // o mapa só ganha cor depois de clicar em "Explorar mapa"
  const botao = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button, a, div, span')].find(e => e.childElementCount === 0 && e.textContent.trim() === 'Explorar mapa'));
  if (botao.asElement()) { await botao.asElement().click(); await espera(8000); }
  const ok = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button')].find(e => e.textContent.trim() === 'Ok'));
  if (ok.asElement()) { await ok.asElement().click().catch(() => {}); await espera(500); }
  await limpar(page);
  await page.screenshot({ path: path.join(destino, 'g1-mapa.png') });
  console.log('  ✔ g1-mapa.png');
  await page.close();
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true,
    userDataDir: path.join(__dirname, '..', 'dados', '.chrome-puppeteer'),
    args: ['--no-first-run', '--disable-gpu'],
  });
  for (const [nome, fn] of [['uol', uol], ['g1-placar', g1Placar], ['g1-mapa', g1]]) {
    try { await fn(browser); } catch (e) { console.log(`  ! ${nome}: ${e.message}`); }
  }
  await browser.close();
})();
