"""Sonda temporária 2: estrutura das páginas candidatas."""
import json, re
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, follow_redirects=True, timeout=25)

def sec(t): print("\n" + "#" * 30, t)

sec("EMPREGARE")
r = c.get("https://www.empregare.com/pt-br/vagas?query=advogado&cidade=rio-de-janeiro")
print(r.status_code, r.url)
s = BeautifulSoup(r.text, "html.parser")
for i in ("v2-config", "busca-v2", "busca-v2-textos"):
    t = s.find(id=i); print(i, (t.string or t.get("src") or str(t.attrs))[:600] if t else None)
a = s.find("a", href=re.compile(r"/pt-br/vaga-"))
card = a
for _ in range(6):
    if card.parent: card = card.parent
    if len(str(card)) > 900: break
print("CARD", re.sub(r"\s+", " ", str(card))[:2500])
print("forms", [(f.get("action"), [i.get("name") for i in f.find_all(["input", "select"])]) for f in s.find_all("form")][:3])
print("apis", sorted(set(re.findall(r"""["'](/[\w/-]*(?:api|busca|vagas)[\w/-]*)["']""", r.text)))[:30])
r = c.get("https://www.empregare.com/pt-br/vaga-advogado-societario-senior_187071")
s = BeautifulSoup(r.text, "html.parser")
for js in s.select('script[type="application/ld+json"]'):
    print("DETALHE LD", (js.string or "")[:1500])

sec("TALENT")
r = c.get("https://br.talent.com/jobs?k=advogado&l=Rio+de+Janeiro")
s = BeautifulSoup(r.text, "html.parser")
h = r.text
i = h.find("639684882392418625")
print("ctx id", re.sub(r"\s+", " ", h[i-1500:i+800]) if i > 0 else "-")
t = s.find(id="_R_"); print("_R_", (t.string or "")[:300] if t else None)
for m in re.finditer(r'"jobTitle"|"title":"', h):
    print("json title ctx", h[m.start()-100:m.start()+400]); break
print("self.__next_f" in h, h.count("__next_f"))

sec("SOLIDES")
r = c.get("https://vagas.solides.com.br/vagas/todos/advogado")
srcs = re.findall(r'<script[^>]+src="([^"]+)"', r.text)
print("srcs", srcs[:30])
achados = set()
for src in srcs:
    u = src if src.startswith("http") else "https://vagas.solides.com.br" + src
    try:
        js = c.get(u).text
    except Exception as e:
        continue
    for m in re.finditer(r"apigw[^\"'`]{0,200}|/jobs/v\d[^\"'`]{0,200}|vacancy[^\"'`]{0,120}", js):
        achados.add(m.group(0)[:200])
for x in sorted(achados)[:60]: print("  ", x)
nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
print("NEXT", nd.group(1)[:1500] if nd else None)
print("nuxt", "__NUXT" in r.text, "window.__" in r.text, re.findall(r"window\.__\w+", r.text)[:5])
for path in ["https://apigw.solides.com.br/jobs/v3/home/vacancy?slug=todos&title=advogado&page=1&take=20",
             "https://apigw.solides.com.br/jobs/v3/portal-vacancies-new?title=advogado&locations=&take=20&page=1",
             "https://apigw.solides.com.br/jobs/v3/home/vacancy?slug=advogado&page=1&take=20"]:
    rr = c.get(path, headers={"Origin": "https://vagas.solides.com.br", "Referer": "https://vagas.solides.com.br/"})
    print(path, rr.status_code, rr.text[:800])
