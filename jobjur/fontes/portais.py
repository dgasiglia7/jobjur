"""Portais de vagas e consultorias de recrutamento da planilha "Empresas e Sites para cadastrar o currículo".

Testados em 2026-11-13. A busca nesses sites é fixa ("advogado" e "jurídico"), então a coleta roda uma vez por
busca e guarda só as vagas da área jurídica.

Lidos: Michael Page (inclui Page Personnel, que redireciona para lá), Randstad, Curriculum, 99jobs, Grupo Selpe,
Winner RH (Gupy), Jobcenter e Resch (lista de vagas da empresa no Vagas.com).
Os demais da planilha que já estavam na busca: Catho, Empregos.com.br, Gupy, InfoJobs, LinkedIn, Trabalha Brasil
e Vagas.com (Indeed só pelo conector, nas conversas).
Ficaram de fora: Glassdoor (bloqueia robôs), Hays, Abler, BURH, Sólides (Fox, Interage), Selecty (Manpower,
Novo Tempo), JobConvo (Adecco), Remotar e Clique Empregos (a lista só carrega no navegador), Across, Agnis,
Contratando, Bettha, Qualita, IAPSIC e Maturi (fora do ar ou com verificação anti-robô), Cia de Talentos, AZ Consult,
HireNow, Evolk, Talento Sênior, Afamar, Imediatta e APInfo (sem vagas jurídicas ou sem lista pública), Nube e
Walljobs (só estágio) e Sales Jobs (só vendas).
"""

import html as html_lib
import json
import logging
import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar
from .construcao import parse_vagas_com
from .seguradoras import eh_juridica, parse_gupy

NOME = "Portais (planilha)"
log = logging.getLogger(__name__)

TERMOS = ("advogado", "jurídico")
GUPY = {"winnerrh": "Winner RH"}
VAGAS_COM = {"jobcenter": ("jobcenter", "Jobcenter do Brasil"), "resch": ("resch", "Resch Recursos Humanos")}


def _juridicas(vagas: list[Vaga]) -> list[Vaga]:
    return [v for v in vagas if eh_juridica(v.titulo)]


def parse_michael_page(html: str) -> list[Vaga]:
    vagas = []
    for tile in BeautifulSoup(html, "html.parser").select("div.job-tile"):
        link = tile.select_one(".job-title a[href]")
        if not link:
            continue
        local, resumo = tile.select_one(".job-location"), tile.select_one(".job_advert__job-summary-text")
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(link.get_text()),
            url="https://www.michaelpage.com.br" + link["href"],
            empresa="Michael Page (cliente confidencial)",
            local=limpar(local.get_text()) if local else "",
            descricao=limpar(resumo.get_text()) if resumo else "",
        ))
    return _juridicas(vagas)


def parse_randstad(html: str) -> list[Vaga]:
    i = html.find("window.__ROUTE_DATA__")
    if i < 0:
        return []
    dados, _ = json.JSONDecoder().raw_decode(html[html.index("{", i):])
    vagas = []
    for hit in (((dados.get("searchResults") or {}).get("hits") or {}).get("hits") or []):
        fonte = hit.get("_source") or {}
        info, lugar, url = fonte.get("JobInformation") or {}, fonte.get("JobLocation") or {}, fonte.get("BlueXSanitized") or {}
        titulo = limpar(info.get("Title"))
        if not titulo or not url.get("Title"):
            continue
        vagas.append(Vaga(
            fonte=NOME,
            titulo=titulo,
            url=f"https://www.randstad.com.br/vagas/{url['Title']}_{url.get('City', '')}_{hit.get('_id')}/",
            empresa="Randstad (cliente)",
            local=", ".join(p for p in (limpar(lugar.get("City")), limpar(lugar.get("Region"))) if p),
        ))
    return _juridicas(vagas)


def parse_curriculum(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("a.card[href]"):
        titulo = card.select_one(".card-titulo")
        if not titulo or "/vagas/vaga/" not in card["href"]:
            continue
        meta = [limpar(p) for p in (card.select_one(".card-meta").get_text() if card.select_one(".card-meta") else "").split("·")]
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(titulo.get_text()),
            url="https://www.curriculum.com.br" + card["href"],
            empresa=meta[0] if meta else "",
            local=meta[1] if len(meta) > 1 else "",
            modalidade=meta[2] if len(meta) > 2 else "",
        ))
    return _juridicas(vagas)


