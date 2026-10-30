"""Roda os coletores de todas as fontes e junta as vagas sem repetição."""

import logging
from concurrent.futures import ThreadPoolExecutor

from .fontes import FONTES, Cliente, Local, Vaga
from .fontes.base import slug

log = logging.getLogger(__name__)


def _coletar_fonte(nome: str, termos: list[str], locais: list[Local | None]) -> list[Vaga]:
    modulo, cliente, vagas = FONTES[nome], Cliente(), []
    for termo in termos:
        for local in locais:
            try:
                vagas += modulo.buscar(cliente, termo, local)
            except Exception as erro:  # um site fora do ar não deve parar a busca nos outros
                log.warning("%s: falha ao buscar %r em %s: %s", nome, termo, local.cidade if local else "Brasil", erro)
    log.info("%s: %d vagas", nome, len(vagas))
    return vagas


def chave(vaga: Vaga) -> str:
    """Identifica a mesma vaga anunciada em sites diferentes ou repetida em buscas diferentes."""
    return f"{slug(vaga.titulo)}|{slug(vaga.empresa)}"


def deduplicar(vagas: list[Vaga]) -> list[Vaga]:
    vistas, unicas = set(), []
    for vaga in vagas:
        if vaga.url in vistas or chave(vaga) in vistas:
            continue
        vistas.update({vaga.url, chave(vaga)})
        unicas.append(vaga)
    return unicas


def coletar(termos: list[str], local: Local | None, fontes: list[str] | None = None) -> list[Vaga]:
    """Busca cada termo na cidade do candidato e no Brasil todo (onde aparecem as vagas remotas)."""
    locais = [local, None] if local else [None]
    nomes = fontes or list(FONTES)
    with ThreadPoolExecutor(max_workers=len(nomes)) as executor:
        resultados = executor.map(lambda nome: _coletar_fonte(nome, termos, locais), nomes)
    return deduplicar([vaga for lista in resultados for vaga in lista])
