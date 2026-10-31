"""InfoJobs; 20 vagas por página.

O InfoJobs filtra por cidade pelo endereço (ex.: empregos-em-rio-janeiro.aspx). Quando não reconhece
a cidade, devolve vagas do Brasil todo, que o ranking depois pontua pela localização.
"""

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "InfoJobs"


def parse(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("div.js_vacancyLoad"):
        titulo = card.select_one(".js_vacancyTitle")
        if not titulo:
            continue
        empresa = card.select_one("a[href*='/empresa-']")
        local = card.select_one("div.mb-8")
        if local and (distancia := local.select_one(".js_divUserVagaDistance")):
            distancia.extract()
        data = card.select_one(".js_date")
        detalhes = [limpar(d.get_text()) for d in card.select("div.d-inline-flex > div")]
        descricao = card.find_all("div", class_="text-medium", recursive=False)
        vagas.append(Vaga(
            fonte=NOME,
            titulo=limpar(titulo.get_text()),
            url="https://www.infojobs.com.br" + card["data-href"],
            empresa=limpar(empresa.get_text()) if empresa else "",
            local=limpar(local.get_text()) if local else "",
            publicada=data["data-value"][:10].replace("/", "-") if data else "",
            descricao=limpar(descricao[-1].get_text()) if descricao else "",
            salario=next((d for d in detalhes if "R$" in d), ""),
            modalidade=next((d.lower() for d in detalhes if d.lower() in {"presencial", "híbrido", "remoto"}), ""),
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2) -> list[Vaga]:
    caminho = f"empregos-em-{slug(local.cidade, sem_preposicoes=True)}.aspx" if local else "empregos.aspx"
    vagas = []
    for pagina in range(1, paginas + 1):
        novas = parse(cliente.get(f"https://www.infojobs.com.br/{caminho}", palabra=termo, page=pagina))
        vagas += novas
        if len(novas) < 20:
            break
    return vagas
