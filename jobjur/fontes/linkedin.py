"""LinkedIn, pela listagem pública de vagas (sem login); 10 vagas por página."""

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar

NOME = "LinkedIn"
URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def parse(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("div.base-search-card"):
        titulo, link = card.select_one(".base-search-card__title"), card.select_one("a.base-card__full-link")
        if not (titulo and link):
            continue
        empresa = card.select_one(".base-search-card__subtitle")
        local = card.select_one(".job-search-card__location")
        data = card.select_one("time")
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(titulo.get_text()),
            url=link["href"].split("?")[0],
            empresa=limpar(empresa.get_text()) if empresa else "",
            local=limpar(local.get_text()) if local else "",
            publicada=data.get("datetime", "") if data else "",
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2,
           dias: int = 30) -> list[Vaga]:
    params = {"keywords": termo, "location": f"{local.cidade}, {local.estado}, Brasil" if local else "Brasil",
              "f_TPR": f"r{dias * 86400}"}
    vagas = []
    for pagina in range(paginas):
        novas = parse(cliente.get(URL, **params, start=pagina * 10))
        # a busca do LinkedIn mistura vagas de outros países quando o termo é genérico
        vagas += [v for v in novas if any(p in v.local for p in ("Brasil", "Brazil"))]
        if len(novas) < 10:
            break
    return vagas
