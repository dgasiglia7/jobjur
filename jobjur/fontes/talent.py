"""Talent.com (br.talent.com): agregador que reúne vagas de muitos sites e páginas de carreira; ~20 por página."""

import re

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar

NOME = "Talent.com"


def _texto(cartao, classe: str) -> str:
    achado = cartao.find(class_=re.compile(rf"^JobCard_{classe}"))
    return limpar(achado.get_text(" ")) if achado else ""


def parse(html: str) -> list[Vaga]:
    vagas, vistas = [], set()
    for bloco in BeautifulSoup(html, "html.parser").select("div[data-new-id]"):
        id_vaga, cartao = bloco["data-new-id"], bloco.find("article")
        if not cartao or id_vaga in vistas or not _texto(cartao, "title"):
            continue
        vistas.add(id_vaga)
        quando = cartao.find("time", datetime=True)
        vagas.append(Vaga(
            fonte=NOME,
            titulo=_texto(cartao, "title"),
            url=f"https://br.talent.com/view?id={id_vaga}",
            empresa=_texto(cartao, "company"),
            local=re.sub(r",\s*BR$", "", _texto(cartao, "location")),
            publicada=quando["datetime"][:10] if quando else "",  # data da última atualização do anúncio
            descricao=re.sub(r"\s*Mostre mais$", "", _texto(cartao, "snippet")),
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    params = {"k": termo}
    if local:
        params["l"] = f"{local.cidade}, {local.uf}"
    return parse(cliente.get("https://br.talent.com/jobs", **params))
