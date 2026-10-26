// Menu do site: uma barra no topo de todas as páginas, com a página atual destacada.
// Cada página carrega este arquivo: a capa com <script src="painel/menu.js"></script> e as do painel com
// <script src="menu.js"></script>. Para mudar o menu, é só mudar a lista PAGINAS.
(function () {
  const PAGINAS = [
    // [arquivo a partir da raiz do site, ícone, nome, etiqueta]
    ["index.html", "🏠", "Início", ""],
    ["painel/perguntas.html", "🌙", "A noite", "ao vivo"],
    ["painel/depois.html", "🇧🇷", "O Brasil", "depois"],
    ["painel/curitiba.html", "🏙️", "Curitiba", "bairros"],
    ["painel/crescimento.html", "📈", "1º → 2º turno", "2002–2026"],
    ["painel/admin.html", "🛠️", "Admin", "só no PC"],
  ];
  if (window.self !== window.top) return;  // dentro do painel admin (iframe), o menu já está nas abas

  const src = document.currentScript.getAttribute("src");
  const raiz = src.startsWith("painel/") ? "" : "../";
  const local = ["127.0.0.1", "localhost"].includes(location.hostname);
  const atual = location.pathname.endsWith("/") ? "index.html" : location.pathname.split("/").slice(-2).join("/");
  const ehAtual = arq => atual === arq || atual.endsWith("/" + arq) || (arq === "index.html" && !atual.includes("painel/") && atual.endsWith("index.html"));

  const estilo = document.createElement("style");
  estilo.textContent = `
    .menu-site { position: sticky; top: 0; z-index: 50; background: var(--cartao, #fff); border-bottom: 1px solid var(--linha, #e3e1dc);
      box-shadow: 0 1px 6px rgba(0,0,0,.05); }
    .menu-site .dentro { max-width: 1100px; margin: 0 auto; padding: 8px 16px; display: flex; gap: 8px; align-items: center;
      overflow-x: auto; scrollbar-width: none; }
    .menu-site .dentro::-webkit-scrollbar { display: none; }
    .menu-site .marca { font-weight: 700; font-size: 14px; color: var(--texto, #1d1d1f); text-decoration: none; margin-right: 6px; white-space: nowrap; }
    .menu-site a.item { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; text-decoration: none;
      color: var(--texto, #1d1d1f); font-size: 13.5px; padding: 5px 11px; border: 1px solid var(--linha, #e3e1dc);
      border-radius: 999px; background: var(--fundo, #f6f5f2); }
    .menu-site a.item:hover { border-color: var(--suave, #6b6b70); }
    .menu-site a.item.atual { border-color: var(--texto, #1d1d1f); background: var(--cartao, #fff); font-weight: 700; }
    .menu-site .icone { font-size: 15px; line-height: 1; }
    .menu-site .tag { font-size: 10.5px; font-weight: 600; color: var(--suave, #6b6b70); border: 1px solid var(--linha, #e3e1dc);
      border-radius: 6px; padding: 0 5px; text-transform: uppercase; letter-spacing: .03em; }
    .menu-site a.item.atual .tag { color: var(--texto, #1d1d1f); }
    [id] { scroll-margin-top: 64px; }  /* os links de seção (#renda etc.) não ficam escondidos atrás do menu */
  `;
  document.head.appendChild(estilo);

  const menu = document.createElement("nav");
  menu.className = "menu-site";
  menu.setAttribute("aria-label", "Páginas do site");
  menu.innerHTML = `<div class="dentro"><a class="marca" href="${raiz}index.html">Noite da apuração 2026</a>` +
    PAGINAS.filter(([arq]) => arq !== "painel/admin.html" || local)
      .map(([arq, icone, nome, tag]) => `<a class="item${ehAtual(arq) ? " atual" : ""}" href="${raiz}${arq}"${ehAtual(arq) ? ' aria-current="page"' : ""}>
        <span class="icone" aria-hidden="true">${icone}</span>${nome}${tag ? `<span class="tag">${tag}</span>` : ""}</a>`).join("") +
    `</div>`;
  document.body.prepend(menu);
  // no celular, se a página atual não couber na barra, rola a barra (só ela) até mostrar o item
  const dentro = menu.querySelector(".dentro"), ativo = menu.querySelector(".atual");
  if (ativo && ativo.offsetLeft + ativo.offsetWidth > dentro.clientWidth) dentro.scrollLeft = ativo.offsetLeft - 16;
})();
