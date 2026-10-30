"""Gupy (portal.gupy.io): ATS usado por muitas empresas e escritórios; 12 vagas por página."""

import json
import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar

NOME = "Gupy"
MODALIDADES = {"remote": "remoto", "hybrid": "híbrido", "on-site": "presencial"}


def parse(html: str) -> list[Vaga]:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    dados = json.loads(m.group(1))["props"]["pageProps"].get("initialJobList") or {}
    return [
        Vaga(
            fonte=NOME,
            titulo=limpar(j["name"]),
            url=j["jobUrl"],
            empresa=limpar(j.get("careerPageName")),
            local=", ".join(x for x in (j.get("city"), j.get("state")) if x),
            publicada=(j.get("publishedDate") or "")[:10],
            descricao=limpar(BeautifulSoup(j.get("description") or "", "html.parser").get_text(" ")),
            modalidade=MODALIDADES.get(j.get("workplaceType"), ""),
        )
        for j in dados.get("data", [])
    ]


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2) -> list[Vaga]:
    filtros = f"term={quote(termo)}"
    if local:
        filtros += f"&city={quote(local.cidade)}&state={quote(local.estado)}"
    vagas = []
    for pagina in range(1, paginas + 1):
        novas = parse(cliente.get(f"https://portal.gupy.io/job-search/{filtros}&page={pagina}"))
        vagas += novas
        if len(novas) < 12:
            break
    return vagas
