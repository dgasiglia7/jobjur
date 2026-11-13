import re
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
c = httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"})
SITES = "www.99jobs.com www.abler.com.br www.across.com.br www.adecco.com.br www.afamar.com.br/vagas-abertas www.agnis.com.br www.agrosearch.com.br www.apinfo.com/apinfo/ www.azconsult.com.br www.bettha.com.br www.burh.com.br www.cliqueempregos.com.br www.contratando.com.br www.curriculum.com.br www.hirenow.company www.evolk.com.br www.foursales.com.br www.foxhumancapital.com www.ciadetalentos.com.br/pt/ www.hays.com.br www.iapsic.com.br www.imediattarh.com.br interagerh.com.br www.jobcenter.com.br www.manpowergroup.com.br www.maturi.com.br www.michaelpage.com.br www.novotemporh.com.br www.nube.com.br www.pagepersonnel.com.br www.qualitarh.com www.randstad.com.br www.remotar.com.br www.reschrh.com.br www.salesjobs.com.br www.gruposelpe.com.br www.talentosenior.com.br www.walljobs.com.br www.winnerrh.com.br www.glassdoor.com.br".split()
EXTRA = ["https://www.michaelpage.com.br/jobs/juridico", "https://www.pagepersonnel.com.br/jobs/juridico", "https://www.hays.com.br/vagas?q=advogado",
         "https://www.adecco.com.br/vagas/?k=advogado", "https://www.randstad.com.br/vagas/q-advogado/", "https://www.remotar.com.br/search/jobs?q=advogado",
         "https://www.curriculum.com.br/vagas/?q=advogado", "https://www.99jobs.com/opportunities/filtered_search?search%5Bterm%5D=advogado",
         "https://www.manpowergroup.com.br/vagas", "https://www.ciadetalentos.com.br/pt/vagas", "https://www.talentosenior.com.br/vagas",
         "https://www.nube.com.br/vagas", "https://www.burh.com.br/vagas", "https://www.abler.com.br/vagas", "https://www.cliqueempregos.com.br/vagas",
         "https://www.jobcenter.com.br/vagas", "https://www.maturi.com.br/vagas", "https://www.apinfo.com/apinfo/inc/list4.cfm"]
ATS = r"https?://[a-z0-9.-]*(?:gupy|inhire|solides|pandape|kenoby|recrutei|vagas\.com|99jobs|abler|quickin|bne\.com|infojobs|jobs\.|vagas\.|breezy|workable|selecty|empregare|jobconvo|taqe|hunterjobs)[a-z0-9./_?=-]*"
def olhar(url, fundo=True):
    try:
        r = c.get(url)
    except Exception as e:
        print("SITE", url, "ERRO", type(e).__name__); return
    h = r.text; low = h.lower()
    ats = sorted(set(re.findall(ATS, h)))[:5]
    links = []
    for a in BeautifulSoup(h, "html.parser").select("a[href]"):
        href = urljoin(str(r.url), a["href"]); t = a.get_text(" ", strip=True)[:40]
        if re.search(r"vaga|job|oportunidade|carreira|trabalhe", href + " " + t, re.I) and urlparse(href).netloc:
            links.append(href)
    links = list(dict.fromkeys(links))
    print("SITE", url, r.status_code, str(r.url)[:70], len(h), "jur" if re.search(r"advogad|jur[ií]dic", low) else "-",
          "cloudflare" if "cf-chl" in low or "just a moment" in low else "", "ATS", ats, "LINKS", len(links), links[:6])
    if fundo:
        for l in links[:3]:
            if urlparse(l).netloc.endswith(urlparse(str(r.url)).netloc.replace("www.", "")) and l != str(r.url):
                olhar(l, False)
for s in SITES:
    olhar("https://" + s)
for u in EXTRA:
    olhar(u, False)
