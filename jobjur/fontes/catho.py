"""Catho; 20 vagas por página."""

import re
from datetime import date, timedelta

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "Catho"


def _data(texto: str, hoje: date) -> str:
    texto = texto.lower()
    if "hoje" in texto:
        return hoje.isoformat()
    if "ontem" in texto:
        return (hoje - timedelta(days=1)).isoformat()
    if m := re.search(r"(\d{2})/(\d{2})", texto):
        d = date(hoje.year, int(m.group(2)), int(m.group(1)))
        return (d if d <= hoje else d.replace(year=hoje.year - 1)).isoformat()
    return ""


def parse(html: str, hoje: date | None = None) -> list[Vaga]:
    hoje = hoje or date.today()
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("li[data-offer-item]"):
        link = card.select_one("h2.title_offer a")
        if not link:
            continue
        empresa = card.select_one("p.mb-2 span")
        icone_local, icone_salario = card.select_one(".i_job_location"), card.select_one(".i_salary")
        local = limpar(icone_local.parent.get_text()) if icone_local else ""
        data = card.select_one('[class*="pub_"]')
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(link.get("title") or link.get_text()),
            url="https://www.catho.com.br" + link["href"],
            empresa=limpar(empresa.get_text()) if empresa else "",
            local=re.sub(r"^\d+ vagas? - ", "", local),
            publicada=_data(data.get_text(), hoje) if data else "",
            salario=limpar(icone_salario.parent.get_text()) if icone_salario else "",
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2) -> list[Vaga]:
    url = f"https://www.catho.com.br/vagas/{slug(termo)}/"
    if local:
        url += f"{slug(local.cidade)}-{local.uf.lower()}/"
    vagas = []
    for pagina in range(1, paginas + 1):
        novas = parse(cliente.get(url, page=pagina) if pagina > 1 else cliente.get(url))
        vagas += novas
        if len(novas) < 20:
            break
    return vagas
