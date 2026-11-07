"""Sonda temporária 4: Icatu."""
import json, re
import httpx
c = httpx.Client(headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True, timeout=25)
r = c.get("https://api.inhire.app/job-posts/public/pages", headers={"X-Tenant": "icatu"})
for j in r.json().get("jobsPage", []):
    print("ICATU |", j.get("displayName"), "|", j.get("location"), "|", j.get("workplaceType"), "|", j.get("publishedAt") or j.get("createdAt"), "| https://icatu.inhire.app/vagas/%s" % j.get("jobId"))
