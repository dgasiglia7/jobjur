"""Páginas de carreira das maiores empresas de tecnologia com operação no Brasil.

Testadas em 2026-11-11. Como nas seguradoras, cada página lista todas as vagas da empresa no Brasil,
então a coleta roda uma vez por busca e guarda só as vagas da área jurídica no Brasil.

Lidas: Amazon, Microsoft, Google, IBM, Oracle, Salesforce, Dell, Nubank, PicPay, Stone, PagBank, VTEX,
EBANX, Globo, Creditas, Grupo Positivo e Wildlife Studios.
Ficaram de fora porque não dá para ler a lista automaticamente: Mercado Livre (o sistema de vagas
recusa robôs), Meta e Uber (recusam robôs), Apple e SAP (a lista só carrega no navegador), TOTVS
(sistema próprio sem lista pública) e Magazine Luiza (99jobs, a lista só carrega no navegador).
"""

import json
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlencode

from .base import Cliente, Local, Vaga, limpar
from .empresas import parse_greenhouse
from .seguradoras import eh_juridica, parse_gupy, parse_workday

NOME = "Tecnologia"
log = logging.getLogger(__name__)

GUPY = {
    "globo": "Globo",
    "pagseguro": "PagBank",
    "creditas": "Creditas",
    "positivo": "Grupo Positivo",
}
GREENHOUSE = {
    "vtex": "VTEX",
    "stone": "Stone",
    "ebanx": "EBANX",
    "wildlifestudios": "Wildlife Studios",
}
SALESFORCE = "https://salesforce.wd12.myworkdayjobs.com"
GOOGLE = "https://www.google.com/about/careers/applications/jobs/results/"
MICROSOFT = "https://apply.careers.microsoft.com"
# Oracle HCM: empresa -> (servidor, site, página pública das vagas)
ORACLE_HCM = {
    "Oracle": ("https://eeho.fa.us2.oraclecloud.com", "CX_45001", "https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{id}"),
    "PicPay": ("https://epdm.fa.la1.oraclecloud.com", "PicPay",
               "https://epdm.fa.la1.oraclecloud.com/hcmUI/CandidateExperience/pt-BR/sites/PicPay/job/{id}"),
    "Dell": ("https://enterpriseplatform.dell.com", "CX_1",
             "https://enterpriseplatform.dell.com/hcmUI/CandidateExperience/en/sites/CX_1/job/{id}"),
}


def _greenhouse(dados: dict, empresa: str) -> list[Vaga]:
    return [v for v in parse_greenhouse(dados, empresa) if not v.local or "china" not in v.local.lower()]


