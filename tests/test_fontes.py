from datetime import date
from pathlib import Path

import pytest

from jobjur.fontes import FONTES, bne, catho, empregos_com, gupy, infojobs, linkedin, trabalha_brasil, vagas_com

FIXTURES = Path(__file__).parent / "fixtures"


def ler(nome: str) -> str:
    return (FIXTURES / f"{nome}.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("modulo", [gupy, linkedin, vagas_com, catho, infojobs, empregos_com, bne, trabalha_brasil])
def test_parse_extrai_campos_basicos(modulo):
    vagas = modulo.parse(ler(modulo.__name__.rsplit(".", 1)[-1]))
    assert len(vagas) == 2
    for vaga in vagas:
        assert vaga.fonte == modulo.NOME
        assert vaga.titulo and vaga.url.startswith("https://")
        assert vaga.local
        if modulo not in (bne, trabalha_brasil):  # esses dois não mostram a data na listagem
            date.fromisoformat(vaga.publicada)


def test_gupy():
    vaga = gupy.parse(ler("gupy"))[0]
    assert vaga.empresa == "Itaú Unibanco"
    assert vaga.local == "São Paulo, São Paulo"
    assert vaga.modalidade == "híbrido"
    assert "<" not in vaga.descricao


def test_linkedin_remove_rastreamento_da_url():
    vaga = linkedin.parse(ler("linkedin"))[0]
    assert vaga.empresa == "Bichara Advogados"
    assert "?" not in vaga.url


def test_vagas_com_sem_texto_de_ajuda_no_local():
    vaga = vagas_com.parse(ler("vagas_com"))[0]
    assert vaga.local == "Rio de Janeiro / RJ"
    assert vaga.publicada == "2026-09-30"
    assert vaga.extras["nivel"] == "Pleno"


def test_catho_data_e_salario():
    vaga = catho.parse(ler("catho"), hoje=date(2026, 10, 30))[0]
    assert vaga.local == "São Paulo"
    assert vaga.publicada == "2026-10-26"
    assert "R$ 3.000,00" in vaga.salario


def test_catho_data_do_ano_anterior():
    assert catho._data("Publicada em 28/12", date(2027, 1, 3)) == "2026-12-28"
    assert catho._data("Publicada Ontem", date(2027, 1, 1)) == "2026-12-31"


def test_infojobs_detalhes():
    vaga = infojobs.parse(ler("infojobs"))[0]
    assert vaga.local == "Porto Alegre - RS"
    assert vaga.salario.startswith("R$")
    assert vaga.modalidade == "presencial"


def test_todas_as_fontes_registradas():
    assert set(FONTES) == {"Gupy", "LinkedIn", "Vagas.com", "Catho", "InfoJobs", "Empregos.com.br", "BNE",
                           "Trabalha Brasil"}


def test_empregos_com():
    vaga = empregos_com.parse(ler("empregos_com"), hoje=date(2026, 10, 30))[0]
    assert vaga.url == "https://www.empregos.com.br/vaga/11975900/advogadoa-em-registro-sp"
    assert vaga.empresa == "Incentiv RH"
    assert vaga.local == "Registro, SP"
    assert vaga.publicada == "2026-10-29"
    assert vaga.modalidade == "presencial"


def test_bne():
    vaga = bne.parse(ler("bne"))[0]
    assert vaga.empresa == "MB Advocacia"
    assert vaga.local == "Vilhena / RO"
    assert vaga.modalidade == "presencial"


def test_trabalha_brasil():
    vaga = trabalha_brasil.parse(ler("trabalha_brasil"))[0]
    assert vaga.titulo == "Advogado"
    assert vaga.empresa == "Adetra"
    assert vaga.salario == "R$ 2.600,00 por mês"


def test_vagas_com_datas_relativas():
    hoje = date(2026, 10, 30)
    assert vagas_com._data("Hoje", hoje) == "2026-10-30"
    assert vagas_com._data("Ontem", hoje) == "2026-10-29"
    assert vagas_com._data("Há 3 dias", hoje) == "2026-10-27"
    assert vagas_com._data("30/09/2026", hoje) == "2026-09-30"
