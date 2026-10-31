"""Empregos.com.br; 20 vagas por página."""

import re
from datetime import date, timedelta
from urllib.parse import unquote

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "Empregos.com.br"


def _data(texto: str, hoje: date) -> str:
    texto = texto.lower()
    if "hoje" in texto or "hora" in texto or "minuto" in texto:
        return hoje.isoformat()
    if "ontem" in texto:
        return (hoje - timedelta(days=1)).isoformat()
    if m := re.search(r"(\d+) dias?", texto):
        return (hoje - timedelta(days=int(m.group(1)))).isoformat()
    return ""


def parse(html: str, hoje: date | None = None) -> list[Vaga]:
    hoje = hoje or date.today()
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("div#job-card"):
        titulo = card.select_one("h2")
        # o link da vaga só aparece nos botões de compartilhar, com o caminho codificado
        caminho = next((m.group(0) for a in card.find_all("a", href=True)
                        if (m := re.search(r"/vaga/\d+/[\w-]+", unquote(a["href"])))), None)
        if not (titulo and caminho):
            continue
        empresa = card.select_one("a[href*='/empresa/']:not(:has(img))")
        infos = [limpar(e.get_text()) for e in card.select("div.mt-1 > div")]
        local = next((e["title"] for e in card.select("h3[title]")), "")
        publicada = next((i for i in infos if "publicada" in i.lower()), "")
        descricao = card.select_one("div.line-clamp-5")
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(titulo.get_text()),
            url="https://www.empregos.com.br" + caminho,
            empresa=limpar(empresa.get_text()) if empresa else "",
            local=limpar(local),
            publicada=_data(publicada, hoje),
            descricao=limpar(descricao.get_text()) if descricao else "",
            salario=next((i for i in infos if "R$" in i or "combinar" in i.lower()), ""),
            modalidade=next((i.lower() for i in infos if i.lower() in {"presencial", "híbrido", "remoto"}), ""),
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2) -> list[Vaga]:
    url = f"https://www.empregos.com.br/vagas/{slug(termo)}"
    if local:
        url += f"-em-{slug(local.cidade)}-{local.uf.lower()}"
    vagas = []
    for pagina in range(1, paginas + 1):
        novas = parse(cliente.get(url, page=pagina) if pagina > 1 else cliente.get(url))
        vagas += novas
        if len(novas) < 20:
            break
    return vagas
