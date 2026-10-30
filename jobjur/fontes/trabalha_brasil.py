"""Trabalha Brasil; 15 vagas por página."""

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "Trabalha Brasil"


def parse(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("article.job-card"):
        link, titulo = card.select_one("a.job-link"), card.select_one(".job-title")
        if not (link and titulo):
            continue
        campos = {c: card.select_one(s) for c, s in (("empresa", ".job-company"), ("local", ".job-location"),
                                                       ("salario", ".salary"), ("modalidade", ".workplace"))}
        texto = {c: limpar(e.get_text()) if e else "" for c, e in campos.items()}
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(titulo.get_text()).removeprefix("Vaga de "),
            url="https://www.trabalhabrasil.com.br" + link["href"],
            empresa=texto["empresa"],
            local=texto["local"],
            salario=texto["salario"],
            modalidade=texto["modalidade"].lower().replace("home-office", "remoto").replace("home office", "remoto"),
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2) -> list[Vaga]:
    lugar = f"em-{slug(local.cidade)}-{local.uf.lower()}" if local else ""
    url = f"https://www.trabalhabrasil.com.br/vagas-de-emprego{'-' + lugar if lugar else ''}/{slug(termo)}"
    vagas = []
    for pagina in range(1, paginas + 1):
        novas = parse(cliente.get(url, pagina=pagina) if pagina > 1 else cliente.get(url))
        vagas += novas
        if len(novas) < 15:
            break
    return vagas
