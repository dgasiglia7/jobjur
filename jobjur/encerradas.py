"""Descobre se uma vaga já foi encerrada no site de origem.

Cada site mostra isso de um jeito, então a verificação é conservadora: só diz
"encerrada" com um sinal claro (página removida, aviso de vaga encerrada, status
da Gupy). Na dúvida (bloqueio, erro de rede, site sem sinal confiável) devolve None,
e a vaga continua como estava.
"""

import json
import re
from datetime import date
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .fontes.base import Cliente

AVISOS = (
    "vaga foi encerrada",
    "vaga encerrada",
    "não está mais disponível",
    "nao esta mais disponivel",
    "vaga expirada",
    "vaga expirou",
    "inscrições encerradas",
    "candidaturas encerradas",
    "não aceita mais candidaturas",
    "no longer accepting applications",
)
LINKEDIN_ID = re.compile(r"-(\d{6,})(?:\?|$)")


def texto_visivel(html: str) -> str:
    sopa = BeautifulSoup(html, "html.parser")
    for tag in sopa(["script", "style", "noscript", "template"]):
        tag.decompose()
    return re.sub(r"\s+", " ", sopa.get_text(" ")).lower()


def gupy(html: str, hoje: date) -> bool | None:
    achado = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not achado:
        return None
    vaga = json.loads(achado.group(1)).get("props", {}).get("pageProps", {}).get("job")
    if not vaga:
        return True  # a Gupy manda para o login quando a vaga não existe mais
    if vaga.get("status") and vaga["status"] != "published":  # frozen (congelada), closed, canceled...
        return True
    expira = (vaga.get("expiresAt") or "")[:10]
    return bool(expira) and expira < hoje.isoformat()


def por_aviso(html: str) -> bool:
    texto = texto_visivel(html)
    return any(aviso in texto for aviso in AVISOS)


def encerrada(cliente: Cliente, url: str, hoje: date | None = None) -> bool | None:
    """True se a vaga foi encerrada, False se continua aberta, None se não deu para saber."""
    hoje = hoje or date.today()
    host = urlparse(url).netloc
    if "indeed." in host:
        return None  # bloqueia robôs
    pedido = url
    if "linkedin.com" in host:
        achado = LINKEDIN_ID.search(urlparse(url).path)
        if not achado:
            return None
        pedido = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{achado.group(1)}"
    try:
        resposta = cliente.resposta(pedido)
    except httpx.HTTPError:
        return None
    if resposta.status_code in (404, 410):
        return True
    if resposta.status_code != 200:
        return None
    html = resposta.text
    if host.endswith("gupy.io"):
        return gupy(html, hoje)
    if "catho.com.br" in host:
        # vaga removida redireciona para a lista de vagas, sem o número da vaga
        numero = url.rstrip("/").rsplit("/", 1)[-1]
        if numero.isdigit() and numero not in str(resposta.url):
            return True
    if "vagas.com.br" in host and "não encontramos resultados para a sua busca" in texto_visivel(html):
        return True
    if "trabalhabrasil.com.br" in host:
        return None  # número inexistente mostra outra vaga, sem aviso confiável
    return por_aviso(html)
