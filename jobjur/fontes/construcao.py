"""Páginas de carreira das maiores construtoras, incorporadoras e empresas de engenharia do Brasil.

Testadas em 2026-11-12. Como nas seguradoras, cada página lista todas as vagas da empresa, então a coleta
roda uma vez por busca e guarda só as vagas da área jurídica.

Lidas: Cyrela, MRV&CO, Tenda, Cury, EZTec, Even, Gafisa, Helbor, JHSF, Mitre, Tegra, Plano&Plano, Plaenge,
Grupo Marquise, HTB, Concrejato, Andrade Gutierrez, Método, Passarelli, 7LM, VIC Engenharia, Rôgga, Rottas e
Stanza (Gupy), Trisul (Pandapé), Direcional, Concremat, Promon e Nova Engevix (lista de vagas da empresa no
Vagas.com). Ficaram de fora porque não têm lista pública de vagas que dê para ler: Moura Dubeux, Lavvi, Patrimar,
Tecnisa, Vitacon, Kallas, RNI, Calçada, João Fortes, Carvalho Hosken, OEC (Novonor), Queiroz Galvão,
Camargo Corrêa, Racional e Construcap.
"""

import html as html_lib
import logging

from bs4 import BeautifulSoup

from . import vagas_com
from .base import Cliente, Local, Vaga, limpar
from .seguradoras import eh_juridica, parse_gupy

NOME = "Construção"
log = logging.getLogger(__name__)

GUPY = {
    "cyrela": "Cyrela",
    "vagas-mrveco": "MRV&CO",
    "tenda": "Construtora Tenda",
    "cury": "Cury Construtora",
    "eztec": "EZTec",
    "sejaeven": "Even",
    "gafisa": "Gafisa",
    "helbor": "Helbor",
    "jhsf": "JHSF",
    "mitrerealty": "Mitre Realty",
    "tegraincorporadora": "Tegra Incorporadora",
    "vemserplano": "Plano&Plano",
    "grupoplaenge": "Plaenge",
    "grupomarquise": "Grupo Marquise",
    "htb": "Grupo HTB",
    "concrejato": "Concrejato Engenharia",
    "andradegutierrez": "Andrade Gutierrez",
    "metodo": "Método",
    "carreiraspassarelli": "Passarelli",
    "vemser7lm": "7LM",
    "vicengenharia": "VIC Engenharia",
    "rogga": "Rôgga",
    "rottas": "Rottas Construtora e Incorporadora",
    "stanza": "Construtora Stanza",
}
# Pandapé (InfoJobs): subdomínio -> empresa
PANDAPE = {"trisul": "Trisul"}
# Vagas.com: busca pelo nome da empresa -> (trecho do nome da empresa no anúncio, empresa)
VAGAS_COM = {
    "direcional": ("direcional", "Direcional Engenharia"),
    "concremat": ("concremat", "Concremat"),
    "promon": ("promon", "Promon Engenharia"),
    "engevix": ("engevix", "Nova Engevix"),
}


def parse_pandape(html: str, sub: str, empresa: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("a.card-vacancy[href]"):
        titulo = card.select_one("h3")
        if not titulo:
            continue
        titulo = limpar(html_lib.unescape(titulo.get("title") or titulo.get_text()))
        if not eh_juridica(titulo):
            continue
        local = card.select_one(".vacancy-detail .align-middle")
        vagas.append(Vaga(fonte=NOME, titulo=titulo, url=f"https://{sub}.pandape.infojobs.com.br{card['href']}",
                          empresa=empresa, local=limpar(local.get_text() if local else "")))
    return vagas


def parse_vagas_com(html: str, trecho: str, empresa: str) -> list[Vaga]:
    vagas = []
    for v in vagas_com.parse(html):
        if trecho in (v.empresa or "").lower() and eh_juridica(v.titulo):
            v.empresa, v.fonte = empresa, NOME
            vagas.append(v)
    return vagas


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME))
               for sub in GUPY]
    tarefas += [(sub, lambda sub=sub: parse_pandape(cliente.get(f"https://{sub}.pandape.infojobs.com.br/"), sub,
                                                    PANDAPE[sub])) for sub in PANDAPE]
    tarefas += [(busca, lambda busca=busca: parse_vagas_com(cliente.get(f"https://www.vagas.com.br/vagas-de-{busca}"),
                                                            *VAGAS_COM[busca])) for busca in VAGAS_COM]
    vagas = []
    for nome, tarefa in tarefas:
        try:
            novas = tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Construção: falha em %s: %s", nome, erro)
            continue
        for v in novas:
            v.fonte = NOME
        vagas += novas
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_construcao_lidas", False):
        return []
    cliente._construcao_lidas = True
    return coletar(cliente)
