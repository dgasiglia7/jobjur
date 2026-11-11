"""Páginas de carreira de empresas escolhidas pela usuária (fintechs e empresas de tecnologia).

Testadas em 2026-11-10. Como nas seguradoras, cada página lista todas as vagas da empresa, então a coleta
roda uma vez por busca e guarda só as vagas da área jurídica. Asaas e Grupo Suno usam a Gupy; iFood e
QuintoAndar usam o Greenhouse; a CloudWalk tem página própria (lp.cloudwalk.io/jobs). A Revolut ficou de
fora porque o site pede verificação anti-robô (as vagas dela no Brasil costumam aparecer no LinkedIn,
que já é buscado).
"""

import logging

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar
from .seguradoras import eh_juridica, parse_gupy

NOME = "Empresas"
log = logging.getLogger(__name__)

# subdomínio do Gupy -> nome da empresa
GUPY = {
    "asaas": "Asaas",
    "gruposunojobs": "Grupo Suno",
}
# quadro do Greenhouse -> nome da empresa
GREENHOUSE = {
    "ifoodcarreiras": "iFood",
    "quintoandar": "QuintoAndar",
}
CLOUDWALK = "https://lp.cloudwalk.io"


def parse_greenhouse(dados: dict, empresa: str) -> list[Vaga]:
    vagas = []
    for j in dados.get("jobs", []):
        # o QuintoAndar põe o nome do grupo antes do cargo ("Grupo QuintoAndar | Analista Compliance")
        titulo = limpar(j.get("title")).split(" | ")[-1]
        if not eh_juridica(titulo):
            continue
        local = limpar((j.get("location") or {}).get("name")).removesuffix(", Brazil")
        publicada = (j.get("first_published") or j.get("updated_at") or "")[:10]
        vagas.append(Vaga(fonte=NOME, titulo=titulo, url=j["absolute_url"], empresa=empresa, local=local,
                          publicada=publicada))
    return vagas


def parse_cloudwalk(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select('a[href^="/jobs/"]'):
        titulo = card.select_one('p[class*="cardTitle"]')
        if not titulo or not eh_juridica(titulo.get_text()):
            continue  # a área "Risk and Compliance" tem engenheiros, então filtra só pelo título
        meta = card.select_one('p[class*="cardMeta"]')
        local = limpar(meta.get_text()).split(" · ")[0] if meta else ""
        vagas.append(Vaga(fonte=NOME, titulo=limpar(titulo.get_text()), url=CLOUDWALK + card["href"],
                          empresa="CloudWalk", local="" if local.lower().startswith("full") else local))
    return vagas


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME))
               for sub in GUPY]
    tarefas += [(quadro, lambda quadro=quadro: parse_greenhouse(
        cliente.json(f"https://boards-api.greenhouse.io/v1/boards/{quadro}/jobs"), GREENHOUSE[quadro]))
        for quadro in GREENHOUSE]
    tarefas.append(("cloudwalk", lambda: parse_cloudwalk(cliente.get(f"{CLOUDWALK}/jobs"))))
    vagas = []
    for nome, tarefa in tarefas:
        try:
            vagas += tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Empresas: falha em %s: %s", nome, erro)
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_empresas_lidas", False):
        return []
    cliente._empresas_lidas = True
    return coletar(cliente)
