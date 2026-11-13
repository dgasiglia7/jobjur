import os, re
import httpx
c = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"})
URLS = {"michaelpage": "https://www.michaelpage.com.br/jobs/juridico", "michaelpage2": "https://www.michaelpage.com.br/jobs/juridico?page=1",
        "randstad": "https://www.randstad.com.br/vagas/s-juridico/", "randstad_q": "https://www.randstad.com.br/vagas/q-advogado/",
        "hays": "https://www.hays.com.br/vagas?q=advogado", "curriculum": "https://www.curriculum.com.br/vagas/de/advogado",
        "99jobs": "https://www.99jobs.com/opportunities/filtered_search?search%5Bterm%5D=advogado", "burh": "https://burh.com.br/busca?q=advogado",
        "afamar": "https://afamar.tweezer.jobs/candidato/vaga/buscar_vaga", "imediatta": "https://imediattarh.com.br/vagas/",
        "selpe": "https://vagas.recrutamentointeligente.net/gruposelpe", "abler": "https://candidatos.abler.com.br/vagas?search=advogado",
        "interage": "https://interagerh.vagas.solides.com.br/", "fox": "https://foxhumancapital.vagas.solides.com.br/", "remotar": "https://remotar.com.br/search/jobs?q=advogado",
        "adecco": "https://app.jobconvo.com/pt-br/careers/Adecco/7b3711ce-e38f-4c37-9b48-3a2ce0d9ba51/", "apinfo": "https://www.apinfo.com/apinfo/inc/list4.cfm",
        "manpower": "https://vagas.manpowergroup.com.br/", "novotempo": "https://novotemporh.com.br/", "agroforce": "https://agroforce.agrosearch.com.br/portal.html",
        "walljobs": "https://www.walljobs.com.br/vagas", "cliqueempregos": "https://app.cliqueempregos.com.br/pesquisa?q=advogado",
        "talentosenior": "https://talentosenior.com.br/", "maturi": "https://www.maturi.com.br/para-pessoas-maduras", "hirenow": "https://hirenow.company/", "evolk": "https://www.evolk.com.br"}
os.makedirs("paginas", exist_ok=True)
for nome, u in URLS.items():
    try:
        r = c.get(u)
        open(f"paginas/{nome}.html", "w").write(f"<!-- {r.status_code} {r.url} -->\n" + r.text)
        print(nome, r.status_code, len(r.text))
    except Exception as e:
        print(nome, "ERRO", e)
