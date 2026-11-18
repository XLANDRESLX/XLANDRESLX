"""Genera assets/stats.svg con datos de la API de GitHub (solo GITHUB_TOKEN, sin servicios externos)."""
import os, json, datetime, urllib.request, urllib.error
from html import escape
USER = os.environ.get("GH_USER", "XLANDRESLX")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
Q = """query($u:String!){user(login:$u){followers{totalCount}
repositories(ownerAffiliation:OWNER,isFork:false,first:100,privacy:PUBLIC){totalCount nodes{stargazerCount languages(first:5,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}
contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}"""
def fetch():
    if os.environ.get("MOCK"):
        import random; random.seed(3); days=[]
        d=datetime.date.today()-datetime.timedelta(days=364)
        for i in range(365): days.append({"contributionCount":random.choice([0,0,1,2,4]),"date":str(d+datetime.timedelta(days=i))})
        weeks=[{"contributionDays":days[i:i+7]} for i in range(0,365,7)]
        L=lambda n,c,s:{"size":s,"node":{"name":n,"color":c}}
        return {"followers":{"totalCount":4},"repositories":{"totalCount":9,"nodes":[{"stargazerCount":3,"languages":{"edges":[L("PHP","#4F5D95",900),L("JavaScript","#f1e05a",500),L("CSS","#563d7c",300),L("HTML","#e34c26",200)]}}]},
                "contributionsCollection":{"contributionCalendar":{"totalContributions":sum(x["contributionCount"] for x in days),"weeks":weeks}}}
    req=urllib.request.Request("https://api.github.com/graphql",json.dumps({"query":Q,"variables":{"u":USER}}).encode(),{"Authorization":"bearer "+TOKEN})
    try:
        with urllib.request.urlopen(req) as resp:
            body=json.load(resp)
    except urllib.error.HTTPError as e:
        detail=e.read().decode() if hasattr(e,"read") else str(e)
        raise RuntimeError(f"GitHub GraphQL falló (HTTP {e.code}): {detail}") from None
    if "errors" in body or "data" not in body:
        raise RuntimeError(f"GitHub GraphQL no devolvió datos: {body}")
    return body["data"]["user"]
u=fetch(); cal=u["contributionsCollection"]["contributionCalendar"]
days=[d for w in cal["weeks"] for d in w["contributionDays"]]
cur=best=run=0
for d in days:
    run=run+1 if d["contributionCount"]>0 else 0; best=max(best,run)
cur=0
for d in reversed(days):
    if d["contributionCount"]>0: cur+=1
    elif d is days[-1]: continue
    else: break
stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
lang={}
for r in u["repositories"]["nodes"]:
    for e in r["languages"]["edges"]:
        n=e["node"]; x=lang.setdefault(n["name"],[0,n["color"] or "#8B949E"]); x[0]+=e["size"]
top=sorted(lang.items(),key=lambda kv:-kv[1][0])[:5]; tot=sum(v[0] for _,v in top) or 1
stats=[("Contribuciones (año)",cal["totalContributions"]),("Racha actual",f"{cur} d"),("Mejor racha",f"{best} d"),("Repos públicos",u["repositories"]["totalCount"]),("Estrellas",stars),("Seguidores",u["followers"]["totalCount"])]
o=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 300" width="100%" role="img" aria-label="Estadísticas de GitHub"><style>text{font-family:ui-monospace,Menlo,Consolas,monospace;fill:#C9D6DD}.v{font-size:30px;font-weight:700;fill:#F2F6F8}.k{font-size:12px;fill:#7FA3B5}.h{font-size:14px;fill:#38BDF8}</style><rect width="900" height="300" rx="14" fill="#0E1A22" stroke="#22343F"/>']
for i,(k,v) in enumerate(stats):
    x=40+(i%3)*150; y=60+(i//3)*80
    o.append(f'<text class="v" x="{x}" y="{y}">{escape(str(v))}</text><text class="k" x="{x}" y="{y+20}">{escape(k)}</text>')
o.append('<text class="h" x="520" y="40">Lenguajes más usados</text>')
y=65
for n,(s,c) in top:
    p=s/tot*100; o.append(f'<text class="k" x="520" y="{y+12}">{escape(n)}</text><rect x="620" y="{y}" width="240" height="12" rx="6" fill="#16262F"/><rect x="620" y="{y}" width="{240*p/100:.0f}" height="12" rx="6" fill="{c}"><animate attributeName="width" from="0" to="{240*p/100:.0f}" dur="1.2s" fill="freeze"/></rect>'); y+=36
# mapa de calor de los últimos 26 semanas
o.append('<text class="h" x="40" y="215">Actividad reciente</text>')
for wi,w in enumerate(cal["weeks"][-40:]):
    for di,d in enumerate(w["contributionDays"]):
        c=d["contributionCount"]; col="#16262F" if c==0 else "#0E5A7A" if c<3 else "#38BDF8" if c<6 else "#F59E0B"
        o.append(f'<rect x="{40+wi*20}" y="{228+di*9}" width="16" height="7" rx="2" fill="{col}"><title>{d["date"]}: {c}</title></rect>')
o.append(f'<text class="k" x="860" y="40" text-anchor="end">Actualizado {datetime.date.today()}</text></svg>')
os.makedirs("assets",exist_ok=True); open("assets/stats.svg","w").write("".join(o)); print("ok")
