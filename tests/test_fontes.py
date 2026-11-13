from datetime import date
from pathlib import Path

import pytest

import json

from jobjur.fontes import (FONTES, bne, catho, empregare, empregos_com, gupy, infojobs, linkedin, talent, trabalha_brasil,
                           vagas_com, wordpress)

FIXTURES = Path(__file__).parent / "fixtures"


def ler(nome: str) -> str:
    return (FIXTURES / f"{nome}.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("modulo", [gupy, linkedin, vagas_com, catho, infojobs, empregos_com, bne, trabalha_brasil,
                                    empregare, talent])
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
                           "Trabalha Brasil", "Empregare", "Talent.com", "RIOVAGAS", "Seguradoras", "Empresas", "Tecnologia", "Telecom",
                           "Financeiro", "Construção", "Transporte", "Portais (planilha)"}


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


def test_empregare():
    vaga = empregare.parse(ler("empregare"))[1]
    assert vaga.empresa == "Rêve"
    assert vaga.local == "Águas Claras, Brasília, DF"
    assert vaga.url == "https://www.empregare.com/pt-br/vaga-advogado-a-corporativo_185359"


def test_talent():
    vaga = talent.parse(ler("talent"))[0]
    assert vaga.titulo == "Advogado(a) Associado(a) - RJ"
    assert vaga.empresa == "Defesa Justa Estratégica ltda"
    assert vaga.local == "Rio de Janeiro, Rio de Janeiro"
    assert vaga.url == "https://br.talent.com/view?id=639684882392418625"
    assert not vaga.descricao.endswith("Mostre mais")


def test_wordpress_ignora_posts_antigos():
    posts = json.loads((FIXTURES / "riovagas.json").read_text(encoding="utf-8"))
    vagas = wordpress.parse(posts, "RIOVAGAS", hoje=date(2026, 11, 6))
    assert [v.publicada for v in vagas] == ["2026-11-05", "2026-10-29"]
    assert vagas[0].titulo.startswith("Advogado Previdenciario – Escritório")
    assert vagas[0].local == "Rio de Janeiro, RJ"


def test_fontes_que_ignoram_a_cidade_nao_repetem_a_busca():
    from jobjur.fontes import Local, riovagas
    rio, sp = Local("Rio de Janeiro", "RJ"), Local("São Paulo", "SP")
    assert empregare.buscar(None, "advogado", rio) == []
    assert riovagas.buscar(None, "advogado", sp) == []
    assert riovagas.buscar(None, "advogado", None) == []


def test_seguradoras_gupy_filtra_juridico():
    from jobjur.fontes import seguradoras
    dados = {"props": {"pageProps": {"jobs": [
        {"id": 1, "title": "Advogado(a) Operacional Pleno (Contencioso)", "department": "Jurídico",
         "workplace": {"address": {"city": "São Paulo", "stateShortName": "SP"}}, "workplaceType": "hybrid"},
        {"id": 2, "title": "Analista de Governança Sênior", "department": "Jurídico", "workplace": {}},
        {"id": 3, "title": "Analista Contábil", "department": "Finanças", "workplace": {}},
    ]}}}
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(dados)}</script>'
    vagas = seguradoras.parse_gupy(html, "tokiomarine")
    assert [v.url for v in vagas] == ["https://tokiomarine.gupy.io/jobs/1", "https://tokiomarine.gupy.io/jobs/2"]
    assert vagas[0].empresa == "Tokio Marine" and vagas[0].local == "São Paulo, SP"
    assert vagas[0].modalidade == "híbrido"


def test_seguradoras_zurich_workday_inhire():
    from jobjur.fontes import seguradoras
    html = ('<table><tr class="data-row"><td><a class="jobTitle-link" href="/job/Sao-Paulo-ADVOG/1/">ADVOG '
            'CORPORATIVO II</a></td><td><span class="jobLocation">São Paulo, BR</span></td></tr>'
            '<tr class="data-row"><td><a class="jobTitle-link" href="/job/x/2/">Atuário</a></td></tr></table>')
    [z] = seguradoras.parse_zurich(html)
    assert z.url == "https://www.careers.zurich.com/job/Sao-Paulo-ADVOG/1/" and z.local == "São Paulo, BR"
    wd = {"jobPostings": [{"title": "ANALISTA PRIVACY SR", "externalPath": "/job/Rio-de-Janeiro-Brazil/X_R-1",
                           "locationsText": "Rio de Janeiro, Brazil"},
                          {"title": "Legal Counsel", "externalPath": "/job/Newark-NJ/Y_R-2", "locationsText": "Newark"}]}
    [p] = seguradoras.parse_workday(wd, seguradoras.PRUDENTIAL, "Careers", "Prudential do Brasil")
    assert p.url.endswith("/Careers/job/Rio-de-Janeiro-Brazil/X_R-1")
    ih = {"jobsPage": [{"displayName": "Advogado Sênior", "jobId": "abc", "location": "Rio de Janeiro, RJ, BR",
                        "workplaceType": "On-site"}, {"displayName": "Recepcionista", "jobId": "d"}]}
    [i] = seguradoras.parse_inhire(ih, "icatu", "Icatu Seguros")
    assert i.url == "https://icatu.inhire.app/vagas/abc" and i.local == "Rio de Janeiro, RJ"
    assert i.modalidade == "presencial"


