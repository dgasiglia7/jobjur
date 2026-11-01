import json
from datetime import datetime

from jobjur import painel


def vaga(titulo, url, nota, local="Rio de Janeiro, RJ", empresa="ACME"):
    return {"fonte": "Gupy", "titulo": titulo, "url": url, "empresa": empresa, "local": local,
            "publicada": "2026-10-30", "modalidade": "", "extras": {"nota": nota}}


def test_regiao():
    assert painel.regiao("Rio de Janeiro, RJ") == "rj"
    assert painel.regiao("Niterói - RJ") == "rj"
    assert painel.regiao("Brasil", "remoto") == "rj"
    assert painel.regiao("São Paulo, SP") == "sp"
    assert painel.regiao("Curitiba, PR") == "outra"


def test_atualizar_acrescenta_sem_apagar(tmp_path):
    arq = tmp_path / "vagas.json"
    quando = datetime(2026, 10, 31, 7, 0, tzinfo=painel.FUSO)
    assert painel.atualizar([vaga("Gerente Jurídico", "https://a", 80),
                             vaga("Advogado Júnior", "https://b", 40)], arq, 65, quando) == 1
    dados = json.loads(arq.read_text())
    chave = painel.id_vaga("Gerente Jurídico", "ACME")
    assert list(dados["vagas"]) == [chave]
    assert dados["vagas"][chave]["grupo"] == "top"
    assert dados["vagas"][chave]["adicionada_em"] == "2026-10-31T07:00-03:00"

    # anotação feita à mão continua lá depois de nova busca; vaga repetida não duplica
    dados["vagas"][chave]["atencao"] = "pede inglês"
    arq.write_text(json.dumps(dados))
    assert painel.atualizar([vaga("Gerente Jurídico", "https://a", 90),
                             vaga("Coordenador Jurídico", "https://c", 70, "São Paulo, SP")], arq, 65) == 1
    dados = json.loads(arq.read_text())
    assert dados["vagas"][chave]["atencao"] == "pede inglês"
    assert dados["vagas"][painel.id_vaga("Coordenador Jurídico", "ACME")]["grupo"] == "sp"


def test_verificar_marca_so_pendentes(tmp_path):
    arq, st = tmp_path / "vagas.json", tmp_path / "status.json"
    painel.atualizar([vaga("A", "https://a", 80), vaga("B", "https://b", 80), vaga("C", "https://c", 80)], arq, 65)
    st.write_text(json.dumps({painel.id_vaga("B", "ACME"): {"status": "enviado"}}))
    vistos = []

    def checar(cliente, url, hoje):
        vistos.append(url)
        return url != "https://c"

    assert painel.verificar(arq, st, cliente=object(), checar=checar) == 1
    dados = json.loads(arq.read_text())["vagas"]
    assert dados[painel.id_vaga("A", "ACME")]["encerrada"] is True
    assert "encerrada_em" in dados[painel.id_vaga("A", "ACME")]
    assert dados[painel.id_vaga("C", "ACME")]["encerrada"] is False
    assert vistos == ["https://a", "https://c"]  # B já foi marcada pela pessoa, não é verificada


def test_sinais_de_vaga_encerrada():
    from datetime import date
    from jobjur import encerradas
    proxima = '<script id="__NEXT_DATA__">{"props":{"pageProps":{"job":{"status":"%s","expiresAt":"%s"}}}}</script>'
    hoje = date(2026, 11, 1)
    assert encerradas.gupy(proxima % ("published", "2026-12-01"), hoje) is False
    assert encerradas.gupy(proxima % ("frozen", "2026-12-01"), hoje) is True
    assert encerradas.gupy(proxima % ("published", "2026-10-30"), hoje) is True
    assert encerradas.por_aviso("<h1>Advogado</h1><p>Essa vaga foi encerrada!</p>")
    # o aviso só vale no texto visível, não em traduções dentro de scripts
    assert not encerradas.por_aviso('<h1>Advogado</h1><script>{"t":"Candidaturas encerradas"}</script>')