def _data(ts) -> str:
    try:
        return datetime.fromtimestamp(int(ts), timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return ""


def parse_amazon(dados: dict) -> list[Vaga]:
    return [
        Vaga(fonte=NOME, titulo=limpar(j["title"]), url="https://www.amazon.jobs" + j["job_path"], empresa="Amazon",
             local=limpar(j.get("normalized_location")).removesuffix(", BRA"))
        for j in dados.get("jobs", [])
        if eh_juridica(j.get("title", ""), j.get("job_category", ""))
    ]


def parse_microsoft(dados: dict) -> list[Vaga]:
    return [
        Vaga(fonte=NOME, titulo=limpar(p["name"]), url=MICROSOFT + p["positionUrl"], empresa="Microsoft",
             local=limpar(", ".join(p.get("locations") or [])), publicada=_data(p.get("postedTs")),
             modalidade={"remote": "remoto", "hybrid": "híbrido", "onsite": "presencial"}.get(p.get("workLocationOption") or "", ""))
        for p in (dados.get("data") or {}).get("positions", [])
        if eh_juridica(p.get("name", ""), p.get("department") or "")
    ]


def parse_google(html: str) -> list[Vaga]:
    """A lista vem num bloco de dados do JavaScript da página: [id, título, link de candidatura, ...]."""
    vagas = []
    for id_vaga, titulo in re.findall(r'\["(\d{12,})","((?:[^"\\]|\\.)+)","https://www\.google\.com/about/careers/applications/signin', html):
        titulo = limpar(json.loads(f'"{titulo}"'))
        if eh_juridica(titulo):
            vagas.append(Vaga(fonte=NOME, titulo=titulo, url=f"{GOOGLE}{id_vaga}", empresa="Google", local="Brasil"))
    return vagas


def parse_ibm(dados: dict) -> list[Vaga]:
    vagas = []
    for h in (dados.get("hits") or {}).get("hits", []):
        j = h.get("_source", {})
        if eh_juridica(j.get("title", ""), j.get("field_keyword_08", "")):
            local = limpar(j.get("field_keyword_19")).removesuffix(", BR").title().replace("No City", "Brasil")
            vagas.append(Vaga(fonte=NOME, titulo=limpar(j["title"]), url=j["url"], empresa="IBM", local=local))
    return vagas


def parse_oracle(dados: dict, empresa: str, link: str) -> list[Vaga]:
    item = (dados.get("items") or [{}])[0]
    return [
        Vaga(fonte=NOME, titulo=limpar(j["Title"]), url=link.format(id=j["Id"]), empresa=empresa,
             local=limpar(j.get("PrimaryLocation")).removesuffix(", Brasil").removesuffix(", Brazil"),
             publicada=(j.get("PostedDate") or "")[:10])
        for j in item.get("requisitionList", [])
        if eh_juridica(j.get("Title", "")) and re.search(r"bra[sz]il", j.get("PrimaryLocation") or "", re.I)
    ]


def parse_ashby(dados: dict, empresa: str) -> list[Vaga]:
    vagas = []
    for j in dados.get("jobs", []):
        pais = ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or ""
        if not eh_juridica(j.get("title", ""), j.get("department") or "") or pais.lower() not in {"brazil", "brasil"}:
            continue
        vagas.append(Vaga(fonte=NOME, titulo=limpar(j["title"]), url=j["jobUrl"], empresa=empresa,
                          local=limpar(j.get("location")), publicada=(j.get("publishedAt") or "")[:10],
                          modalidade={"remote": "remoto", "hybrid": "híbrido", "onsite": "presencial"}.get(
                              (j.get("workplaceType") or "").lower(), "")))
    return vagas


def _amazon(cliente: Cliente) -> list[Vaga]:
    vagas = []
    for offset in range(0, 1000, 100):
        dados = cliente.json("https://www.amazon.jobs/en/search.json?" + urlencode(
            {"normalized_country_code[]": "BRA", "result_limit": 100, "offset": offset, "sort": "recent"}))
        vagas += parse_amazon(dados)
        if offset + 100 >= dados.get("hits", 0):
            break
    return vagas


def _microsoft(cliente: Cliente) -> list[Vaga]:
    vagas = []
    for inicio in range(0, 300, 10):
        dados = cliente.json(f"{MICROSOFT}/api/pcsx/search?" + urlencode(
            {"domain": "microsoft.com", "query": "", "location": "Brazil", "start": inicio}))
        vagas += parse_microsoft(dados)
        if len((dados.get("data") or {}).get("positions", [])) < 10:
            break
    return vagas


def _google(cliente: Cliente) -> list[Vaga]:
    vagas, vistos = [], set()
    for pagina in range(1, 11):
        html = cliente.get(GOOGLE, location="Brazil", page=pagina)
        ids = set(re.findall(r'\["(\d{12,})","', html))
        if not ids or ids <= vistos:
            break
        vistos |= ids
        vagas += parse_google(html)
    return vagas


def _ibm(cliente: Cliente) -> list[Vaga]:
    corpo = {"appId": "careers", "scopes": ["careers2"], "size": 100, "from": 0, "lang": "zz",
             "query": {"bool": {"must": [{"term": {"field_keyword_05": "Brazil"}}]}},
             "_source": ["title", "url", "field_keyword_19", "field_keyword_05", "field_keyword_08"]}
    return parse_ibm(cliente.json("https://www-api.ibm.com/search/api/v2", "POST", corpo))


def _oracle(cliente: Cliente, empresa: str) -> list[Vaga]:
    servidor, site, link = ORACLE_HCM[empresa]
    vagas = []
    for offset in range(0, 1000, 200):
        finder = f"findReqs;siteNumber={site},limit=200,offset={offset},sortBy=POSTING_DATES_DESC"
        if empresa == "Oracle":
            finder += ",keyword=Brazil"  # a Oracle tem milhares de vagas no mundo
        dados = cliente.json(f"{servidor}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?" + urlencode(
            {"onlyData": "true", "expand": "requisitionList.secondaryLocations", "finder": finder}))
        vagas += parse_oracle(dados, empresa, link)
        item = (dados.get("items") or [{}])[0]
        if offset + 200 >= (item.get("TotalJobsCount") or 0):
            break
    return vagas


def _salesforce(cliente: Cliente) -> list[Vaga]:
    vagas = []
    for offset in range(0, 400, 20):
        dados = cliente.json(f"{SALESFORCE}/wday/cxs/salesforce/External_Career_Site/jobs", "POST",
                             {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": "Brazil"})
        vagas += parse_workday(dados, SALESFORCE, "External_Career_Site", "Salesforce")
        if len(dados.get("jobPostings", [])) < 20:
            break
    for v in vagas:
        v.fonte = NOME
    return vagas


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME))
               for sub in GUPY]
    tarefas += [(quadro, lambda quadro=quadro: _greenhouse(
        cliente.json(f"https://boards-api.greenhouse.io/v1/boards/{quadro}/jobs"), GREENHOUSE[quadro]))
        for quadro in GREENHOUSE]
    tarefas += [(empresa, lambda empresa=empresa: _oracle(cliente, empresa)) for empresa in ORACLE_HCM]
    tarefas += [("amazon", lambda: _amazon(cliente)), ("microsoft", lambda: _microsoft(cliente)),
                ("google", lambda: _google(cliente)), ("ibm", lambda: _ibm(cliente)),
                ("salesforce", lambda: _salesforce(cliente)),
                ("nubank", lambda: parse_ashby(cliente.json("https://api.ashbyhq.com/posting-api/job-board/nubank"), "Nubank"))]
    vagas = []
    for nome, tarefa in tarefas:
        try:
            novas = tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Tecnologia: falha em %s: %s", nome, erro)
            continue
        for v in novas:
            v.fonte = NOME
        vagas += novas
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_tecnologia_lidas", False):
        return []
    cliente._tecnologia_lidas = True
    return coletar(cliente)
