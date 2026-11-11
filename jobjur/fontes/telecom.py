"""Páginas de carreira das maiores empresas de telecomunicações do Brasil.

Testadas em 2026-11-11. Como nas seguradoras, cada página lista todas as vagas da empresa, então a coleta
roda uma vez por busca e guarda só as vagas da área jurídica.

Lidas: Vivo, Claro, TIM, V.tal, Algar Telecom, Brisanet, Giga+ (Alloha Fibra), Vero, Nio e Unifique
(Gupy) e Sky, Nokia e American Tower (Oracle HCM). Ficaram de fora: Oi (sem página de vagas ativa),
Ericsson (recusa robôs), Huawei e IHS Towers (sem lista pública de vagas no Brasil), Desktop (Pandapé,
não testada a fundo) e Ligga (o site não respondeu).
"""

import logging

from .base import Cliente, Local, Vaga
from .seguradoras import parse_gupy
from .tecnologia import _oracle

NOME = "Telecom"
log = logging.getLogger(__name__)

# subdomínio do Gupy -> nome da empresa
GUPY = {
    "vivo": "Vivo",
    "vempraclaro": "Claro",
    "vemprotime": "TIM",
    "vtal": "V.tal",
    "algar": "Algar Telecom",
    "brisanet": "Brisanet",
    "allohafibra": "Giga+ (Alloha Fibra)",
    "vero": "Vero Internet",
    "nio": "Nio",
    "vemserunifique": "Unifique",
}
# Oracle HCM: empresa -> (servidor, site, página pública das vagas)
ORACLE_HCM = {
    "Sky": ("https://egky.fa.us6.oraclecloud.com", "CX_5001",
            "https://egky.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/pt-BR/sites/CX_5001/job/{id}"),
    "Nokia": ("https://fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com", "CX_1",
              "https://fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/{id}"),
    "American Tower": ("https://hdsn.fa.us6.oraclecloud.com", "CX_1",
                       "https://hdsn.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/{id}"),
}


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME))
               for sub in GUPY]
    tarefas += [(empresa, lambda empresa=empresa: _oracle(cliente, empresa, ORACLE_HCM)) for empresa in ORACLE_HCM]
    vagas = []
    for nome, tarefa in tarefas:
        try:
            vagas += tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Telecom: falha em %s: %s", nome, erro)
    for v in vagas:
        v.fonte = NOME
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_telecom_lidas", False):
        return []
    cliente._telecom_lidas = True
    return coletar(cliente)
