"""Vagas.com.br; a primeira página traz cerca de 30 vagas."""

import re
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "Vagas.com"


def _data(texto: str, hoje: date | None = None) -> str:
    hoje = hoje or date.today()
    texto = texto.lower()
    if "hoje" in texto:
        return hoje.isoformat()
    if "ontem" in texto:
        return (hoje - timedelta(days=1)).isoformat()
    if m := re.search(r"(\d+) dias", texto):
        return (hoje - timedelta(days=int(m.group(1)))).isoformat()
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return ""


def parse(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("li.vaga"):
        link = card.select_one("a.link-detalhes-vaga")
        if not link:
            continue
        local = card.select_one(".vaga-local")
        if local and (dica := local.select_one(".tooltip-place")):
            dica.extract()
        data = limpar(card.select_one(".data-publicacao").get_text()) if card.select_one(".data-publicacao") else ""
        data = _data(data)
        empresa, nivel, descricao = (card.select_one(s) for s in (".emprVaga", ".nivelVaga", ".detalhes"))
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(link.get("title") or link.get_text()),
            url="https://www.vagas.com.br" + link["href"],
            empresa=limpar(empresa.get_text()) if empresa else "",
            local=limpar(local.get_text()) if local else "",
            publicada=data,
            descricao=limpar(descricao.get_text()).removeprefix("Descrição: ") if descricao else "",
            extras={"nivel": limpar(nivel.get_text())} if nivel else {},
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 1) -> list[Vaga]:
    url = f"https://www.vagas.com.br/vagas-de-{slug(termo)}"
    if local:
        url += f"-em-{slug(local.cidade)}"
    return parse(cliente.get(url))
