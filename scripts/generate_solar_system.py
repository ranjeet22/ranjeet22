#!/usr/bin/env python3
"""Generate an animated GitHub Solar System SVG from public GitHub data."""
import json, math, os, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = os.getenv('GITHUB_USERNAME', 'ranjeet22')
TOKEN = os.getenv('GITHUB_TOKEN', '')
OUT = Path(os.getenv('OUTPUT_PATH', 'assets/solar-system.svg'))
W, H, CX, CY = 1200, 700, 600, 355
COLORS = {'Python':'#4387c8','JavaScript':'#f0db4f','TypeScript':'#3178c6','Jupyter Notebook':'#f07825','HTML':'#e76f45','CSS':'#a77bd0','Java':'#e76f51','C++':'#659ad2','C':'#8c9ab5','Go':'#55b9c7','Kotlin':'#a77be8','Rust':'#b97850','PHP':'#777bb4','Shell':'#8caa62','Ruby':'#cc342d'}
FALLBACK = ['#56b6c2','#e5a84b','#9c83d9','#e47b88','#69a6d8','#8ebc83']

def api(path):
    headers = {'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'github-solar-system'}
    if TOKEN: headers['Authorization'] = f'Bearer {TOKEN}'
    req = urllib.request.Request('https://api.github.com'+path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

def fetch_data():
    profile = api(f'/users/{USERNAME}')
    repos = api(f'/users/{USERNAME}/repos?per_page=100&sort=pushed&type=owner')
    repos = [r for r in repos if not r.get('fork') and not r.get('archived')]
    totals, related = Counter(), defaultdict(list)
    for repo in repos[:60]:
        try: langs = api(f"/repos/{USERNAME}/{repo['name']}/languages")
        except Exception as e:
            print(f"Skipping language data for {repo['name']}: {e}"); continue
        for lang, size in langs.items():
            totals[lang] += size; related[lang].append(repo)
    total = sum(totals.values()) or 1
    languages = []
    for lang, size in totals.most_common(7):
        items = sorted(related[lang], key=lambda r:r.get('pushed_at') or '', reverse=True)[:4]
        languages.append({'name':lang,'percent':round(size*100/total,1),'repos':[{'name':r['name'],'url':r['html_url']} for r in items]})
    events = api(f'/users/{USERNAME}/events/public?per_page=100')
    pushes = []
    for e in events:
        if e.get('type') == 'PushEvent':
            full = e.get('repo',{}).get('name','')
            pushes.append({'repo':full.split('/',1)[-1],'url':'https://github.com/'+full,'count':len(e.get('payload',{}).get('commits',[]))})
    return {'login':profile['login'],'avatar':profile['avatar_url'],'languages':languages,'pushes':pushes[:5],'updated':datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

def build_svg(d):
    langs = d.get('languages',[])[:7] or [{'name':'No language data','percent':0,'repos':[]}]
    radii, speeds = [125,175,225,275,325,375,425], [22,29,37,46,55,66,78]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100%" viewBox="0 0 {W} {H}" role="img" aria-label="Animated GitHub solar system for {escape(d["login"])}">']
    s.append('''<defs>
      <radialGradient id="spaceGlow"><stop offset="0" stop-color="#f7c85b" stop-opacity=".27"/><stop offset="1" stop-color="#f7c85b" stop-opacity="0"/></radialGradient>
      <radialGradient id="sun"><stop offset="0" stop-color="#fff7cf"/><stop offset=".7" stop-color="#ffc94f"/><stop offset="1" stop-color="#f39a38"/></radialGradient>
      <filter id="glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <clipPath id="avatarClip"><circle cx="600" cy="355" r="38"/></clipPath>
    </defs>''')
    s.append('<rect width="1200" height="700" rx="22" fill="#070910"/>')
    s.append('<ellipse cx="600" cy="355" rx="210" ry="180" fill="url(#spaceGlow)"/>')
    for i in range(150):
        x,y=(i*197+31)%W,(i*113+19)%H
        s.append(f'<circle cx="{x}" cy="{y}" r="{.6+(i%4)*.28:.1f}" fill="#dbe5ff" opacity="{.22+(i%7)*.09:.2f}"/>')
    s.append(f'<text x="34" y="43" fill="#d8dbe5" font-family="monospace" font-size="15" letter-spacing="2">GITHUB SOLAR SYSTEM · @{escape(d["login"].upper())}</text>')
    for r in radii[:len(langs)]: s.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{r}" ry="{r*.57:.1f}" fill="none" stroke="#778198" stroke-opacity=".24" stroke-width="1.1" stroke-dasharray="4 8"/>')
    avatar = escape(d.get('avatar','https://github.com/identicons/ranjeet22.png'), {'"':'&quot;'})
    s += [f'<circle cx="{CX}" cy="{CY}" r="70" fill="url(#spaceGlow)"/>',f'<circle cx="{CX}" cy="{CY}" r="49" fill="url(#sun)" filter="url(#glow)"/>',f'<circle cx="{CX}" cy="{CY}" r="42" fill="#111827"/>',f'<image x="{CX-38}" y="{CY-38}" width="76" height="76" href="{avatar}" xlink:href="{avatar}" clip-path="url(#avatarClip)"/>',f'<circle cx="{CX}" cy="{CY}" r="49" fill="none" stroke="#ffd36a" stroke-width="5"/>',f'<text x="{CX}" y="{CY+72}" text-anchor="middle" fill="#f0e7d4" font-family="monospace" font-size="13">@{escape(d["login"])}</text>']
    for i,lang in enumerate(langs):
        r=radii[i]; angle=-90+i*49; a=math.radians(angle); x=CX+r*math.cos(a); y=CY+r*.57*math.sin(a)
        color=COLORS.get(lang['name'],FALLBACK[i%len(FALLBACK)])
        size=max(12,min(25,11+math.sqrt(max(lang.get('percent',0),0))*2))
        s.append(f'<g transform="translate({CX} {CY})"><g><animateTransform attributeName="transform" type="rotate" from="{angle}" to="{angle+360}" dur="{speeds[i]}s" repeatCount="indefinite"/><g transform="translate({r} 0) scale(1 .57)">')
        s.append(f'<circle r="{size}" fill="{color}" stroke="#fff" stroke-opacity=".45" stroke-width="1.5" filter="url(#glow)"/>')
        initials=escape(''.join(w[0] for w in lang['name'].split()[:2]).upper()[:2])
        s.append(f'<text y="5" text-anchor="middle" fill="#fff" font-family="Arial" font-size="{max(9,size*.75):.1f}" font-weight="700">{initials}</text>')
        for j,repo in enumerate(lang.get('repos',[])[:3]):
            ma=math.radians(j*120); mr=size+14+j*3; mx,my=mr*math.cos(ma),mr*math.sin(ma)
            url=escape(repo['url'],{'"':'&quot;'})
            s.append(f'<a href="{url}" xlink:href="{url}"><title>{escape(repo["name"])}</title><circle cx="{mx:.1f}" cy="{my:.1f}" r="3.5" fill="#dce5f6" stroke="#070910" stroke-width="1"/></a>')
        s.append('</g></g>')
        s.append(f'<text x="{x:.1f}" y="{y+size+18:.1f}" text-anchor="middle" fill="#dce2ed" font-family="monospace" font-size="13" font-weight="600">{escape(lang["name"])} · {lang.get("percent",0):.1f}%</text>')
        if lang.get('repos'):
            url=escape(lang['repos'][0]['url'],{'"':'&quot;'})
            s.append(f'<a href="{url}" xlink:href="{url}"><title>Explore {escape(lang["repos"][0]["name"])}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="{size+5}" fill="transparent"/></a>')
        s.append('</g>')
    for i,p in enumerate(d.get('pushes',[])[:5]):
        x,y=110+i*220,590-(i%2)*35; url=escape(p['url'],{'"':'&quot;'})
        s.append(f'<a href="{url}" xlink:href="{url}"><title>{escape(p["repo"])} · {p["count"]} commits</title><path d="M{x-32} {y+12} Q{x-8} {y-5} {x+14} {y}" stroke="#8eb9ee" stroke-opacity=".5" stroke-width="2" fill="none"/><circle cx="{x+14}" cy="{y}" r="3.5" fill="#d8edff"><animate attributeName="opacity" values=".3;1;.3" dur="2.8s" repeatCount="indefinite"/></circle><text x="{x+22}" y="{y+4}" fill="#aebbd0" font-family="monospace" font-size="10">{escape(p["repo"][:22])}</text></a>')
    s.append(f'<text x="34" y="674" fill="#8992a4" font-family="monospace" font-size="11">PUBLIC GITHUB DATA · {escape(d.get("updated",""))}</text>')
    s.append('<text x="1166" y="674" text-anchor="end" fill="#8992a4" font-family="monospace" font-size="11">PLANETS = LANGUAGES · MOONS = REPOS · COMETS = PUSHES</text></svg>')
    return '\n'.join(s)

if __name__ == '__main__':
    data=fetch_data(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(build_svg(data),encoding='utf-8')
    print(f"Generated {OUT}: {len(data['languages'])} languages, {len(data['pushes'])} recent pushes")
