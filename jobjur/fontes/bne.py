"""BNE (Banco Nacional de Empregos); 20 vagas por página."""

from bs4 import BeautifulSoup

from .base import Cliente, Local, Vaga, limpar, slug

NOME = "BNE"
MODALIDADES = {"presencial", "híbrido", "remoto", "home office"}


def parse(html: str) -> list[Vaga]:
    vagas = []
    for card in BeautifulSoup(html, "html.parser").select("div.card--list--vagas"):
        link = card.select_one("a.card__link")
        if not link:
            continue
        # itens na ordem: cargo, empresa (quando informada), modalidade, cidade/UF
        itens = [limpar(i.get_text()) for i in card.select(".info__vaga-item")]
        modalidade = next((i for i in itens if i.lower() in MODALIDADES), "")
        local = next((i for i in itens if "/" in i), "")
        outros = [i for i in itens[1:] if i not in (modalidade, local)]
        descricao = card.select_one(".info__vaga p")
        vagas.append(Vaga(
            fonte=NOME,
            titulo=itens[0] if itens else limpar(link.get_text()).removeprefix("Vaga De "),
            url=link["href"],
            empresa=outros[0] if outros else "",
            local=local,
            descricao=limpar(descricao.get_text()) if descricao else "",
            modalidade=modalidade.lower().replace("home office", "remoto"),
        ))
    return vagas


def buscar(cliente: Cliente, termo: str, local: Local | None = None, paginas: int = 2) -> list[Vaga]:
    url = f"https://www.bne.com.br/vagas-de-emprego-para-{slug(termo)}"
    if local:
        url += f"-em-{slug(local.cidade)}-{local.uf.lower()}"
    vagas = []
    for pagina in range(1, paginas + 1):
        novas = parse(cliente.get(url, Page=pagina) if pagina > 1 else cliente.get(url))
        vagas += novas
        if len(novas) < 20:
            break
    return vagas
