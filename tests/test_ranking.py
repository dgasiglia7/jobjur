from datetime import date

from jobjur.coleta import deduplicar
from jobjur.fontes import Vaga
from jobjur.perfil import Perfil
from jobjur.ranking import Avaliacao, nota_por_regras, ranquear

PERFIL = Perfil(
    nome="Teste", cidade="Rio de Janeiro", uf="RJ", anos_experiencia=15, senioridade="sênior",
    areas_atuacao=["contratos", "compliance", "contencioso estratégico"], setores=["seguros"],
    tipo_atuacao=["jurídico interno"], formacao=[], certificacoes=[], idiomas=[], experiencias=[],
    cargos_alvo=["Advogada Sênior"], palavras_chave=["contratos", "compliance", "seguros"],
)
HOJE = date(2026, 10, 30)


def vaga(titulo, local="Rio de Janeiro - RJ", **kw):
    return Vaga(fonte="X", titulo=titulo, url=f"https://x/{titulo}/{local}", local=local, **kw)


def test_vaga_nao_juridica_fica_de_fora():
    assert nota_por_regras(vaga("Analista de Marketing"), PERFIL, HOJE) == 0


def test_senioridade_e_area_pesam():
    senior = nota_por_regras(vaga("Advogado Sênior - Contratos e Compliance"), PERFIL, HOJE)
    junior = nota_por_regras(vaga("Advogado Júnior - Contratos"), PERFIL, HOJE)
    assert senior > junior


def test_localizacao():
    rio = nota_por_regras(vaga("Advogado Sênior", "Rio de Janeiro - RJ"), PERFIL, HOJE)
    remoto = nota_por_regras(vaga("Advogado Sênior", "São Paulo - SP", modalidade="remoto"), PERFIL, HOJE)
    sp = nota_por_regras(vaga("Advogado Sênior", "São Paulo - SP", modalidade="presencial"), PERFIL, HOJE)
    assert rio > remoto > sp


def test_deduplicar_mesma_vaga_em_sites_diferentes():
    a = Vaga(fonte="Gupy", titulo="Advogado(a) Sênior", empresa="Acme", url="https://a")
    b = Vaga(fonte="LinkedIn", titulo="Advogado(a)  Sênior", empresa="ACME", url="https://b")
    assert deduplicar([a, b]) == [a]


def test_ranquear_sem_claude_ordena_e_filtra():
    vagas = [vaga("Advogado Júnior"), vaga("Vendedor"), vaga("Advogado Sênior de Compliance")]
    resultado = ranquear(vagas, PERFIL, usar_claude=False)
    assert [v.titulo for v in resultado] == ["Advogado Sênior de Compliance", "Advogado Júnior"]


def test_ranquear_com_claude_usa_nota_do_modelo(monkeypatch):
    def falso(vagas, perfil):
        return [Avaliacao(indice=i, nota=10 * (i + 1), motivo="ok") for i in range(len(vagas))]

    monkeypatch.setattr("jobjur.ranking.avaliar_com_claude", falso)
    vagas = [vaga("Advogado Sênior de Compliance"), vaga("Advogado Júnior")]
    resultado = ranquear(vagas, PERFIL, usar_claude=True)
    assert [v.titulo for v in resultado] == ["Advogado Júnior", "Advogado Sênior de Compliance"]
    assert resultado[0].extras["motivo"] == "ok"


def test_avaliar_com_claude_em_lotes():
    from types import SimpleNamespace

    from jobjur.ranking import Avaliacoes, avaliar_com_claude

    chamadas = []

    def parse(**kw):
        chamadas.append(kw)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=Avaliacoes(
            avaliacoes=[Avaliacao(indice=0, nota=70, motivo="combina"), Avaliacao(indice=99, nota=1, motivo="x")]))

    cliente = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))
    vagas = [vaga(f"Advogado {i}") for i in range(3)]
    resultado = avaliar_com_claude(vagas, PERFIL, client=cliente, lote=2)
    assert len(chamadas) == 2
    assert [a.nota if a else None for a in resultado] == [70, None, 70]