def test_seguradoras_le_paginas_uma_vez(monkeypatch):
    from jobjur.fontes import seguradoras
    chamadas = []
    monkeypatch.setattr(seguradoras, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = seguradoras.Cliente(pausa=0)
    seguradoras.buscar(cliente, "advogado")
    seguradoras.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_empresas_greenhouse_filtra_juridico():
    from jobjur.fontes import empresas
    dados = {"jobs": [
        {"title": "Grupo QuintoAndar | Analista Compliance Sênior", "location": {"name": "São Paulo, São Paulo, Brazil"},
         "absolute_url": "https://job-boards.greenhouse.io/quintoandar/jobs/1", "first_published": "2026-10-27T18:57:05-04:00"},
        {"title": "Engenheiro de Dados", "location": {"name": "Remoto"}, "absolute_url": "https://x/2"},
    ]}
    [v] = empresas.parse_greenhouse(dados, "QuintoAndar")
    assert v.titulo == "Analista Compliance Sênior" and v.empresa == "QuintoAndar"
    assert v.local == "São Paulo, São Paulo" and v.publicada == "2026-10-27" and v.fonte == "Empresas"


def test_empresas_gupy_usa_nome_da_fonte():
    from jobjur.fontes import empresas, seguradoras
    dados = {"props": {"pageProps": {"jobs": [{"id": 7, "title": "Advogado Sênior", "workplace": {}}]}}}
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(dados)}</script>'
    [v] = seguradoras.parse_gupy(html, "asaas", empresas.GUPY, empresas.NOME)
    assert v.fonte == "Empresas" and v.empresa == "Asaas" and v.url == "https://asaas.gupy.io/jobs/7"


