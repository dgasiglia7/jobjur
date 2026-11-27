"""Recalcula a nota de todas as vagas do painel quando o perfil muda (por exemplo, currículo novo).

A nota de cada vaga é calculada no dia em que ela entra no painel. Quando o perfil muda, as notas
antigas ficam desatualizadas, então a busca guarda uma impressão digital (hash) do perfil em
docs/vagas.json e, se o perfil da vez for diferente, recalcula todas as vagas com o perfil novo.
Só mudam a nota e o grupo; status, favoritas e anotações ficam em docs/status.json e não são tocados.

Para recalcular, a busca guarda o texto de cada vaga do painel em historico/descricoes.json sempre
que a encontra. Vagas sem texto guardado (as que entraram antes disso e não apareceram de novo) são
recalculadas pelo título, local e data, e nesse caso a nota não desce, porque faltam dados para
pontuar a descrição.

uso: python -m jobjur.recalculo dados/perfil.json [--forcar]
"""

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from . import painel
from .fontes import Vaga
from .perfil import Perfil
from .ranking import nota_por_regras

DESCRICOES_PADRAO = Path("historico/descricoes.json")
TAMANHO_DESCRICAO = 3000


def hash_perfil(perfil: Perfil) -> str:
    return hashlib.sha256(perfil.model_dump_json().encode()).hexdigest()[:16]


def ler_descricoes(caminho: Path) -> dict[str, str]:
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}


def guardar_descricoes(vagas: list[dict], caminho_painel: Path = painel.PAINEL_PADRAO,
                       caminho: Path = DESCRICOES_PADRAO) -> None:
    """Guarda o texto das vagas encontradas nesta busca que estão no painel."""
    existentes = painel.ler(caminho_painel)["vagas"]
    por_url = {v["url"]: chave for chave, v in existentes.items()}
    descricoes = ler_descricoes(caminho)
    for vaga in vagas:
        chave = por_url.get(vaga["url"])
        if chave is None:
            chave = painel.id_vaga(vaga["titulo"], vaga.get("empresa", ""))
            if chave not in existentes:
                continue
        descricoes[chave] = (vaga.get("descricao") or "")[:TAMANHO_DESCRICAO]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(descricoes, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")


def _dia(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto[:10])
    except (TypeError, ValueError):
        return None


def recalcular(perfil: Perfil, caminho_painel: Path = painel.PAINEL_PADRAO,
               caminho_descricoes: Path = DESCRICOES_PADRAO, forcar: bool = False) -> int | None:
    """Recalcula as notas se o perfil mudou desde o último cálculo. Devolve quantas notas mudaram,
    ou None se o perfil é o mesmo e nada foi feito."""
    impressao = hash_perfil(perfil)
    dados = painel.ler(caminho_painel)
    if dados.get("perfil_hash") == impressao and not forcar:
        return None
    descricoes = ler_descricoes(caminho_descricoes)
    mudaram = 0
    for chave, vaga in dados["vagas"].items():
        objeto = Vaga(fonte=vaga.get("fonte", ""), titulo=vaga["titulo"], url=vaga["url"],
                      empresa=vaga.get("empresa", ""), local=vaga.get("local", ""),
                      publicada=vaga.get("publicada", ""), modalidade=vaga.get("modalidade", ""),
                      descricao=descricoes.get(chave, ""))
        # a data de referência é a de entrada no painel, para o bônus de vaga recente valer como valeu
        nota = nota_por_regras(objeto, perfil, _dia(vaga.get("adicionada_em", "")))
        if chave not in descricoes:
            nota = max(nota, int(vaga.get("nota") or 0))
        if nota != vaga.get("nota"):
            mudaram += 1
        vaga["nota"] = nota
        vaga["grupo"] = painel.grupo(nota, vaga.get("regiao") or painel.regiao(vaga.get("local", ""), vaga.get("modalidade", "")))
    dados["perfil_hash"] = impressao
    painel.salvar(dados, caminho_painel)
    return mudaram


def main() -> None:
    parser = argparse.ArgumentParser(description="Recalcula as notas do painel quando o perfil muda.")
    parser.add_argument("perfil", type=Path)
    parser.add_argument("--painel", type=Path, default=painel.PAINEL_PADRAO)
    parser.add_argument("--descricoes", type=Path, default=DESCRICOES_PADRAO)
    parser.add_argument("--forcar", action="store_true", help="recalcula mesmo se o perfil não mudou")
    args = parser.parse_args()
    perfil = Perfil.model_validate_json(args.perfil.read_text(encoding="utf-8"))
    mudaram = recalcular(perfil, args.painel, args.descricoes, args.forcar)
    print("Perfil igual ao do último cálculo; notas mantidas." if mudaram is None
          else f"Perfil novo: notas recalculadas, {mudaram} mudaram.")


if __name__ == "__main__":
    main()
