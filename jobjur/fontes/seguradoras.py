"""Páginas de carreira das maiores seguradoras, que costumam ter departamentos jurídicos grandes.

Testadas em 2026-11-06. Cada página lista todas as vagas da empresa, então a coleta roda uma vez por
busca (não por termo) e guarda só as vagas da área jurídica. Ficaram de fora porque não dá para ler a
lista automaticamente: Bradesco Seguros (Cornerstone), Mapfre e IRB (SuccessFactors sem vagas na
busca), Allianz (verificação anti-robô), SulAmérica (sem página de vagas própria), Sompo (só e-mail) e AXA.
HDI, Yelum (Liberty), AIG e Chubb foram testadas e não tinham vagas no Brasil.
"""

import json
import logging
import re

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar

NOME = "Seguradoras"
log = logging.getLogger(__name__)

# subdomínio do Gupy -> nome da empresa
GUPY = {
    "tokiomarine": "Tokio Marine",
    "porto": "Porto",
    "grupomag": "Grupo MAG",
    "caixavidaeprevidencia": "Caixa Vida e Previdência",
    "brasilprev": "Brasilprev",
    "brasilseg": "Brasilseg",
    "vemproitau": "Itaú",
}
ZURICH = "https://www.careers.zurich.com"
PRUDENTIAL = "https://pru.wd5.myworkdayjobs.com"
MODALIDADES = {"remote": "remoto", "hybrid": "híbrido", "on-site": "presencial"}
JURIDICO = re.compile(r"jur[ií]dic|advog|compliance|contencioso|societ[aá]ri|regulat[oó]ri|privacy|privacidade|"
                      r"\blegal\b|lawyer|counsel|paralegal", re.I)
CLIENTE_PJ = re.compile(r"pessoas? jur[ií]dica|f[ií]sica,? (e )?jur[ií]dica", re.I)


def eh_juridica(titulo: str, area: str = "") -> bool:
    # "Gerente PJ", "Pessoa Física, Jurídica e Agro": cargos comerciais, não da área jurídica
    return bool(JURIDICO.search(f"{titulo} {area}")) and not CLIENTE_PJ.search(titulo)


def parse_gupy(html: str, sub: str, empresas: dict[str, str] = GUPY, fonte: str = NOME) -> list[Vaga]:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    vagas = []
    for j in json.loads(m.group(1))["props"]["pageProps"].get("jobs") or []:
        titulo, area = limpar(j.get("title")), limpar(j.get("department"))
        if not eh_juridica(titulo, area):
            continue
        endereco = (j.get("workplace") or {}).get("address") or {}
        local = ", ".join(x for x in (endereco.get("city"), endereco.get("stateShortName")) if x)
        vagas.append(Vaga(fonte=fonte, titulo=titulo, url=f"https://{sub}.gupy.io/jobs/{j['id']}",
                          empresa=empresas.get(sub, sub), local=local, descricao=area,
                          modalidade=MODALIDADES.get(j.get("workplaceType"), "")))
    return vagas


def parse_zurich(html: str) -> list[Vaga]:
    vagas = []
    for linha in BeautifulSoup(html, "html.parser").select("tr.data-row"):
        link = linha.select_one("a.jobTitle-link")
        if not link or not eh_juridica(link.get_text()):
            continue
        local = linha.select_one(".jobLocation")
        vagas.append(Vaga(fonte=NOME, titulo=limpar(link.get_text()), url=ZURICH + link["href"],
                          empresa="Zurich Seguros", local=limpar(local.get_text() if local else "")))
    return vagas


def parse_workday(dados: dict, base: str, site: str, empresa: str) -> list[Vaga]:
    return [
        Vaga(fonte=NOME, titulo=limpar(j["title"]), url=f"{base}/{site}{j['externalPath']}", empresa=empresa,
             local=limpar(j.get("locationsText")))
        for j in dados.get("jobPostings", [])
        if eh_juridica(j.get("title", "")) and "brazil" in (j.get("externalPath", "") + j.get("locationsText", "")).lower()
    ]


def parse_inhire(dados: dict, tenant: str, empresa: str) -> list[Vaga]:
    return [
        Vaga(fonte=NOME, titulo=limpar(j["displayName"]), url=f"https://{tenant}.inhire.app/vagas/{j['jobId']}",
             empresa=empresa, local=limpar(j.get("location")).removesuffix(", BR"),
             modalidade=MODALIDADES.get((j.get("workplaceType") or "").lower(), ""))
        for j in dados.get("jobsPage", [])
        if eh_juridica(j.get("displayName", ""))
    ]


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub)) for sub in GUPY]
    tarefas += [
        ("zurich", lambda: parse_zurich(cliente.get(f"{ZURICH}/search/", q="", locationsearch="Brazil"))),
        ("prudential", lambda: parse_workday(cliente.json(
            f"{PRUDENTIAL}/wday/cxs/pru/Careers/jobs", "POST",
            {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "Brasil"}), PRUDENTIAL, "Careers",
            "Prudential do Brasil")),
        ("icatu", lambda: parse_inhire(cliente.json("https://api.inhire.app/job-posts/public/pages",
                                                    cabecalhos={"X-Tenant": "icatu"}), "icatu", "Icatu Seguros")),
    ]
    vagas = []
    for nome, tarefa in tarefas:
        try:
            vagas += tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Seguradoras: falha em %s: %s", nome, erro)
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_seguradoras_lidas", False):
        return []
    cliente._seguradoras_lidas = True
    return coletar(cliente)