def test_empresas_le_paginas_uma_vez(monkeypatch):
    from jobjur.fontes import empresas
    chamadas = []
    monkeypatch.setattr(empresas, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = empresas.Cliente(pausa=0)
    empresas.buscar(cliente, "advogado")
    empresas.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_empresas_cloudwalk_filtra_pelo_titulo():
    from jobjur.fontes import empresas
    card = ('<li><a class="jobs-webflow_card__Y" href="/jobs/{slug}"><div><p class="jobs-webflow_cardTitle__Y">{t}</p>'
            '<div><p class="jobs-webflow_cardMeta__S">{m}</p><span>Risk and Compliance</span></div></div>'
            '<span>Apply</span></a></li>')
    html = (card.format(slug="legal-counsel-abc", t="Legal Counsel", m="São Paulo, BRA · Full Time")
            + card.format(slug="insider-risk-x", t="Insider Risk Security Engineer", m="Full Time"))
    [v] = empresas.parse_cloudwalk(html)
    assert v.url == "https://lp.cloudwalk.io/jobs/legal-counsel-abc" and v.local == "São Paulo, BRA"
    assert v.empresa == "CloudWalk"


def test_tecnologia_parsers():
    from jobjur.fontes import tecnologia as t
    [a] = t.parse_amazon({"jobs": [
        {"title": "Sr Corporate Counsel - Retail", "job_path": "/en/jobs/1/sr", "normalized_location": "Sao Paulo, Sao Paulo, BRA"},
        {"title": "Software Engineer", "job_path": "/en/jobs/2/se"}]})
    assert a.url == "https://www.amazon.jobs/en/jobs/1/sr" and a.local == "Sao Paulo, Sao Paulo" and a.fonte == "Tecnologia"
    [m] = t.parse_microsoft({"data": {"positions": [
        {"name": "Corporate Counsel", "positionUrl": "/careers/job/9", "locations": ["São Paulo, Brazil"], "postedTs": 1793991679,
         "workLocationOption": "hybrid", "department": "Legal"},
        {"name": "Area Support Lead", "positionUrl": "/careers/job/8", "department": "Support"}]}})
    assert m.url == "https://apply.careers.microsoft.com/careers/job/9" and m.modalidade == "híbrido" and m.publicada
    html = '[["111024354363351750","Legal Counsel, Brazil","https://www.google.com/about/careers/applications/signin?jobId=x"],["222024354363351750","Software Engineer","https://www.google.com/about/careers/applications/signin?jobId=y"]'
    [g] = t.parse_google(html)
    assert g.url.endswith("/results/111024354363351750") and g.titulo == "Legal Counsel, Brazil"
    [o] = t.parse_oracle({"items": [{"requisitionList": [
        {"Title": "Estagiário Jurídico", "Id": "11941", "PrimaryLocation": "SAO PAULO, SP, Brasil", "PostedDate": "2026-09-30"},
        {"Title": "Legal Counsel", "Id": "1", "PrimaryLocation": "Austin, TX, United States"}]}]}, "PicPay", "https://x/job/{id}")
    assert o.url == "https://x/job/11941" and o.local == "SAO PAULO, SP"
    [n] = t.parse_ashby({"jobs": [
        {"title": "Compliance Specialist", "location": "São Paulo", "jobUrl": "https://jobs.ashbyhq.com/nubank/a",
         "workplaceType": "Hybrid", "address": {"postalAddress": {"addressCountry": "Brazil"}}},
        {"title": "Compliance Expert", "location": "Ciudad de México", "jobUrl": "https://jobs.ashbyhq.com/nubank/b",
         "address": {"postalAddress": {"addressCountry": "Mexico"}}}]}, "Nubank")
    assert n.url.endswith("/a") and n.modalidade == "híbrido"
    [i] = t.parse_ibm({"hits": {"hits": [{"_source": {"title": "Advogado Sênior", "url": "https://careers.ibm.com/x",
                                                      "field_keyword_19": "SÃO PAULO, BR"}}]}})
    assert i.empresa == "IBM" and i.local == "São Paulo"


def test_telecom_le_paginas_uma_vez(monkeypatch):
    from jobjur.fontes import telecom
    chamadas = []
    monkeypatch.setattr(telecom, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = telecom.Cliente(pausa=0)
    telecom.buscar(cliente, "advogado")
    telecom.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_financeiro_lever_filtra_juridico():
    from jobjur.fontes import financeiro
    dados = [
        {"text": "Advogado(a) Contencioso", "hostedUrl": "https://jobs.lever.co/bv/1", "createdAt": 1762819200000,
         "categories": {"location": "São Paulo, SP", "team": "Jurídico"}, "workplaceType": "hybrid"},
        {"text": "Engenheiro de Dados", "hostedUrl": "https://jobs.lever.co/bv/2", "categories": {"team": "Dados"}},
    ]
    vagas = financeiro.parse_lever(dados, "Banco BV")
    assert [v.titulo for v in vagas] == ["Advogado(a) Contencioso"]
    assert vagas[0].empresa == "Banco BV" and vagas[0].publicada == "2025-11-11" and vagas[0].local == "São Paulo, SP"


def test_financeiro_le_paginas_uma_vez(monkeypatch):
    from jobjur.fontes import financeiro
    chamadas = []
    monkeypatch.setattr(financeiro, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = financeiro.Cliente(pausa=0)
    financeiro.buscar(cliente, "advogado")
    financeiro.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_cargo_comercial_pessoa_juridica_nao_e_juridico():
    from jobjur.fontes.seguradoras import eh_juridica
    assert not eh_juridica("Gerente de Negócios Pessoa Física, Jurídica e Agro")
    assert not eh_juridica("Gerente de Relacionamento Pessoa Jurídica")
    assert eh_juridica("Analista Jurídico")


def test_construcao_pandape_filtra_juridico():
    from jobjur.fontes import construcao
    html = """
    <a class="card card-vacancy" href="/Detail/1"><h3 title="Advogado(a) Imobili&#xE1;rio">x</h3>
      <div class="vacancy-detail"><div class="align-middle mr-20">S&#xE3;o Paulo - SP</div></div></a>
    <a class="card card-vacancy" href="/Detail/2"><h3 title="Corretor de Im&#xF3;veis">x</h3></a>"""
    vagas = construcao.parse_pandape(html, "trisul", "Trisul")
    assert [(v.titulo, v.local, v.url) for v in vagas] == [
        ("Advogado(a) Imobiliário", "São Paulo - SP", "https://trisul.pandape.infojobs.com.br/Detail/1")]


def test_construcao_le_paginas_uma_vez(monkeypatch):
    from jobjur.fontes import construcao
    chamadas = []
    monkeypatch.setattr(construcao, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = construcao.Cliente(pausa=0)
    construcao.buscar(cliente, "advogado")
    construcao.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_construcao_pandape_para_quando_a_pagina_repete():
    from jobjur.fontes import construcao
    html = '<a class="card card-vacancy" href="/Detail/1"><h3 title="Advogado(a)">x</h3></a>'
    chamadas = []

    class Falso:
        def get(self, url, **params):
            chamadas.append(params)
            return html
    vagas = construcao.ler_pandape(Falso(), "braspress", "Braspress")
    assert len(vagas) == 1 and chamadas == [{"PageNumber": 1}]


def test_transporte_le_paginas_uma_vez(monkeypatch):
    from jobjur.fontes import transporte
    chamadas = []
    monkeypatch.setattr(transporte, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = transporte.Cliente(pausa=0)
    transporte.buscar(cliente, "advogado")
    transporte.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_portais_le_sites_uma_vez(monkeypatch):
    from jobjur.fontes import portais
    chamadas = []
    monkeypatch.setattr(portais, "coletar", lambda cliente: chamadas.append(1) or [])
    cliente = portais.Cliente(pausa=0)
    portais.buscar(cliente, "advogado")
    portais.buscar(cliente, "compliance")
    assert chamadas == [1]


def test_portais_parsers():
    from jobjur.fontes import portais
    mp = ('<div class="job-tile"><div class="job-title"><h3><a href="/job-detail/advogado/ref/1">Advogado(a) Pleno</a></h3></div>'
          '<div class="job-location"> Rio de Janeiro</div></div>'
          '<div class="job-tile"><div class="job-title"><h3><a href="/job-detail/x/ref/2">Gerente de Vendas</a></h3></div></div>')
    [v] = portais.parse_michael_page(mp)
    assert (v.titulo, v.local, v.url) == ("Advogado(a) Pleno", "Rio de Janeiro", "https://www.michaelpage.com.br/job-detail/advogado/ref/1")
    rs = ('<script>window.__ROUTE_DATA__ = {"searchResults":{"hits":{"hits":[{"_id":"9","_source":{"JobInformation":'
          '{"Title":"Supervisor Jurídico"},"JobLocation":{"City":"Rio de Janeiro","Region":"Rio de Janeiro"},'
          '"BlueXSanitized":{"Title":"supervisor-juridico","City":"rio-de-janeiro"}}}]}}};</script>')
    [v] = portais.parse_randstad(rs)
    assert v.url == "https://www.randstad.com.br/vagas/supervisor-juridico_rio-de-janeiro_9/"
    cu = ('<a class="card" href="/vagas/vaga/1/de-Advogado/em-RJ"><span class="card-titulo">Advogado Jr</span>'
          '<span class="card-meta">Escritório X · Rio de Janeiro/RJ · remoto</span></a>')
    [v] = portais.parse_curriculum(cu)
    assert (v.empresa, v.local, v.modalidade) == ("Escritório X", "Rio de Janeiro/RJ", "remoto")
    nj = ('<a class="opportunity-card" href="https://99jobs.com/x/jobs/5-advogado-trabalhista-pleno?utm=1"><h1>📢 ADVOGADO TRAB...</h1>'
          '<span class="opportunity-label-acting-mode">Remoto</span><div class="opportunity-address"><p> Não informado </p></div>'
          '<div class="opportunity-company-infos"><h2> Empresa Y </h2></div></a>')
    [v] = portais.parse_99jobs(nj)
    assert (v.titulo, v.local, v.modalidade, v.url) == ("Advogado trabalhista pleno", "", "Remoto", "https://99jobs.com/x/jobs/5-advogado-trabalhista-pleno")
    se = ('<div data-x="{&quot;listaVagas&quot;:{&quot;vagas&quot;:[{&quot;titulo&quot;:&quot;Advogado J\\u00fanior&quot;,'
          '&quot;nomeCidade&quot;:&quot;Niter\\u00f3i&quot;,&quot;siglaEstado&quot;:&quot;RJ&quot;,&quot;regime&quot;:&quot;Remoto&quot;,'
          '&quot;url&quot;:&quot;https://vagas.recrutamentointeligente.net/gruposelpe/detalhe/a/R1&quot;}]}}"></div>')
    [v] = portais.parse_selpe(se)
    assert (v.titulo, v.local) == ("Advogado Júnior", "Niterói/RJ")


def test_portais_mostram_o_nome_do_site(monkeypatch):
    from jobjur.fontes import portais
    html = ('<a class="card" href="/vagas/vaga/1/de-Advogado"><span class="card-titulo">Advogado Jr</span>'
            '<span class="card-meta">X · Rio de Janeiro/RJ</span></a>')

    class Falso:
        def get(self, url, **params):
            if "curriculum" in url:
                return html
            raise RuntimeError("fora do ar")

    [v] = portais.coletar(Falso())
    assert v.fonte == "Curriculum"
