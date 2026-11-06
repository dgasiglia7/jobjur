"""Sonda temporária: testa portais candidatos a novas fontes (roda no GitHub Actions)."""
import json, re, sys
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
URLS = [
 "https://vagas.solides.com.br/vagas/todos/advogado",
 "https://apigw.solides.com.br/jobs/v3/home/vacancy?title=advogado&locations=&page=1&take=20",
 "https://br.jooble.org/SearchResult?ukw=advogado&rgns=Rio%20de%20Janeiro",
 "https://www.careerjet.com.br/vagas?s=advogado&l=Rio+de+Janeiro",
 "https://br.talent.com/jobs?k=advogado&l=Rio+de+Janeiro",
 "https://www.jobbol.com.br/vagas?q=advogado",
 "https://riovagas.com.br/?s=advogado",
 "https://riovagas.com.br/tag/advogado/",
 "https://www.trampos.co/oportunidades?tr=advogado",
 "https://portal.abler.com.br/vagas?search=advogado",
 "https://www.recrutei.com.br/vagas?search=advogado",
 "https://www.empregare.com/pt-br/vagas?query=advogado",
 "https://www.adzuna.com.br/search?q=advogado&loc=Rio+de+Janeiro",
 "https://www.bebee.com/br/jobs?term=advogado",
 "https://www.simplyhired.com.br/search?q=advogado&l=Rio+de+Janeiro",
 "https://www.glassdoor.com.br/Vaga/rio-de-janeiro-advogado-vagas-SRCH_IL.0,14_IC2370297_KO15,23.htm",
 "https://br.indeed.com/jobs?q=advogado&l=Rio+de+Janeiro",
 "https://www.sine.com.br/vagas-empregos-em-rio-de-janeiro-rj/advogado",
 "https://www.vagas.net/vagas?q=advogado",
 "https://www.netvagas.com.br/empregos/advogado",
 "https://www.empregosrj.com/?s=advogado",
 "https://www.cathojobs.com/",
 "https://programathor.com.br/jobs",
 "https://www.99jobs.com/opportunities?search=advogado",
 "https://jobs.quickin.io/",
 "https://www.kenoby.com/",
 "https://emprego.net/vagas?q=advogado",
 "https://www.jobatus.com.br/vagas-de-emprego?q=advogado&l=rio+de+janeiro",
 "https://www.empregoligado.com.br/",
 "https://br.trabajo.org/vagas-advogado-rio-de-janeiro",
 "https://br.jobrapido.com/?w=advogado&l=rio+de+janeiro",
 "https://www.whatjobs.com/br/jobs/advogado/rio-de-janeiro",
 "https://br.linkedin.com/jobs/advogado-vagas-rio-de-janeiro",
]
PAD = re.compile(r"vaga|job|oportunidade|emprego|position", re.I)
c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, follow_redirects=True, timeout=25)
for u in URLS:
    print("=" * 100); print(u)
    try:
        r = c.get(u)
    except Exception as e:
        print("ERRO", e); continue
    h = r.text
    print("status", r.status_code, "final", str(r.url)[:150], "bytes", len(h), "ctype", r.headers.get("content-type"))
    if "json" in (r.headers.get("content-type") or ""):
        print(h[:2500]); continue
    s = BeautifulSoup(h, "html.parser")
    print("title", (s.title.get_text(strip=True) if s.title else "")[:120])
    tipos = []
    for js in s.select('script[type="application/ld+json"]'):
        try:
            d = json.loads(js.string or "")
        except Exception:
            continue
        for x in (d if isinstance(d, list) else d.get("@graph", [d]) if isinstance(d, dict) else []):
            if isinstance(x, dict):
                tipos.append(x.get("@type"))
                if x.get("@type") in ("JobPosting", "ItemList"):
                    print("LDJSON", json.dumps(x, ensure_ascii=False)[:700])
    print("ld types", tipos[:10])
    print("scripts ids", [t.get("id") for t in s.find_all("script") if t.get("id")][:10], "NEXT" if "__NEXT_DATA__" in h else "", "NUXT" if "__NUXT__" in h else "")
    links = []
    for a in s.find_all("a", href=True):
        t = re.sub(r"\s+", " ", a.get_text(" ")).strip()
        if PAD.search(a["href"]) and len(t) > 8 and "advog" in t.lower() + a["href"].lower():
            links.append((t[:80], a["href"][:140]))
    print("links advog", len(links))
    for l in links[:8]:
        print("   ", l)
    if not links:
        txt = re.sub(r"\s+", " ", s.get_text(" "))
        i = txt.lower().find("advogad")
        print("texto:", txt[max(0, i - 200):i + 400] if i >= 0 else txt[:300])
