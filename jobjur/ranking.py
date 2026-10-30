"""Pontua cada vaga pela compatibilidade com o perfil do candidato.

Primeiro uma nota por regras (área, senioridade, localização, data), que funciona sem chave de API
e serve de filtro. Com JOBJUR_API_KEY (ou ANTHROPIC_API_KEY) definida, as melhores vagas são reavaliadas pelo Claude,
que dá uma nota de 0 a 100 e explica o motivo.
"""

import json
from datetime import date

import anthropic
from pydantic import BaseModel

from .fontes import Vaga
from .fontes.base import slug
from .perfil import MODELO, Perfil, cliente_claude, tem_chave

TERMOS_JURIDICOS = ("advog", "juridic", "compliance", "legal", "lawyer", "counsel", "paralegal",
                    "contencioso", "societari", "tributari", "trabalhist", "regulatori", "governanca")
NIVEL_BAIXO = ("estagi", "trainee", "junior", "jr", "assistente", "auxiliar", "aprendiz")
NIVEL_ALTO = ("senior", "sr", "especialista", "coordenador", "coordenadora", "gerente", "head", "lider",
              "consultor", "consultora", "pleno-senior")
PALAVRAS_VAZIAS = {"de", "da", "do", "das", "dos", "e", "em", "com", "para", "a", "o", "incluindo", "gestao",
                   "advogado", "advogada", "juridico", "juridica", "direito"}


def _palavras(texto: str) -> set[str]:
    return set(slug(texto).split("-"))


def _palavras_perfil(perfil: Perfil) -> set[str]:
    textos = perfil.areas_atuacao + perfil.palavras_chave + perfil.setores
    return {p for t in textos for p in _palavras(t) if len(p) >= 3 and p not in PALAVRAS_VAZIAS}


def _tem(palavras: set[str], prefixos: tuple[str, ...]) -> bool:
    return any(p.startswith(x) for p in palavras for x in prefixos)


def eh_juridica(vaga: Vaga) -> bool:
    return _tem(_palavras(vaga.titulo), TERMOS_JURIDICOS)


def nota_por_regras(vaga: Vaga, perfil: Perfil, hoje: date | None = None) -> int:
    if not eh_juridica(vaga):
        return 0
    hoje = hoje or date.today()
    titulo, texto = _palavras(vaga.titulo), _palavras(f"{vaga.titulo} {vaga.descricao}")
    alvo = _palavras_perfil(perfil)
    nota = 40 + 8 * len(titulo & alvo) + 2 * len((texto - titulo) & alvo)

    senior = perfil.anos_experiencia >= 8 or slug(perfil.senioridade) in {"senior", "especialista", "coordenacao", "gerencia"}
    if senior:
        if _tem(titulo, NIVEL_BAIXO):
            nota -= 30
        if _tem(titulo, NIVEL_ALTO):
            nota += 15

    local = slug(vaga.local)
    remoto = "remot" in slug(f"{vaga.modalidade} {vaga.titulo}") or "home-office" in slug(vaga.titulo)
    if slug(perfil.cidade) in local:
        nota += 15
    elif remoto:
        nota += 10
    elif perfil.uf.lower() in local.split("-"):
        nota += 5
    elif local and local not in {"brasil", "brazil"}:
        nota -= 15

    if vaga.publicada:
        try:
            if (hoje - date.fromisoformat(vaga.publicada[:10])).days <= 7:
                nota += 5
        except ValueError:
            pass
    return max(0, min(100, nota))


class Avaliacao(BaseModel):
    indice: int
    nota: int
    motivo: str


class Avaliacoes(BaseModel):
    avaliacoes: list[Avaliacao]


INSTRUCAO = (
    "Você ajuda um profissional do Direito a encontrar vagas. Abaixo estão o perfil dele e uma lista "
    "numerada de vagas. Para cada vaga, dê uma nota de 0 a 100 para a compatibilidade com o perfil, "
    "considerando área do Direito, senioridade, setor, tipo de atuação (empresa ou escritório) e "
    "localização (vagas remotas servem para qualquer cidade; presenciais em outra cidade valem pouco). "
    "O motivo deve ter uma frase curta em português, dizendo o que combina e o que não combina."
)


def avaliar_com_claude(vagas: list[Vaga], perfil: Perfil, client: anthropic.Anthropic | None = None,
                       lote: int = 25) -> list[Avaliacao | None]:
    client = client or cliente_claude()
    resultado: list[Avaliacao | None] = [None] * len(vagas)
    perfil_json = perfil.model_dump_json(exclude={"nome", "experiencias"})
    for inicio in range(0, len(vagas), lote):
        trecho = vagas[inicio:inicio + lote]
        lista = json.dumps([
            {"indice": i, "titulo": v.titulo, "empresa": v.empresa, "local": v.local, "modalidade": v.modalidade,
             "salario": v.salario, "descricao": v.descricao[:600]}
            for i, v in enumerate(trecho)
        ], ensure_ascii=False)
        resposta = client.beta.messages.parse(
            model=MODELO,
            max_tokens=16000,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": f"{INSTRUCAO}\n\nPerfil:\n{perfil_json}\n\nVagas:\n{lista}"}],
            output_format=Avaliacoes,
        )
        if resposta.stop_reason == "refusal" or not resposta.parsed_output:
            continue
        for a in resposta.parsed_output.avaliacoes:
            if 0 <= a.indice < len(trecho):
                resultado[inicio + a.indice] = a
    return resultado


def ranquear(vagas: list[Vaga], perfil: Perfil, usar_claude: bool | None = None,
             limite_claude: int = 75) -> list[Vaga]:
    """Devolve as vagas jurídicas ordenadas pela nota, com a nota e o motivo em vaga.extras."""
    for vaga in vagas:
        vaga.extras["nota_regras"] = nota_por_regras(vaga, perfil)
    candidatas = sorted((v for v in vagas if v.extras["nota_regras"] > 0),
                        key=lambda v: v.extras["nota_regras"], reverse=True)
    for vaga in candidatas:
        vaga.extras["nota"] = vaga.extras["nota_regras"]

    if usar_claude is None:
        usar_claude = tem_chave()
    if usar_claude and candidatas:
        topo = candidatas[:limite_claude]
        for vaga, avaliacao in zip(topo, avaliar_com_claude(topo, perfil)):
            if avaliacao:
                vaga.extras["nota"] = max(0, min(100, avaliacao.nota))
                vaga.extras["motivo"] = avaliacao.motivo
    return sorted(candidatas, key=lambda v: v.extras["nota"], reverse=True)