def parse_99jobs(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("a.opportunity-card[href]"):
        titulo = limpar(card.h1.get_text()) if card.h1 else ""
        url = card["href"].split("?")[0]
        if titulo.endswith("..."):  # a listagem corta títulos longos; o endereço tem o título inteiro
            trecho = re.sub(r"^\d+-", "", url.rsplit("/", 1)[-1])
            titulo = limpar(unquote(trecho).replace("-", " ")).capitalize()
        titulo = re.sub(r"^\W+", "", titulo)
        nivel, modo = card.select_one(".opportunity-label-level"), card.select_one(".opportunity-label-acting-mode")
        lugar, empresa = card.select_one(".opportunity-address p"), card.select_one(".opportunity-company-infos h2")
        local = limpar(lugar.get_text()) if lugar else ""
        vagas.append(Vaga(
            fonte=NOME,
            titulo=titulo,
            url=url,
            empresa=limpar(empresa.get_text()) if empresa else "",
            local="" if local == "Não informado" else local,
            modalidade=limpar(modo.get_text()) if modo else "",
            extras={"nivel": limpar(nivel.get_text())} if nivel else {},
        ))
    return _juridicas(vagas)


def parse_selpe(html: str) -> list[Vaga]:
    texto = html_lib.unescape(html)
    i = texto.find('"listaVagas":')
    if i < 0:
        return []
    dados, _ = json.JSONDecoder().raw_decode(texto[i + len('"listaVagas":'):])
    vagas = []
    for v in dados.get("vagas") or []:
        titulo = limpar(v.get("titulo"))
        if not titulo or not v.get("url"):
            continue
        cidade = "" if v.get("hideCidade") else limpar(v.get("nomeCidade"))
        uf = "" if v.get("hideEstado") else limpar(v.get("siglaEstado"))
        vagas.append(Vaga(
            fonte=NOME,
            titulo=titulo,
            url=v["url"],
            empresa="Grupo Selpe (cliente)",
            local="/".join(p for p in (cidade, uf) if p),
            modalidade=limpar(v.get("regime")),
            descricao=limpar(v.get("atividades"))[:500],
        ))
    return _juridicas(vagas)


def coletar(cliente: Cliente) -> list[Vaga]:
    tarefas = [
        ("Michael Page", lambda: parse_michael_page(cliente.get("https://www.michaelpage.com.br/jobs/juridico"))),
        ("Randstad", lambda: parse_randstad(cliente.get("https://www.randstad.com.br/vagas/s-juridico/"))),
        ("Grupo Selpe", lambda: parse_selpe(cliente.get("https://vagas.recrutamentointeligente.net/gruposelpe"))),
    ]
    # o Curriculum só tem página para cargos ("jurídico" dá 404)
    tarefas.append(("Curriculum", lambda: parse_curriculum(cliente.get("https://www.curriculum.com.br/vagas/de/advogado"))))
    for termo in TERMOS:
        tarefas.append((f"99jobs {termo}", lambda termo=termo: parse_99jobs(
            cliente.get("https://www.99jobs.com/opportunities/filtered_search", **{"search[term]": termo}))))
    tarefas += [(sub, lambda sub=sub: parse_gupy(cliente.get(f"https://{sub}.gupy.io/"), sub, GUPY, NOME)) for sub in GUPY]
    tarefas += [(busca, lambda busca=busca: parse_vagas_com(cliente.get(f"https://www.vagas.com.br/vagas-de-{busca}"),
                                                            *VAGAS_COM[busca])) for busca in VAGAS_COM]
    vagas, vistas = [], set()
    for nome, tarefa in tarefas:
        try:
            novas = tarefa()
        except Exception as erro:  # um site fora do ar não deve parar os outros
            log.warning("Portais: falha em %s: %s", nome, erro)
            continue
        for v in novas:
            if v.url in vistas:  # "advogado" e "jurídico" trazem as mesmas vagas
                continue
            vistas.add(v.url)
            v.fonte = NOME
            vagas.append(v)
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    # a busca chama cada fonte para vários termos e locais; aqui basta ler os sites uma vez
    if getattr(cliente, "_portais_lidos", False):
        return []
    cliente._portais_lidos = True
    return coletar(cliente)
