"""Sonda temporária 3: seguradoras restantes."""
import json, re
import httpx
from bs4 import BeautifulSoup
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, follow_redirects=True, timeout=25)
JUR = re.compile(r"jur[ií]dic|advog|compliance|contencioso|contrat|regulat[oó]ri|societ[aá]ri|legal|lawyer|counsel|paralegal", re.I)
def sec(t): print("\n###", t)

sec("ICATU inhire")
r = c.get("https://api.inhire.app/job-posts/public/pages", headers={"X-Tenant": "icatu"})
d = r.json(); print(list(d))
for k, v in d.items():
    if isinstance(v, list): print(k, len(v), json.dumps(v[:1], ensure_ascii=False)[:400])
for u in ["https://api.inhire.app/job-posts/public/pages/job-posts", "https://api.inhire.app/job-posts/public", "https://api.inhire.app/job-posts/public/pages/jobs"]:
    rr = c.get(u, headers={"X-Tenant": "icatu"}); print(u, rr.status_code, rr.text[:300])
h = c.get("https://icatu.inhire.app/vagas").text
print("api refs", sorted(set(re.findall(r'api\.inhire\.app/[\w/.-]+', h)))[:20])
for src in re.findall(r'<script[^>]+src="([^"]+)"', h)[:15]:
    js = c.get(src if src.startswith("http") else "https://icatu.inhire.app" + src).text
    for m in set(re.findall(r'["`](/job-posts[\w/${}.-]*)', js)): print("  js", m)

sec("WORKDAY prudential / aig")
for t, w, site in [("pru", "wd5", "Careers"), ("aig", "wd1", "aig")]:
    r = c.post(f"https://{t}.{w}.myworkdayjobs.com/wday/cxs/{t}/{site}/jobs", json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "Brasil"})
    for j in r.json().get("jobPostings", []):
        print("  ", t, "|", j["title"], "|", j.get("locationsText"), "|", j.get("postedOn"), "|", f"https://{t}.{w}.myworkdayjobs.com/{site}{j['externalPath']}")
    r = c.post(f"https://{t}.{w}.myworkdayjobs.com/wday/cxs/{t}/{site}/jobs", json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "jurídico"})
    for j in r.json().get("jobPostings", []):
        print("  jur", t, "|", j["title"], "|", j.get("locationsText"), "|", j.get("postedOn"))

sec("BRADESCO csod")
h = c.get("https://bradesco.csod.com/ux/ats/careersite/3/home?c=bradesco").text
tok = re.search(r'"token"\s*:\s*"([^"]+)"', h)
ctx = re.search(r'csod\.context\s*=\s*(\{.*?\});', h, re.S)
cloud = re.search(r'"cloud"\s*:\s*"([^"]+)"', h)
print("cloud", cloud and cloud.group(1))
if tok:
    base = (cloud.group(1) if cloud else "https://us.api.csod.com/").rstrip("/")
    for kw in ["jurídico", "advogado", "compliance"]:
        body = {"careerSiteId": 3, "careerSitePageId": 3, "pageNumber": 1, "pageSize": 50, "cultureId": 12, "searchText": kw, "cultureName": "pt-BR", "states": [], "countryCodes": [], "cities": [], "placeID": "", "radius": None, "postingsWithinDays": None, "customFieldCheckboxKeys": [], "customFieldDropdowns": [], "customFieldRadios": []}
        rr = c.post(base + "/rec-job-search/external/jobs", json=body, headers={"Authorization": "Bearer " + tok.group(1), "Content-Type": "application/json"})
        print(kw, rr.status_code, rr.text[:200] if rr.status_code != 200 else "")
        if rr.status_code == 200:
            for j in rr.json().get("data", {}).get("requisitions", []):
                print("   ", j.get("requisitionId"), "|", j.get("displayJobTitle"), "|", [l.get("city") for l in j.get("locations", [])], "|", j.get("postingEffectiveDate", "")[:10], "| https://bradesco.csod.com/ux/ats/careersite/3/home/requisition/%s?c=bradesco" % j.get("requisitionId"))

sec("CHUBB oracle")
u = "https://fa-ewgu-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber=CX_2,limit=50,keyword=%22Brazil%22"
r = c.get(u); print(r.status_code)
try:
    for it in r.json()["items"][0]["requisitionList"]:
        print("   ", it["Title"], "|", it.get("PrimaryLocation"), "|", it.get("PostedDate"), "| https://careers.chubb.com/job/%s" % it["Id"])
except Exception as e:
    print(r.text[:300])

sec("MAPFRE / ZURICH / IRB successfactors")
for u in ["https://jobs.mapfre.com/search/?q=jur%C3%ADdico&locationsearch=Brasil&locale=pt_BR", "https://jobs.mapfre.com/search/?q=&locationsearch=Brasil&locale=pt_BR",
          "https://www.careers.zurich.com/search/?q=&locationsearch=Brazil", "https://careers.zurich.com/search/?q=&locationsearch=Brasil",
          "https://career2.successfactors.eu/career?company=IRBBrasilREP"]:
    try:
        r = c.get(u)
    except Exception as e:
        print("XX", u, type(e).__name__); continue
    s = BeautifulSoup(r.text, "html.parser")
    rows = s.select("tr.data-row") or s.select("li.job-tile")
    print(r.status_code, u, str(r.url)[:80], "rows", len(rows))
    for row in rows[:40]:
        a = row.select_one("a.jobTitle-link") or row.find("a")
        loc = row.select_one(".jobLocation")
        t = a.get_text(strip=True) if a else ""
        print("    ", "*" if JUR.search(t) else " ", t, "|", loc.get_text(" ", strip=True)[:40] if loc else "", "|", ("https://" + str(r.url).split("/")[2] + a["href"]) if a and a.get("href", "").startswith("/") else "")

sec("SOMPO / AXA / ALLIANZ / SULAMERICA")
for u in ["https://sompo.com.br/carreiras", "https://axa.com.br/trabalhe-conosco", "https://careers.allianz.com/global/en/search-results?keywords=&location=Brazil", "https://www.sulamerica.com.br/", "https://portal.sulamericaseguros.com.br/"]:
    try:
        r = c.get(u)
    except Exception as e:
        print("XX", u, type(e).__name__); continue
    links = sorted(set(a["href"] for a in BeautifulSoup(r.text, "html.parser").find_all("a", href=True) if re.search(r"vaga|carreir|trabalh|career|job|gupy|inhire|workday|csod", a["href"], re.I)))
    print(r.status_code, u, links[:15])
