"""Sonda temporária 2: vagas jurídicas nas seguradoras."""
import json, re
import httpx
from bs4 import BeautifulSoup
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, follow_redirects=True, timeout=25)
JUR = re.compile(r"jur[ií]dic|advog|compliance|contencioso|contrat|regulat[oó]ri|societ[aá]ri|governan|legal|lawyer|counsel|paralegal|sinistro.*judic|ouvidoria|riscos", re.I)

print("### GUPY completas")
for g in ["porto","tokiomarine","grupomag","caixavidaeprevidencia","caixaresidencial","brasilseg","brasilprev","hdiseguros","capemisa","vemproitau","yelum","sulamericasaude","libertyseguros","zurichsantander","zurichbrasil","mapfrebrasil","sompoaxa","bradescosaude","odontoprev","porto-seguro","azul","itauseguros","itau-seguros","previsul","mongeral","omintseguros","omint","sabemi","kovr","mbm","austral-re","mitsui","starr","fator","sulamericaseguros"]:
    try:
        r = c.get(f"https://{g}.gupy.io/")
    except Exception as e:
        print("XX", g); continue
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if r.status_code != 200 or not m:
        continue
    pp = json.loads(m.group(1))["props"]["pageProps"]
    jobs = pp.get("jobs") or []
    jur = [j for j in jobs if JUR.search(j.get("title", "") + " " + (j.get("department") or ""))]
    print(f"== {g} ({(pp.get('careerPage') or {}).get('name')}): {len(jobs)} vagas, {len(jur)} jurídicas/afins")
    for j in jur:
        a = (j.get("workplace") or {}).get("address") or {}
        print("   ", j["id"], "|", j["title"].strip(), "|", j.get("department"), "|", a.get("city"), a.get("stateShortName"), "|", (j.get("workplace") or {}).get("workplaceType"), "|", j.get("publishedDate", "")[:10] if j.get("publishedDate") else "", "|", f"https://{g}.gupy.io/jobs/{j['id']}")
    if jobs and g == "porto": print("   keys", list(jobs[0]))

print("\n### INHIRE icatu")
for u, h in [("https://api.inhire.app/job-posts/public/pages", {"X-Tenant": "icatu"}),
             ("https://api.inhire.app/job-posts/public/pages?limit=200", {"X-Tenant": "icatu"}),
             ("https://icatu.inhire.app/vagas", {})]:
    try:
        r = c.get(u, headers=h); print(u, r.status_code, r.text[:600].replace("\n", " "))
    except Exception as e:
        print(u, "ERRO", e)

print("\n### WORKDAY")
WD = [("zurich","wd3","Zurich"),("zurich","wd3","zurich"),("chubb","wd1","chubbcareers"),("chubb","wd5","Chubb"),("pru","wd5","Careers"),("axa","wd3","AXA"),("allianz","wd3","Allianz"),("mapfre","wd3","MAPFRE"),("swissre","wd3","SwissRe"),("munichre","wd3","MunichRe"),("libertymutual","wd5","LMI"),("generali","wd3","Generali"),("aig","wd1","aig"),("travelers","wd5","External"),("mufg","wd3","MUFG-Careers"),("sompo","wd3","Sompo")]
for t, w, site in WD:
    u = f"https://{t}.{w}.myworkdayjobs.com/wday/cxs/{t}/{site}/jobs"
    try:
        r = c.post(u, json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "Brasil"})
        print(t, site, r.status_code, r.text[:300].replace("\n", " ") if r.status_code == 200 else "")
    except Exception as e:
        print(t, site, "ERRO", type(e).__name__)

print("\n### PAGINAS")
for u in ["https://www.sulamerica.com.br/carreiras", "https://carreiras.sulamerica.com.br/", "https://www.sulamericaseguros.com.br/trabalheconosco",
          "https://www.mapfre.com.br/sobre-a-mapfre/trabalhe-conosco/", "https://jobs.mapfre.com/", "https://www.zurich.com.br/pt-br/trabalhe-conosco",
          "https://www.zurich.com.br/carreiras", "https://www.yelumseguros.com.br/carreiras", "https://www.yelum.com.br/trabalhe-conosco",
          "https://www.prudential.com.br/trabalhe-conosco", "https://sompo.com.br/carreiras", "https://axa.com.br/trabalhe-conosco",
          "https://www.chubb.com/br-pt/sobre-a-chubb/trabalhe-conosco.html", "https://careers.chubb.com/", "https://www.allianz.com.br/sobre-a-allianz/trabalhe-conosco.html",
          "https://jobs.allianz.com/", "https://www.hdi.com.br/trabalhe-conosco", "https://www.bbseguros.com.br/carreiras", "https://www.irbre.com/carreiras/",
          "https://www.portoseguro.com.br/carreiras", "https://bradesco.csod.com/ux/ats/careersite/3/home?c=bradesco"]:
    try:
        r = c.get(u)
    except Exception as e:
        print("XX", u, type(e).__name__); continue
    links = sorted(set(re.findall(r"https?://[\w.-]*(?:gupy\.io|myworkdayjobs\.com|successfactors\.\w+|inhire\.\w+|csod\.com|pandape[\w.]*|abler\.com\.br|recrutei\.com\.br|lever\.co|greenhouse\.io|smartrecruiters\.com|eightfold\.ai|taleo\.net|oraclecloud\.com|kenoby\.com|solides\.com\.br|jobs\.[\w.-]+)[^\"'\s<>]*", r.text)))
    s = BeautifulSoup(r.text, "html.parser")
    print(r.status_code, u, "->", str(r.url)[:90], "|", (s.title.get_text(strip=True) if s.title else "")[:50])
    for l in links[:8]: print("     ", l[:140])
    if "csod" in u:
        print("   token?", re.findall(r'"token"\s*:\s*"([^"]{10,40})', r.text)[:1], re.findall(r'csod\.context\s*=\s*(\{.{0,300})', r.text)[:1])
