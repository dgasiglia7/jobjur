"""Páginas de carreira dos maiores bancos e empresas do setor financeiro com operação no Brasil.

Testadas em 2026-11-11. Como nas seguradoras, cada página lista todas as vagas da empresa, então a coleta
roda uma vez por busca e guarda só as vagas da área jurídica (no Brasil, quando a página é global).

Lidas: Safra, Sicredi, BMG, Genial, Banco ABC Brasil, Banco Mercantil e Banco Sofisa (Gupy), BTG Pactual,
XP, Banco Inter, C6 Bank, Banco Pan e Agibank (Greenhouse), Banco BV e Neon (Lever), B3, Cielo, Dock, Cora,
Bradesco e XP (InHire), Santander, Mastercard e Citi (Workday) e JPMorgan (Oracle HCM).
Itaú já é lido pela fonte Seguradoras; Nubank, PagBank, PicPay, Stone e Creditas pela fonte Tecnologia.
Ficaram de fora: HSBC, UBS, BNP Paribas e Experian (o sistema de vagas recusa a consulta), Visa (nenhuma vaga
no Brasil), Goldman Sachs e Morgan Stanley (a lista só carrega no navegador), Daycoval e Serasa (o site
não respondeu) e Banco do Brasil e Caixa (contratam por concurso público).
"""

import logging
from datetime import datetime, timezone

from .base import Cliente, Local, Vaga, limpar
from .empresas import parse_greenhouse
from .seguradoras import MODALIDADES, eh_juridica, parse_gupy, parse_inhire, parse_workday
from .tecnologia import _oracle

NOME = "Financeiro"
log = logging.getLogger(__name__)

GUPY = {
    "venhasersafra": "Safra",
    "sicredi": "Sicredi",
    "bmg": "Banco BMG",
    "genial": "Genial Investimentos",
    "abcbrasil": "Banco ABC Brasil",
    "mercantil": "Banco Mercantil",
    "bancosofisa": "Banco Sofisa",
}
GREENHOUSE = {
    "btgpactual": "BTG Pactual",
    "xpinc": "XP Inc.",
    "inter": "Banco Inter",
    "c6bank": "C6 Bank",
    "bancopan": "Banco Pan",
    "agibank": "Agibank",
}
LEVER = {"bv": "Banco BV", "neon": "Neon"}
INHIRE = {"b3": "B3", "cielo": "Cielo", "xp": "XP Inc.", "dock": "Dock", "cora": "Cora", "bradesco": "Bradesco"}
# Workday: empresa -> (servidor, tenant, site)
WORKDAY = {
    "Santander": ("https://santander.wd3.myworkdayjobs.com", "santander", "SantanderCareers"),
    "Mastercard": ("https://mastercard.wd1.myworkdayjobs.com", "mastercard", "CorporateCareers"),
    "Citi": ("https://citi.wd5.myworkdayjobs.com", "citi", "2"),
}
# Oracle HCM: empresa -> (servidor, site, página pública das vagas)
ORACLE_HCM = {
    "JPMorgan": ("https://jpmc.fa.oraclecloud.com", "CX_1001",
                 "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{id}"),
}


def parse_lever(dados: list, empresa: str) -> list[Vaga]:
    vagas = []
    for j in dados or []:
        cat = j.get("categories") or {}
        if not eh_juridica(j.get("text", ""), cat.get("team") or cat.get("department") or ""):
            continue
        try:
            data = datetime.fromtimestamp(int(j["createdAt"]) / 1000, timezone.utc).date().isoformat()
        except (KeyError, TypeError, ValueError):
            data = ""
        vagas.append(Vaga(fonte=NOME, titulo=limpar(j["text"]), url=j["hostedUrl"], empresa=empresa,
                          local=limpar(cat.get("location")), publicada=data,
                          modalidade=MODALIDADES.get((j.get("workplaceType") or "").lower().replace("onsite", "on-site"), "")))
    return vagas


def _workday(cliente: Cliente, empresa: str) -> list[Vaga]:
    servidor, tenant, site = WORKDAY[empresa]
    vagas = []
    for offset in range(0, 400, 20):
        dados = cliente.json(f"{servidor}/wday/cxs/{tenant}/{site}/jobs", "POST",
                             {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": "Brazil"})
        vagas += parse_workday(dados, servidor, site, empresa)
        if len(dados.get("jobPostings", [])) < 20:
            break
    return vagas


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME))
               for sub in GUPY]
    tarefas += [(quadro, lambda quadro=quadro: parse_greenhouse(
        cliente.json(f"https://boards-api.greenhouse.io/v1/boards/{quadro}/jobs"), GREENHOUSE[quadro]))
        for quadro in GREENHOUSE]
    tarefas += [(quadro, lambda quadro=quadro: parse_lever(
        cliente.json(f"https://api.lever.co/v0/postings/{quadro}?mode=json"), LEVER[quadro])) for quadro in LEVER]
    tarefas += [(f"inhire {t}", lambda t=t: parse_inhire(cliente.json(
        "https://api.inhire.app/job-posts/public/pages", cabecalhos={"X-Tenant": t}), t, INHIRE[t])) for t in INHIRE]
    tarefas += [(empresa, lambda empresa=empresa: _workday(cliente, empresa)) for empresa in WORKDAY]
    tarefas += [(empresa, lambda empresa=empresa: _oracle(cliente, empresa, ORACLE_HCM)) for empresa in ORACLE_HCM]
    vagas = []
    for nome, tarefa in tarefas:
        try:
            novas = tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Financeiro: falha em %s: %s", nome, erro)
            continue
        for v in novas:
            v.fonte = NOME
        vagas += novas
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_financeiro_lidas", False):
        return []
    cliente._financeiro_lidas = True
    return coletar(cliente)
