"""Generate a profile from public GitHub data; standard library only."""

from __future__ import annotations

import base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import html
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER = "beemines"
TAGLINE = "Student · Full-stack Developer · Agent Explorer"


def api(path, body=None):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("A GitHub token is required to refresh public profile data")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "beemines-profile",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    request = urllib.request.Request(
        "https://api.github.com" + path,
        data=None if body is None else json.dumps(body).encode(),
        headers=headers,
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(2**attempt)


def esc(value):
    return html.escape(str(value), quote=True)


def svg(width, height, content, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img"><title>{esc(label)}</title>'
        f"<style>text{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}}</style>{content}</svg>"
    )


def save(name, content):
    ET.fromstring(content)
    (ASSETS / name).write_text(content, encoding="utf-8")


def text(x, y, value, fill, size=12, weight=400, extra=""):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" {extra}>{esc(value)}</text>'


def banner():
    image = base64.b64encode((ASSETS / "forest-background.png").read_bytes()).decode()
    content = f'<image width="2172" height="724" href="data:image/png;base64,{image}"/>'
    content += "<defs>"
    for name, count, width, begin, dur, y, height in [
        ("name", 8, 680, 0, 1.05, 180, 150),
        ("tagline", len(TAGLINE), 890, 1.25, 2.6, 337, 48),
    ]:
        values = ";".join(f"{width * i / count:.2f}" for i in range(count + 1))
        content += (
            f'<clipPath id="{name}"><rect x="125" y="{y}" width="{width}" height="{height}">'
            f'<animate attributeName="width" values="{values}" dur="{dur}s" begin="{begin}s" calcMode="discrete" fill="freeze"/>'
            "</rect></clipPath>"
        )
    content += "</defs><style>@media(prefers-reduced-motion:reduce){.type{clip-path:none}.cursor{display:none}}</style>"
    content += '<g class="type" clip-path="url(#name)"><text x="125" y="300" fill="#284a36" font-family="monospace" font-size="132" font-weight="800">beemines</text></g>'
    content += f'<g class="type" clip-path="url(#tagline)">{text(125, 369, TAGLINE, "#284a36", 31, 600)}</g>'
    content += '<rect class="cursor" x="125" y="190" width="5" height="118" fill="#284a36"><animate attributeName="x" from="125" to="805" dur="1.05s" fill="freeze"/><set attributeName="visibility" to="hidden" begin="1.1s"/></rect>'
    save("header.svg", svg(2172, 724, content, f"beemines — {TAGLINE}"))


def palette(dark):
    return (
        ("#0d1117", "#30363d", "#e6edf3", "#9198a1", "#9bbf98")
        if dark
        else ("#ffffff", "#d1d9e0", "#1f2328", "#59636e", "#4b7658")
    )


def cards(stats, languages, colors, dark):
    bg, line, fg, muted, accent = palette(dark)
    frame = f'<rect x=".5" y=".5" width="359" height="145" rx="5" fill="{bg}" stroke="{line}"/>'
    content = frame + text(16, 25, "beemines' GitHub stats", accent, 13, 600)
    rows = [
        ("Contributions", stats["contributionCalendar"]["totalContributions"]),
        ("Pull requests", stats["totalPullRequestContributions"]),
        ("Commits", stats["totalCommitContributions"]),
        ("Issues", stats["totalIssueContributions"]),
    ]
    for i, (name, value) in enumerate(rows):
        content += text(16, 48 + i * 20, name, muted) + text(
            343, 48 + i * 20, value, fg, 12, 600, 'text-anchor="end"'
        )
    content += text(16, 134, "Past year · GitHub contribution data", muted, 9)
    suffix = "dark" if dark else "light"
    save(
        f"stats-{suffix}.svg",
        svg(360, 146, content, "GitHub contribution statistics for the past year"),
    )
    content = frame + text(16, 25, "Most used languages", accent, 13, 600)
    total = sum(languages.values())
    if total:
        ranked = sorted(languages.items(), key=lambda pair: -pair[1])
        shown = ranked[:5] + (
            [("Other", sum(n for _, n in ranked[5:]))] if len(ranked) > 5 else []
        )
        colors = dict(colors, Other="#89947d")
        x = 16
        for name, count in shown:
            width = count / total * 328
            content += f'<rect x="{x:.2f}" y="39" width="{max(0.1, width - 0.7):.2f}" height="7" fill="{colors[name]}"/>'
            x += width
        for i, (name, count) in enumerate(shown):
            x, y = 16 + (i % 2) * 166, 67 + (i // 2) * 19
            content += (
                f'<circle cx="{x + 3}" cy="{y - 4}" r="3" fill="{colors[name]}"/>'
            )
            content += text(x + 12, y, name, fg, 11) + text(
                x + 152,
                y,
                f"{count / total * 100:.1f}%",
                muted,
                10,
                400,
                'text-anchor="end"',
            )
    else:
        content += text(16, 68, "No public language data yet", muted)
    content += text(16, 134, "Public original repositories · Code bytes", muted, 9)
    save(
        f"languages-{suffix}.svg",
        svg(
            360,
            146,
            content,
            "Language distribution by bytes in public original repositories",
        ),
    )


def bee_calendar(calendar, dark):
    bg, line, fg, muted, accent = palette(dark)
    weeks = calendar["weeks"]
    cell, left, top = 12, 20, 37
    width = len(weeks) * cell + 40
    height = 150
    levels = [
        "#161b22" if dark else "#ebedf0",
        "#0e4429" if dark else "#9be9a8",
        "#006d32" if dark else "#40c463",
        "#26a641" if dark else "#30a14e",
        "#39d353" if dark else "#216e39",
    ]
    index = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }
    content = f'<rect width="{width}" height="{height}" fill="{bg}"/>'
    points = []
    seen = set()
    for col, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = datetime.strptime(day["date"], "%Y-%m-%d")
            month = (date.year, date.month)
            if month not in seen:
                if col < len(weeks) - 2:
                    content += text(
                        left + col * cell, 19, date.strftime("%b"), muted, 10
                    )
                seen.add(month)
            x, y = left + col * cell, top + day["weekday"] * cell
            content += f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{levels[index[day["contributionLevel"]]]}"><title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>'
            if day["contributionCount"]:
                points.append((x + 5, y + 5))
    content += text(
        20,
        141,
        f"{calendar['totalContributions']} contributions · Past year",
        muted,
        10,
    )
    content += text(width - 118, 141, "Less", muted, 9)
    for i, color in enumerate(levels):
        content += f'<rect x="{width - 93 + i * 11}" y="133" width="8" height="8" rx="1" fill="{color}"/>'
    content += text(width - 34, 141, "More", muted, 9)
    if points:
        path = f"M {points[0][0]} {points[0][1] - 9}"
        for i, a in enumerate(points):
            b = points[(i + 1) % len(points)]
            path += f" L {a[0]} {a[1] - 9}"
            path += f" Q {(a[0] + b[0]) / 2:.1f} {max(24, min(a[1], b[1]) - 26)} {b[0]} {b[1] - 9}"
        motion = f'<animateMotion dur="{max(8, len(points) * 1.4):.1f}s" repeatCount="indefinite" path="{path}"/>'
        content += "<style>@media(prefers-reduced-motion:reduce){.bee-flight{display:none}}</style>"
        content += f'<g class="bee-flight">{motion}<g transform="scale(.8)" shape-rendering="crispEdges">'
        content += '<g><animateTransform attributeName="transform" type="scale" values="1 1;1 .65;1 1" dur=".12s" repeatCount="indefinite"/><rect x="-8" y="-15" width="7" height="7" fill="#b9e2eb"/><rect x="1" y="-17" width="7" height="9" fill="#d7f1f4"/></g>'
        for x, y, w, h, color in [
            (-9, -7, 16, 10, "#332819"),
            (-7, -9, 12, 14, "#332819"),
            (-7, -7, 4, 10, "#ffcc4d"),
            (0, -7, 4, 10, "#ffcc4d"),
            (6, -5, 5, 8, "#332819"),
            (8, -4, 2, 2, "#fff"),
            (-12, -3, 3, 3, "#332819"),
        ]:
            content += (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'
            )
        content += "</g></g>"
    save(
        f"bee-{'dark' if dark else 'light'}.svg",
        svg(
            width,
            height,
            content,
            "A bee visiting dates with real GitHub contributions",
        ),
    )


def readme(merged):
    lines = [
        '<img src="./assets/header.svg" width="100%" alt="beemines — Student · Full-stack Developer · Agent Explorer" />',
        "",
        "<p>",
    ]
    for name in [
        "Java",
        "Python",
        "JavaScript",
        "Vue",
        "Spring Boot",
        "MySQL",
        "Redis",
        "Git",
    ]:
        safe = name.replace(" ", "_")
        lines.append(
            f'  <img src="https://img.shields.io/badge/{safe}-315341?style=flat-square" alt="{name}" />'
        )
    lines += ["</p>", "", "#### GitHub activity", "", "<p>"]
    for name, label in [
        ("stats", "GitHub contribution statistics"),
        ("languages", "Most used languages"),
    ]:
        lines += [
            "  <picture>",
            f'    <source media="(prefers-color-scheme: dark)" srcset="./assets/{name}-dark.svg" />',
            f'    <img src="./assets/{name}-light.svg" width="48%" alt="{label}" />',
            "  </picture>",
        ]
    lines += [
        "</p>",
        "",
        "#### Contribution trail",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="./assets/bee-dark.svg" />',
        '  <img src="./assets/bee-light.svg" width="100%" alt="A bee flying over my real GitHub contribution calendar" />',
        "</picture>",
        "",
        "#### Selected contributions",
        "",
    ]
    for item in merged[:6]:
        name = item["repo"].split("/")[-1]
        lines.append(
            f"- **[{name} #{item['number']}]({item['url']})** · Merged  \n  {item['summary']}"
        )
    if not merged:
        lines.append("Selected merged contributions will appear here.")
    lines += [
        "",
        "<sub>Profile data refreshes every six hours. The list includes selected, merged pull requests.</sub>",
        "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    query = """query($login:String!,$after:String){user(login:$login){contributionsCollection{totalCommitContributions totalIssueContributions totalPullRequestContributions contributionCalendar{totalContributions weeks{contributionDays{date weekday contributionCount contributionLevel}}}} repositories(first:100,after:$after,ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){pageInfo{hasNextPage endCursor}nodes{name languages(first:100,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""
    stats = None
    languages = defaultdict(int)
    colors = {}
    after = None
    while True:
        result = api(
            "/graphql", {"query": query, "variables": {"login": USER, "after": after}}
        )
        if result.get("errors"):
            raise RuntimeError("GitHub GraphQL failed: " + json.dumps(result["errors"]))
        user = result["data"]["user"]
        stats = user["contributionsCollection"]
        for repo in user["repositories"]["nodes"]:
            if repo["name"] == USER:
                continue
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                languages[name] += edge["size"]
                colors[name] = edge["node"]["color"] or "#8b949e"
        info = user["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            break
        after = info["endCursor"]
    candidates = json.loads(
        (ROOT / "selected-contributions.json").read_text(encoding="utf-8")
    )

    def check(item):
        pr = api(f"/repos/{item['repo']}/pulls/{item['number']}")
        if pr["user"]["login"].lower() != USER or not pr["merged"]:
            return None
        return dict(item, url=pr["html_url"], merged_at=pr["merged_at"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        merged = [item for item in pool.map(check, candidates) if item]
    merged.sort(key=lambda item: item["merged_at"], reverse=True)
    ASSETS.mkdir(exist_ok=True)
    banner()
    for dark in [False, True]:
        cards(stats, languages, colors, dark)
        bee_calendar(stats["contributionCalendar"], dark)
    readme(merged)
    print(
        f"Generated profile: {stats['contributionCalendar']['totalContributions']} contributions; {len(merged)} selected merged PRs"
    )


if __name__ == "__main__":
    main()
