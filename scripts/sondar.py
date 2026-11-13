import re, json
import httpx
c = httpx.Client(timeout=25, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"})
URLS = ["https://www.michaelpage.com.br/jobs/juridico", "https://www.randstad.com.br/vagas/s-juridico/", "https://www.hays.com.br/vagas?q=advogado",
        "https://www.curriculum.com.br/vagas/?q=advogado", "https://www.99jobs.com/opportunities/filtered_search?search%5Bterm%5D=advogado",
        "https://burh.com.br/busca?q=advogado", "https://www.walljobs.com.br/", "https://imediattarh.com.br/vagas/", "https://afamar.tweezer.jobs/candidato/vaga/buscar_vaga",
        "https://vagas.recrutamentointeligente.net/gruposelpe", "https://candidatos.abler.com.br/vagas?search=advogado", "https://foxhumancapital.com/vagasdeemprego/",
        "https://interagerh.vagas.solides.com.br/", "https://maturijobs.empregare.com/", "https://jobs.jobconvo.com/pt-br/careers/Adecco/7b3711ce-e38f-4c37-9b48-3a2ce0d9ba51/",
        "https://www.apinfo.com/apinfo/inc/list4.cfm", "https://www.vagas.com.br/vagas-de-jobcenter", "https://www.vagas.com.br/vagas-de-resch",
        "https://remotar.com.br/search/jobs?q=advogado", "https://app.cliqueempregos.com.br/pesquisa?q=advogado"]
for u in URLS:
    try:
        r = c.get(u)
    except Exception as e:
        print("=====", u, "ERRO", type(e).__name__); continue
    h = r.text
    print("=====", u, r.status_code, str(r.url)[:90], len(h), "NEXT" if "__NEXT_DATA__" in h else "", "NUXT" if "__NUXT__" in h else "")
    apis = sorted(set(re.findall(r'https?://[a-z0-9.-]*api[a-z0-9.-]*\.[a-z]+[a-z0-9/._-]*', h)))[:6]
    print("APIS", apis)
    achados = [m.start() for m in re.finditer(r"advogad|jur[ií]dic", h, re.I)][:40]
    vistos = 0; ultimo = -10**9
    for i in achados:
        if i - ultimo < 1500: continue
        ultimo = i; vistos += 1
        print("TRECHO", re.sub(r"\s+", " ", h[max(0, i - 700):i + 400]))
        if vistos >= 2: break
