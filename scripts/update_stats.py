#!/usr/bin/env python3
"""Update GitHub stats baked into neofetch-*.svg (tspan ids: stat_*).

Uses STATS_TOKEN (PAT, sees private repos) if set, else GITHUB_TOKEN.
With a token that can't see private repos, the total-repos and contribution
numbers are only updated when they grow (never downgraded to public-only).
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("STATS_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
FULL_ACCESS = bool(os.environ.get("STATS_TOKEN"))
LOGIN = "ksanyok"
CREATED = datetime(2018, 10, 19, tzinfo=timezone.utc)

QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER) {
      totalCount
      nodes { stargazerCount isPrivate }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
  }
}
""" % LOGIN

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
data = json.load(urllib.request.urlopen(req))["data"]["user"]

repos_total = data["repositories"]["totalCount"]
public = sum(1 for n in data["repositories"]["nodes"] if not n["isPrivate"])
stars = sum(n["stargazerCount"] for n in data["repositories"]["nodes"])
contribs = data["contributionsCollection"]["contributionCalendar"]["totalContributions"]

now = datetime.now(timezone.utc)
months = (now.year - CREATED.year) * 12 + now.month - CREATED.month
if now.day < CREATED.day:
    months -= 1
uptime = f"{months // 12} yrs {months % 12} mos on GitHub"

def current(svg, sid):
    m = re.search(f'id="{sid}"[^>]*>([^<]*)<', svg)
    return m.group(1) if m else None

def set_stat(svg, sid, value):
    return re.sub(f'(id="{sid}"[^>]*>)[^<]*(<)', lambda m: m.group(1) + str(value) + m.group(2), svg)

for fn in ("neofetch-dark.svg", "neofetch-light.svg"):
    svg = open(fn, encoding="utf-8").read()
    svg = set_stat(svg, "stat_uptime", uptime)
    svg = set_stat(svg, "stat_public", public)
    svg = set_stat(svg, "stat_stars", stars)
    old_repos = current(svg, "stat_repos")
    old_contribs = current(svg, "stat_contribs")
    if FULL_ACCESS or (old_repos and repos_total >= int(old_repos)):
        svg = set_stat(svg, "stat_repos", repos_total)
    if FULL_ACCESS or (old_contribs and contribs >= int(old_contribs.replace(",", ""))):
        svg = set_stat(svg, "stat_contribs", f"{contribs:,}")
    open(fn, "w", encoding="utf-8").write(svg)
    print(f"{fn}: repos={repos_total} public={public} stars={stars} contribs={contribs} uptime='{uptime}'")

sys.exit(0)
