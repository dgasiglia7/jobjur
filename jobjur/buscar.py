"""Busca diária: coleta vagas, ranqueia contra o perfil e salva o resultado em dados/.

uso: python -m jobjur.buscar dados/perfil.json [--termos "advogado,compliance"] [--sem-claude]
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .coleta import coletar
from . import painel
from .fontes import FONTES, Local, Vaga
from .perfil import Perfil
from .ranking import ranquear

TERMOS_PADRAO = ["advogado", "jurídico"]
FUSO = ZoneInfo("America/Sao_Paulo")


def termos_do_perfil(perfil: Perfil, maximo: int = 10) -> list[str]:
    """Termos amplos primeiro (trazem mais vagas), depois as palavras-chave do perfil."""
    termos = []
    for termo in TERMOS_PADRAO + perfil.palavras_chave:
        if termo.lower() not in termos:
            termos.append(termo.lower())
    return termos[:maximo]


def relatorio(vagas: list[Vaga], perfil: Perfil, minimo: int, quando: datetime) -> str:
    linhas = [f"# Vagas para {perfil.nome}", "", f"Gerado em {quando:%d/%m/%Y às %H:%M} (horário de Brasília).", ""]
    boas = [v for v in vagas if v.extras["nota"] >= minimo]
    linhas.append(f"{len(boas)} vagas com nota a partir de {minimo}, de {len(vagas)} vagas jurídicas encontradas.")
    for v in boas:
        novidade = " 🆕" if v.extras.get("nova") else ""
        detalhes = " · ".join(x for x in (v.empresa, v.local, v.modalidade, v.salario, v.fonte) if x)
        linhas += ["", f"## {v.extras['nota']} · [{v.titulo}]({v.url}){novidade}", detalhes]
        if v.extras.get("motivo"):
            linhas.append(f"> {v.extras['motivo']}")
    return "\n".join(linhas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Busca e ranqueia vagas jurídicas para um perfil.")
    parser.add_argument("perfil", type=Path, help="perfil.json gerado por python -m jobjur.perfil")
    parser.add_argument("--termos", help="termos de busca separados por vírgula (padrão: a partir do perfil)")
    parser.add_argument("--fontes", help=f"sites separados por vírgula (padrão: {', '.join(FONTES)})")
    parser.add_argument("--sem-claude", action="store_true", help="usar só a nota por regras")
    parser.add_argument("--nota-minima", type=int, default=60, help="nota mínima para entrar no relatório")
    parser.add_argument("--saida", type=Path, default=Path("dados"), help="pasta de saída")
    parser.add_argument("--painel", type=Path, help="também acrescenta as vagas boas a este vagas.json do painel")
    parser.add_argument("--nota-painel", type=int, default=painel.NOTA_MINIMA, help="nota mínima para entrar no painel")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    perfil = Perfil.model_validate_json(args.perfil.read_text(encoding="utf-8"))
    termos = [t.strip() for t in args.termos.split(",")] if args.termos else termos_do_perfil(perfil)
    fontes = [f.strip() for f in args.fontes.split(",")] if args.fontes else None
    logging.info("Buscando %s", ", ".join(termos))

    vagas = ranquear(coletar(termos, Local(perfil.cidade, perfil.uf), fontes), perfil,
                     usar_claude=False if args.sem_claude else None)

    args.saida.mkdir(parents=True, exist_ok=True)
    historico_arq = args.saida / "historico.json"
    historico = set(json.loads(historico_arq.read_text())) if historico_arq.exists() else set()
    for v in vagas:
        v.extras["nova"] = v.url not in historico
    historico_arq.write_text(json.dumps(sorted(historico | {v.url for v in vagas}), indent=0))

    quando = datetime.now(FUSO)
    base = args.saida / f"vagas-{quando:%Y-%m-%d-%Hh%M}"
    base.with_suffix(".json").write_text(
        json.dumps([v.to_dict() for v in vagas], ensure_ascii=False, indent=2), encoding="utf-8")
    base.with_suffix(".md").write_text(relatorio(vagas, perfil, args.nota_minima, quando), encoding="utf-8")
    logging.info("%d vagas jurídicas ranqueadas. Relatório em %s", len(vagas), base.with_suffix(".md"))
    if args.painel:
        novas = painel.atualizar([v.to_dict() for v in vagas], args.painel, args.nota_painel, quando)
        logging.info("%d vagas novas no painel %s", novas, args.painel)


if __name__ == "__main__":
    main()
