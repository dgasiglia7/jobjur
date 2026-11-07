"""Sonda temporária: onde as maiores seguradoras publicam vagas."""
import json, re
import httpx
from bs4 import BeautifulSoup
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, follow_redirects=True, timeout=20)
ATS = re.compile(r"https?://[\w.-]*(gupy\.io|myworkdayjobs\.com|successfactors\.\w+|kenoby\.com|inhire\.app|pandape[\w.]*|abler\.com\.br|recrutei\.com\.br|lever\.co|greenhouse\.io|smartrecruiters\.com|eightfold\.ai|csod\.com|taleo\.net|oraclecloud\.com|icims\.com|solides\.com\.br|vagas\.com\.br/[\w-]*|jobs\.[\w.-]+|carreiras?\.[\w.-]+|trabalheconosco[\w.-]*)[^\"'\s<>]*", re.I)
PAGINAS = [
 "https://www.bradescoseguros.com.br/clientes/institucional/trabalhe-conosco",
 "https://www.bradescoseguros.com.br/trabalhe-conosco",
 "https://www.portoseguro.com.br/trabalhe-conosco", "https://www.porto.vc/trabalhe-conosco", "https://carreiras.porto.com.br/",
 "https://www.caixaseguradora.com.br/trabalhe-conosco", "https://www.caixavidaeprevidencia.com.br/trabalhe-conosco",
 "https://www.bbseguros.com.br/trabalhe-conosco", "https://www.brasilseg.com.br/trabalhe-conosco", "https://www.brasilprev.com.br/trabalhe-conosco",
 "https://www.itau.com.br/carreiras", "https://carreiras.itau.com.br/",
 "https://portal.sulamericaseguros.com.br/trabalhe-conosco", "https://www.sulamerica.com.br/trabalhe-conosco",
 "https://www.zurich.com.br/pt-br/sobre-nos/trabalhe-conosco", "https://www.zurich.com/careers",
 "https://www.mapfre.com.br/trabalhe-conosco/", "https://www.tokiomarine.com.br/trabalhe-conosco/",
 "https://www.allianz.com.br/trabalhe-conosco.html", "https://careers.allianz.com/",
 "https://www.hdiseguros.com.br/trabalhe-conosco", "https://www.yelumseguros.com.br/trabalhe-conosco", "https://www.libertyseguros.com.br/trabalhe-conosco",
 "https://www.icatuseguros.com.br/trabalhe-conosco", "https://www.mag.com.br/trabalhe-conosco", "https://www.prudentialdobrasil.com.br/trabalhe-conosco",
 "https://www.sompo.com.br/trabalhe-conosco", "https://www.axa.com.br/trabalhe-conosco", "https://www.chubb.com/br-pt/careers.html", "https://www.irbre.com/trabalhe-conosco/",
]
for u in PAGINAS:
    try:
        r = c.get(u)
    except Exception as e:
        print("XX", u, type(e).__name__); continue
    achados = sorted(set(m.group(0)[:120] for m in ATS.finditer(r.text)))
    s = BeautifulSoup(r.text, "html.parser")
    print(r.status_code, u, "->", str(r.url)[:80], "|", (s.title.get_text(strip=True) if s.title else "")[:60])
    for a in achados[:12]: print("     ", a)
GUPY = ["portoseguro","porto","portoseguroconsorcio","tokiomarine","tokiomarineseguradora","icatu","icatuseguros","grupomag","mag","sulamerica","sulamericaseguros","caixaseguradora","caixavidaeprevidencia","caixaresidencial","brasilseg","bbseguros","brasilprev","bradescoseguros","bradesco","mapfre","mapfreseguros","allianz","allianzseguros","zurich","zurichseguros","hdi","hdiseguros","yelum","yelumseguros","liberty","prudential","prudentialdobrasil","itau","itauunibanco","sompo","sompoaxa","axa","chubb","irbre","irb","justos","akad","youse","pottencial","excelsior","essor","ezze","alfaseguradora","capemisa","unimedseguros","sicoobseguros","sinaf","berkley","swissre","munichre","fairfax","argo","austral","junto","newe","bmg","generali"]
print("\n### GUPY")
for g in GUPY:
    try:
        r = c.get(f"https://{g}.gupy.io/")
    except Exception as e:
        print("XX", g, type(e).__name__); continue
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if r.status_code != 200 or not m:
        print(r.status_code, g, "sem next"); continue
    pp = json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    jobs = pp.get("jobs") or (pp.get("careerPage") or {}).get("jobs") or []
    nome = (pp.get("careerPage") or {}).get("name") or pp.get("name") or ""
    print("OK", g, "|", nome, "| keys", list(pp)[:12], "| jobs", len(jobs) if isinstance(jobs, list) else type(jobs))
    if isinstance(jobs, list):
        for j in jobs[:3]: print("      ", json.dumps(j, ensure_ascii=False)[:300])
