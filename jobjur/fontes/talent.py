"""Talent.com (br.talent.com): agregador que reúne vagas de muitos sites e páginas de carreira."""

import re

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar

NOME = "Talent.com"
ROTULO = re.compile(r"^Mostre mais for (?P<titulo>.+?)(?: at (?P<empresa>.+))?$")
LOCAL = re.compile(r"^[A-ZÀ-Ý][\wÀ-ÿ' .-]+,\s*[A-Z]{2}$")


def _cartao(link):
    """Sobe a partir do link até o cartão que contém só esta vaga."""
    cartao = link
    while cartao.parent is not None and cartao.parent.name not in ("body", "main", "ul", "ol"):
        if len({a["href"] for a in cartao.parent.find_all("a", href=re.compile(r"view\?id="))}) > 1:
            break
        cartao = cartao.parent
    return cartao


def parse(html: str) -> list[Vaga]:
    vagas, vistas = [], set()
    for link in BeautifulSoup(html, "html.parser").find_all("a", href=re.compile(r"view\?id=\d+"), attrs={"aria-label": True}):
        rotulo = ROTULO.match(limpar(link["aria-label"]))
        id_vaga = re.search(r"id=(\d+)", link["href"]).group(1)
        if not rotulo or id_vaga in vistas:
            continue
        vistas.add(id_vaga)
        cartao = _cartao(link)
        textos = [limpar(t) for t in cartao.stripped_strings]
        snippet = cartao.find("p", class_=re.compile("snippet"))
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(rotulo["titulo"]),
            url=f"https://br.talent.com/view?id={id_vaga}",
            empresa=limpar(rotulo["empresa"] or ""),
            local=next((t for t in textos if LOCAL.match(t)), ""),
            descricao=limpar(snippet.get_text(" ")) if snippet else "",
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 1) -> list[Vaga]:
    params = {"k": termo}
    if local:
        params["l"] = f"{local.cidade}, {local.uf}"
    return parse(cliente.get("https://br.talent.com/jobs", **params))
