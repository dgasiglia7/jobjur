"""Vagas.com.br; a primeira página traz cerca de 30 vagas."""

from datetime import datetime

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "Vagas.com"


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
        try:
            data = datetime.strptime(data, "%d/%m/%Y").date().isoformat()
        except ValueError:
            pass
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
