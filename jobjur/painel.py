"""Mantém docs/vagas.json, a lista de vagas do painel publicado no GitHub Pages.

Cada busca acrescenta as vagas novas com nota suficiente; as que já estão no painel
não são alteradas, para não perder anotações feitas à mão. O status de candidatura
(currículo enviado, cadastrada...) fica em outro arquivo, docs/status.json, que só o
painel escreve, então a busca nunca apaga o que a Daniele marcou.

uso: python -m jobjur.painel dados/vagas-AAAA-MM-DD-HHhMM.json [--painel docs/vagas.json]
     python -m jobjur.painel verificar [--painel docs/vagas.json] [--status docs/status.json]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .encerradas import encerrada
from .fontes.base import Cliente, slug

FUSO = ZoneInfo("America/Sao_Paulo")
PAINEL_PADRAO = Path("docs/vagas.json")
STATUS_PADRAO = Path("docs/status.json")
NOTA_MINIMA = 65


def id_vaga(titulo: str, empresa: str) -> str:
    return slug(f"{titulo}-{empresa}")[:80].strip("-")


def regiao(local: str, modalidade: str = "") -> str:
    """rj para Rio de Janeiro e vagas remotas, sp para São Paulo, outra para o resto."""
    texto = slug(f"{local} {modalidade}")
    partes = set(texto.split("-"))
    if "remoto" in partes or "remote" in partes or "home-office" in texto:
        return "rj"
    if "rio-de-janeiro" in texto or "rj" in partes:
        return "rj"
    if "sao-paulo" in texto or "sp" in partes:
        return "sp"
    return "outra"


def grupo(nota: int, reg: str) -> str:
    if reg == "rj":
        return "top" if nota >= 75 else "ressalvas"
    return "sp" if reg == "sp" else "outras"


def entrada(vaga: dict, quando: datetime) -> dict:
    """Converte uma vaga do resultado da busca para o formato do painel."""
    extras = vaga.get("extras", {})
    nota = int(extras.get("nota", 0))
    reg = regiao(vaga.get("local", ""), vaga.get("modalidade", ""))
    return {
        "titulo": vaga["titulo"],
        "empresa": vaga.get("empresa", ""),
        "local": vaga.get("local", ""),
        "modalidade": vaga.get("modalidade", ""),
        "publicada": vaga.get("publicada", ""),
        "fonte": vaga["fonte"],
        "url": vaga["url"],
        "grupo": grupo(nota, reg),
        "regiao": reg,
        "nota": nota,
        "combina": extras.get("motivo", ""),
        "atencao": "",
        "adicionada_em": quando.isoformat(timespec="minutes"),
        "encerrada": False,
        "revisada": False,
    }


def ler(caminho: Path) -> dict:
    if not caminho.exists():
        return {"atualizado_em": "", "vagas": {}}
    return json.loads(caminho.read_text(encoding="utf-8"))


def atualizar(vagas: list[dict], caminho: Path = PAINEL_PADRAO, minimo: int = NOTA_MINIMA,
              quando: datetime | None = None) -> int:
    """Acrescenta ao painel as vagas com nota >= minimo que ainda não estão lá. Devolve quantas entraram."""
    quando = quando or datetime.now(FUSO)
    painel = ler(caminho)
    existentes = painel["vagas"]
    urls = {v["url"] for v in existentes.values()}
    novas = 0
    for vaga in vagas:
        if vaga.get("extras", {}).get("nota", 0) < minimo or vaga["url"] in urls:
            continue
        chave = id_vaga(vaga["titulo"], vaga.get("empresa", ""))
        if chave in existentes:
            continue
        existentes[chave] = entrada(vaga, quando)
        urls.add(vaga["url"])
        novas += 1
    painel["atualizado_em"] = quando.isoformat(timespec="minutes")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    salvar(painel, caminho)
    return novas


def salvar(painel: dict, caminho: Path) -> None:
    caminho.write_text(json.dumps(painel, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def verificar(caminho: Path = PAINEL_PADRAO, caminho_status: Path = STATUS_PADRAO,
              cliente: Cliente | None = None, quando: datetime | None = None, checar=encerrada) -> int:
    """Confere nos sites as vagas que a pessoa ainda não marcou (sem status ou Pendente).

    Vaga fechada, congelada ou vencida vira encerrada; vaga que o site reabriu volta a ficar aberta
    (e no painel volta para Pendente). O que a pessoa marcou à mão, inclusive "Encerrado", fica como
    está. Devolve quantas vagas mudaram.
    """
    quando = quando or datetime.now(FUSO)
    cliente = cliente or Cliente()
    painel = ler(caminho)
    status = json.loads(caminho_status.read_text(encoding="utf-8")) if caminho_status.exists() else {}
    agora = quando.isoformat(timespec="minutes")
    mudaram = 0
    for chave, vaga in painel["vagas"].items():
        if status.get(chave, {}).get("status", "pendente") != "pendente":
            continue
        try:
            fechada = checar(cliente, vaga["url"], quando.date())
        except Exception as erro:  # um site com página estranha não pode parar a verificação
            logging.warning("Não consegui verificar %s: %s", vaga["url"], erro)
            continue
        if fechada is None or bool(fechada) == bool(vaga.get("encerrada")):
            continue
        vaga["encerrada"] = bool(fechada)
        if fechada:
            vaga["encerrada_em"] = agora
            logging.info("Encerrada: %s (%s)", vaga["titulo"], vaga["url"])
        else:
            vaga.pop("encerrada_em", None)
            vaga["reaberta_em"] = agora
            logging.info("Reaberta: %s (%s)", vaga["titulo"], vaga["url"])
        mudaram += 1
    salvar(painel, caminho)
    return mudaram


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if sys.argv[1:2] == ["verificar"]:
        parser = argparse.ArgumentParser(prog="python -m jobjur.painel verificar",
                                         description="Marca as vagas pendentes encerradas nos sites e reabre as que voltaram.")
        parser.add_argument("--painel", type=Path, default=PAINEL_PADRAO)
        parser.add_argument("--status", type=Path, default=STATUS_PADRAO)
        args = parser.parse_args(sys.argv[2:])
        print(f"{verificar(args.painel, args.status)} vagas mudaram de situação")
        return
    parser = argparse.ArgumentParser(description="Acrescenta ao painel as vagas de uma busca.")
    parser.add_argument("resultado", type=Path, help="JSON gerado por python -m jobjur.buscar")
    parser.add_argument("--painel", type=Path, default=PAINEL_PADRAO)
    parser.add_argument("--nota-minima", type=int, default=NOTA_MINIMA)
    args = parser.parse_args()
    vagas = json.loads(args.resultado.read_text(encoding="utf-8"))
    print(f"{atualizar(vagas, args.painel, args.nota_minima)} vagas novas no painel")


if __name__ == "__main__":
    main()
