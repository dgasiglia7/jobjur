"""Sonda temporária 3."""
import json, re
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, follow_redirects=True, timeout=25)
def sec(t): print("\n" + "#" * 30, t)

sec("EMPREGARE paginas/local")
for q in ["query=advogado&localidade=rio-de-janeiro-rj", "query=advogado&regiao=rio-de-janeiro-rj", "query=advogado&pagina=2", "query=advogado&page=2", "query=juridico", "query=compliance"]:
    r = c.get("https://www.empregare.com/pt-br/vagas?" + q)
    s = BeautifulSoup(r.text, "html.parser")
    ul = s.find(id="resList")
    print(q, r.status_code, r.url, ul.attrs if ul else None, [ (x.select_one('.card__t').get_text(strip=True), x.select_one('.card__l').get_text(strip=True)) for x in s.select('li.card')][:4])
r = c.get("https://www.empregare.com/pt-br/vagas?query=advogado")
cfg = json.loads(BeautifulSoup(r.text, "html.parser").find(id="busca-v2").string)
for g in cfg.get("grupos", []):
    print("grupo", g.get("k"), [o[0] for o in (g.get("ops") or [])][:8])
print([k for k in cfg])
print(re.findall(r'(?:fetch|url)\s*\(?\s*[`"\'][^`"\']{0,120}', r.text)[:10])

sec("TALENT")
r = c.get("https://br.talent.com/jobs?k=advogado&l=Rio+de+Janeiro")
s = BeautifulSoup(r.text, "html.parser")
as_ = s.find_all("a", href=re.compile(r"view\?id="))
print("anchors", len(as_))
for a in as_[:2]:
    card = a
    for _ in range(8):
        if card.parent is not None and len(card.get_text()) < 120: card = card.parent
    print("CARD", re.sub(r"\s+", " ", str(card))[:2000])
    print("TEXT", re.sub(r"\s+", " ", card.get_text(" | "))[:400])
h = r.text
for m in list(re.finditer(r'\\"title\\":', h))[:2]:
    print("RSC", h[m.start()-300:m.start()+900])
r2 = c.get("https://br.talent.com/view?id=639684882392418625")
print("view", r2.status_code, r2.url)
for js in BeautifulSoup(r2.text, "html.parser").select('script[type="application/ld+json"]'):
    print("VIEW LD", (js.string or "")[:1200])

sec("SOLIDES")
js = c.get("https://vagas.solides.com.br/_next/static/chunks/app/(portal)/vagas/%5B...filter%5D/page-f1f773a595fdaebb.js").text
print(len(js))
for m in re.finditer(r"apigw|/v\d/|vacanc|fetch\(|baseURL|process\.env", js):
    print("  ", js[max(0, m.start()-150):m.start()+250].replace("\n", " ")); 
for ch in ["/_next/static/chunks/940-456f019be83c3148.js", "/_next/static/chunks/331-99995d5b9ffc5147.js", "/_next/static/chunks/908-a67d22b2c6af07ba.js", "/_next/static/chunks/874-96a8b29c4810fc1f.js", "/_next/static/chunks/63-9a83a80bbe5b0f17.js", "/_next/static/chunks/app/layout-5e3d65711b46c5bf.js", "/_next/static/chunks/581-318d95a7aba219c3.js", "/_next/static/chunks/863-ee8acd8821841c6a.js"]:
    t = c.get("https://vagas.solides.com.br" + ch).text
    for m in re.finditer(r"apigw[^\"'`]{0,150}|https://[\w.-]*solides[\w.-]*[^\"'`]{0,100}|vacancy[^\"'`]{0,80}", t):
        print(ch[-25:], m.group(0)[:200])
r = c.get("https://vagas.solides.com.br/vagas/todos/advogado")
i = r.text.find("dvogad", r.text.find("Buscar vagas"))
print("SSR ctx", re.sub(r"\s+", " ", r.text[i-1500:i+1500]) if i > 0 else "-")
print("next_f", r.text.count("__next_f"))
for m in list(re.finditer(r'\\"title\\":\\"[^\\]*[Aa]dvog', r.text))[:2]:
    print("RSC", r.text[m.start()-600:m.start()+900])
