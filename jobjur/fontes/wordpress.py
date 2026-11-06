"""Sites de vagas feitos em WordPress, lidos pela API pública (wp-json) de posts."""

import re
from datetime import date, timedelta

from bs4 import BeautifulSoup

from .base import Cliente, Vaga, limpar

DIAS = 30  # esses sites guardam anúncios de anos atrás; só interessam os recentes


def parse(posts: list[dict], fonte: str, hoje: date | None = None) -> list[Vaga]:
    limite = ((hoje or date.today()) - timedelta(days=DIAS)).isoformat()
    vagas = []
    for post in posts:
        publicada = (post.get("date") or "")[:10]
        if publicada and publicada < limite:
            continue
        titulo = BeautifulSoup((post.get("title") or {}).get("rendered", ""), "html.parser").get_text()
        resumo = BeautifulSoup((post.get("excerpt") or {}).get("rendered", ""), "html.parser").get_text(" ")
        valor = re.search(r"Sal[áa]rio:\s*(R\$\s*[\d.,]+)", resumo)
        vagas.append(Vaga(fonte=fonte, titulo=limpar(titulo), url=post["link"], local="Rio de Janeiro, RJ",
                          publicada=publicada, descricao=limpar(resumo), salario=valor.group(1) if valor else ""))
    return vagas


def buscar(cliente: Cliente, site: str, fonte: str, termo: str) -> list[Vaga]:
    resposta = cliente.resposta(f"{site}/wp-json/wp/v2/posts", search=termo, per_page=30,
                                _fields="title,link,date,excerpt", orderby="date")
    if resposta.status_code != 200:
        return []
    return parse(resposta.json(), fonte)
