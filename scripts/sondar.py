"""Sonda temporária 4: roda os coletores novos de verdade."""
import json, re, sys
sys.path.insert(0, ".")
from jobjur.fontes import Cliente, Local, empregare, talent, riovagas, empregos_rj
c = Cliente(pausa=1)
rio = Local("Rio de Janeiro", "RJ")
for mod, local in [(empregare, None), (talent, rio), (talent, None), (riovagas, rio), (empregos_rj, rio)]:
    for termo in ["advogado", "jurídico", "compliance"]:
        try:
            vs = mod.buscar(c, termo, local)
        except Exception as e:
            print(mod.NOME, termo, "ERRO", repr(e)); continue
        print(f"== {mod.NOME} {termo} {local and local.cidade}: {len(vs)}")
        for v in vs[:6]:
            print("   ", v.titulo[:70], "|", v.empresa[:30], "|", v.local, "|", v.publicada, "|", v.url[:90])
# fixtures
h = c.get("https://br.talent.com/jobs", k="advogado", l="Rio de Janeiro, RJ")
from bs4 import BeautifulSoup
s = BeautifulSoup(h, "html.parser")
links = s.find_all("a", href=re.compile(r"view\?id=\d+"), attrs={"aria-label": True})
for a in links[:2]:
    print("FIXTURE_TALENT", str(talent._cartao(a)))
r = c.resposta("https://riovagas.com.br/wp-json/wp/v2/posts", search="advogado", per_page=2, _fields="title,link,date,excerpt")
print("FIXTURE_WP", r.status_code, r.text[:3000])
