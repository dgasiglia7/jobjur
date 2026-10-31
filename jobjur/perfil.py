"""Lê um currículo em PDF e extrai o perfil profissional usado na busca de vagas."""

import base64
import json
import os
import sys
from pathlib import Path

import anthropic
from pydantic import BaseModel, Field

MODELO = "claude-opus-5-5"
# Nome próprio para a chave, para que o Claude Code no mesmo ambiente não a use no lugar da assinatura
VARIAVEL_CHAVE = "JOBJUR_API_KEY"


def tem_chave() -> bool:
    return bool(os.environ.get(VARIAVEL_CHAVE) or os.environ.get("ANTHROPIC_API_KEY"))


def cliente_claude() -> anthropic.Anthropic:
    """Usa JOBJUR_API_KEY quando definida; senão, as credenciais padrão do SDK (ANTHROPIC_API_KEY etc.)."""
    chave = os.environ.get(VARIAVEL_CHAVE)
    return anthropic.Anthropic(api_key=chave) if chave else anthropic.Anthropic()


class Experiencia(BaseModel):
    empresa: str
    cargo: str
    inicio: str = Field(description="Mês/ano de início, ex.: 2018-11")
    fim: str = Field(description="Mês/ano de fim, ou 'atual'")


class Perfil(BaseModel):
    nome: str
    cidade: str
    uf: str
    anos_experiencia: int
    senioridade: str = Field(description="estagiário, júnior, pleno, sênior, especialista, coordenação ou gerência")
    areas_atuacao: list[str] = Field(description="Áreas do Direito em que atua, ex.: contratos, contencioso cível, compliance")
    setores: list[str] = Field(description="Setores de mercado da experiência, ex.: seguros, tecnologia")
    tipo_atuacao: list[str] = Field(description="jurídico interno (in-house), escritório, setor público")
    formacao: list[str]
    certificacoes: list[str]
    idiomas: list[str]
    experiencias: list[Experiencia]
    cargos_alvo: list[str] = Field(description="Títulos de vaga compatíveis com o perfil, como aparecem em anúncios")
    palavras_chave: list[str] = Field(description="Termos para buscar vagas nos sites")


INSTRUCAO = (
    "Você recebe o currículo de um profissional do Direito no Brasil. Extraia o perfil "
    "profissional para alimentar uma busca automática de vagas. Não inclua telefone, "
    "e-mail, endereço completo nem referências pessoais. Em cargos_alvo e palavras_chave, "
    "use os termos que recrutadores brasileiros usam em anúncios de vagas jurídicas."
)


def extrair_perfil(caminho_pdf: Path, client: anthropic.Anthropic | None = None) -> Perfil:
    client = client or cliente_claude()
    pdf_b64 = base64.standard_b64encode(caminho_pdf.read_bytes()).decode()
    resposta = client.beta.messages.parse(
        model=MODELO,
        max_tokens=16000,
        output_config={"effort": "medium"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": INSTRUCAO},
            ],
        }],
        output_format=Perfil,
    )
    if resposta.stop_reason == "refusal":
        raise RuntimeError("O modelo recusou a extração do currículo.")
    return resposta.parsed_output


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("uso: python -m jobjur.perfil <curriculo.pdf> <saida.json>")
    perfil = extrair_perfil(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(perfil.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Perfil salvo em {sys.argv[2]}")


if __name__ == "__main__":
    main()
