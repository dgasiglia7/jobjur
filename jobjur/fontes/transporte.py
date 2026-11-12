"""Páginas de carreira das maiores empresas de transporte terrestre do Brasil (ferrovias, rodovias,
transportadoras, ônibus, metrô e locadoras de veículos).

Testadas em 2026-11-12. Como nas seguradoras, cada página lista todas as vagas da empresa, então a coleta
roda uma vez por busca e guarda só as vagas da área jurídica.

Lidas: Rumo, Brado, JSL, Simpar, Vamos, Tegma, Rodonaves, Carvalima, Motiva (antiga CCR), EcoRodovias,
Guanabara, Grupo Comporte, ClickBus, Localiza, Movida e Expresso São Miguel (Gupy), MRS Logística, Patrus,
Braspress, Jadlog e Total Express (Pandapé), Loggi (InHire) e Grupo JCA (Auto Viação 1001), MetrôRio e DHL Express (lista de vagas da empresa no Vagas.com).
Ficaram de fora: VLI (o site não respondeu), Buser, Jamef, Gontijo e Águia Branca (sem lista pública de vagas).
"""

import logging

from .base import Cliente, Local, Vaga
from .construcao import ler_pandape, parse_vagas_com
from .seguradoras import parse_gupy, parse_inhire

NOME = "Transporte"
log = logging.getLogger(__name__)

GUPY = {
    "rumolog": "Rumo",
    "bradologistica": "Brado Logística",
    "jsl": "JSL",
    "simpar": "Simpar",
    "vamos": "Grupo Vamos",
    "tegma": "Tegma",
    "rodonaves": "Grupo Rodonaves",
    "carvalima": "Carvalima Transportes",
    "motiva": "Motiva",
    "ecorodovias": "EcoRodovias",
    "guanabara": "Grupo Guanabara",
    "itamarati": "Grupo Comporte",
    "clickbus": "ClickBus",
    "localiza": "Localiza&Co",
    "movida": "Movida",
    "sejaesm": "Expresso São Miguel",
}
PANDAPE = {"mrs": "MRS Logística", "patrustransportes": "Patrus Transportes", "braspress": "Braspress", "jadlog": "Jadlog", "totalexpress": "Total Express"}
# Vagas.com: busca pelo nome da empresa -> (trecho do nome da empresa no anúncio, empresa)
VAGAS_COM = {
    "jca": ("jca", "Grupo JCA (Auto Viação 1001)"),
    "metrorio": ("metr", "MetrôRio"),
    "dhl": ("dhl", "DHL Express"),
}


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME))
               for sub in GUPY]
    tarefas += [(sub, lambda sub=sub: ler_pandape(cliente, sub, PANDAPE[sub])) for sub in PANDAPE]
    tarefas += [(busca, lambda busca=busca: parse_vagas_com(cliente.get(f"https://www.vagas.com.br/vagas-de-{busca}"),
                                                            *VAGAS_COM[busca])) for busca in VAGAS_COM]
    tarefas.append(("loggi", lambda: parse_inhire(cliente.json("https://api.inhire.app/job-posts/public/pages",
                                                               cabecalhos={"X-Tenant": "loggi"}), "loggi", "Loggi")))
    vagas = []
    for nome, tarefa in tarefas:
        try:
            novas = tarefa()
        except Exception as erro:  # uma página fora do ar não deve parar as outras
            log.warning("Transporte: falha em %s: %s", nome, erro)
            continue
        for v in novas:
            v.fonte = NOME
        vagas += novas
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler as páginas uma vez
    if getattr(cliente, "_transporte_lidas", False):
        return []
    cliente._transporte_lidas = True
    return coletar(cliente)
