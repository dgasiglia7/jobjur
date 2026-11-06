"""Empregare (empregare.com): portal e ATS de muitas empresas; 10 vagas por página.

A busca do site não filtra por cidade, então só roda uma vez por termo (no Brasil todo) e o
ranqueamento separa as vagas do Rio.
"""

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar

NOME = "Empregare"
POR_PAGINA = 10


def parse(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("li.card"):
        link = card.select_one(".card__t a[href]")
        if not link:
            continue
        data = card.select_one("time[datetime]")
        local = limpar(card.select_one(".card__l").get_text() if card.select_one(".card__l") else "")
        empresa = card.select_one(".card__e")
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(link.get_text()),
            url="https://www.empregare.com" + link["href"] if link["href"].startswith("/") else link["href"],
            empresa=limpar(empresa.get_text()) if empresa else "",
            local=local.replace(" · ", ", "),
            publicada=data["datetime"][:10] if data else "",
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 3) -> list[Vaga]:
    if local:
        return []  # o site ignora a cidade; a busca sem cidade já traz tudo
    vagas = []
    for pagina in range(1, paginas + 1):
        params = {"query": termo, "ordem": "recentes"}
        if pagina > 1:
            params["pagina"] = pagina
        novas = parse(cliente.get("https://www.empregare.com/pt-br/vagas", **params))
        vagas += novas
        if len(novas) < POR_PAGINA:
            break
    return vagas
