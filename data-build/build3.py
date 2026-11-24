import json,collections,time,math
import front as F
from shapely.geometry import Point,Polygon,LineString,shape
from shapely.strtree import STRtree
t=time.time()
def pts(path): return [Point(f['geometry']['x'],f['geometry']['y']) for f in json.load(open(path)) if f.get('geometry')]
# pavement polygons
PV=[];PVs=[]
for f in json.load(open('pave.json')):
    g=f.get('geometry'); a=f['attributes']
    if not g or a.get('TYPE') not in ('STREET','ALLEY'): continue
    for r in g['rings']:
        if len(r)>=4:
            p=Polygon(r).buffer(0)
            if not p.is_empty: PV.append(p);PVs.append(((a.get('TYPE')),(a.get('SURFACETYPE') or '').strip()))
pvt=STRtree(PV)
CB=pts('cb.json');cbt=STRtree(CB)
LT=pts('lights.json');ltt=STRtree(LT)
def lines(path,keep=lambda a:True):
    L=[];A=[]
    for f in json.load(open(path)):
        g=f.get('geometry')
        if not g or not keep(f['attributes']): continue
        for p in g['paths']:
            if len(p)>1: L.append(LineString(p));A.append(f['attributes'])
    return L,A
SM,_=lines('smain.json');smt=STRtree(SM)
PM,PMA=lines('pmp.json',lambda a:(a.get('Status')=='INCOMPLETE') and any(k in (a.get('Recommendation') or '') for k in ('NEW SIDEWALK','WIDEN')));pmt=STRtree(PM)
AL,ALA=lines('alleys.json');alt=STRtree(AL)
WW=[(F.wl[k]) for k in range(len(F.wl))]
walkW=[]
for f in json.load(open('walks.json')):
    if f.get('geometry') and f['attributes'].get('TRAIL')!='Yes':
        for p in f['geometry']['paths']:
            if len(p)>1: walkW.append(f['attributes'].get('WIDTH'))
PAVED={'ACP','PCC','PC','BST','BR'}
CURBC={'C&G':1,'CURB':2,'THICKN':3,'NONE':4}
def curbcode(ct,walk=False):
    # City street centerline CurbType1/CurbType2 (2024-25 pavement survey). Type2 is a secondary type, not the other side:
    # 0 no record, 1 curb and gutter, 2 curb without gutter, 3 thickened edge, 4 none; +10 = block has two types, side inferred from sidewalk
    if not ct or not ct[0]: return 0
    a=CURBC.get(ct[0],0); b=CURBC.get(ct[1] or 'NONE',4)
    if b in (4,a) or not a: return a
    # mixed: two curb types on one block, side not recorded. Assume the better one sits on the side with sidewalk.
    hi_,lo_=min(a,b),max(a,b)
    return 10+(hi_ if walk else lo_)
def outward(line,poly,d):
    out=[]
    n=max(3,int(line.length//10))
    for k in range(n):
        t=(k+0.5)/n*line.length;p=line.interpolate(t);p2=line.interpolate(min(line.length,t+1));p1=line.interpolate(max(0,t-1))
        ang=math.atan2(p2.y-p1.y,p2.x-p1.x);nx,ny=-math.sin(ang),math.cos(ang)
        q=Point(p.x+nx*d,p.y+ny*d)
        if poly.contains(q) or poly.distance(q)<d*0.5: q=Point(p.x-nx*d,p.y-ny*d)
        out.append(q)
    return out
def pave_at(q):
    for j in pvt.query(q):
        if PV[j].contains(q): return PVs[j]
    return None
def enrich(poly,r):
    L=r['line']; strip=L.buffer(16)
    # paving: sample points 14 ft out
    hits=[pave_at(q) for q in outward(L,poly,14)]
    st=[h for h in hits if h and h[0]=='STREET']
    pv=sum(1 for h in st if h[1] in PAVED); gv=sum(1 for h in st if h[1]=='GRV')
    if len(st)>=0.5*len(hits) and (pv or gv): paved=1 if pv>=gv else 0; known=1
    elif len(st)>=0.5*len(hits): paved=1; known=0   # street pavement mapped, surface type blank or unknown
    else: paved=r['paved'];known=0
    _g=list(getattr(L,'geoms',[L]));c=list(_g[0].coords)+list(_g[-1].coords);a0,a1=c[0],c[-1];dx,dy=a1[0]-a0[0],a1[1]-a0[1];dl=math.hypot(dx,dy) or 1;ux,uy=dx/dl,dy/dl
    ext=LineString([(a0[0]-ux*100,a0[1]-uy*100),(a1[0]+ux*100,a1[1]+uy*100)])
    curb=curbcode(r.get('ct'),r.get('walk'))
    smain=1 if any(SM[k].distance(L)<=45 for k in smt.query(L.buffer(45))) else 0
    light=1 if any(LT[k].distance(L)<=25 for k in ltt.query(L.buffer(25))) else 0
    tier=0
    for k in pmt.query(L.buffer(40)):
        if PM[k].distance(L)<=40 and PM[k].buffer(40).intersection(L).length>=0.3*L.length:
            tier=max(tier,int(PMA[k].get('Tier') or 0)+1)
    narrow=0
    if r['walk']:
        ws=[walkW[k] for k in F.wtree.query(L.buffer(22)) if F.wl[k].distance(L)<=22 and walkW[k]]
        if ws and min(ws)<5: narrow=1
    return paved,known,curb,smain,light,tier,narrow
pcode={a['OBJECTID']:a['PARCEL_CODE'] for a in json.load(open('pcodes.json'))}
names=[];nid={};out=[];seen=set();st=collections.Counter()
def N(n):
    if n not in nid: nid[n]=len(names);names.append(n)
    return nid[n]
for i,a in enumerate(F.attrs):
    ad=(a['Site_Address'] or '').strip()
    if not ad:
        pc=pcode.get(a['OBJECTID'])
        if not pc: continue
        ad='PARCEL '+pc
    elif a.get('Site_City')!='BELLINGHAM' or not ad[0].isdigit(): continue
    if ad in seen or F.polys[i].area>400000: continue
    try: r=F.analyze(i)
    except Exception: st['err']+=1;continue
    if not ad.startswith('PARCEL'):
        try:
            r,fx=F.addr_fix(i,r,ad)
            if fx: st['fixed']+=1
        except Exception: st['fixerr']+=1
    fr=[x for x in r if x['kind']=='street']
    poly=F.polys[i]
    if not fr:
        # recover frontage from street pavement polygons (streets with no centerline)
        segs=[]
        for s_a,s_b,Ls,ang in F.sides(poly):
            seg=LineString([s_a,s_b])
            if Ls<12: continue
            qs=outward(seg,poly,10); h=[pave_at(q) for q in qs]
            if sum(1 for x in h if x and x[0]=='STREET')>=0.6*len(h): segs.append(seg)
        if segs:
            from shapely.ops import unary_union,linemerge
            ln=linemerge(unary_union(segs)) if len(segs)>1 else segs[0]
            parts=list(getattr(ln,'geoms',[ln]))
            for g in parts:
                if g.length>=12:
                    cov,inc=F.walkcov(g,22)
                    fr.append(dict(name='Street with no mapped centerline',len=round(g.length,1),kind='street',cls='local',walk=cov>=0.5,inc=inc,paved=True,line=g))
            if fr: st['recovered']+=1
    if not fr: st['nofront']+=1;continue
    al=sum(x['len'] for x in r if x['kind']=='alley')
    alinfo=0
    if al:
        near=[k for k in alt.query(poly.buffer(30)) if AL[k].distance(poly)<=30]
        if near:
            sf=(ALA[near[0]].get('SURFACETYPE') or '').strip(); alinfo=2 if sf in ('GRV',) else 1
    seen.add(ad);st['ok']+=1
    rows=[]
    for x in fr[:6]:
        pv,known,curb,sm,lt,tier,nar=enrich(poly,x)
        rows.append([N(x['name']),x['len'],1 if x['cls']=='arterial' else 0,(2 if x['inc'] else 1) if x['walk'] else 0,pv,curb,sm,lt,tier,nar,known])
        st['curb']+=curb;st['pmp']+=tier>0;st['unpaved']+=pv==0;st['narrow']+=nar
    out.append([ad,round(poly.area),round(al),rows,0,alinfo])
out.sort(key=lambda x:x[0])
json.dump({'asof':'2026-11-24','streets':names,'lots':out},open('lots3.json','w'),separators=(',',':'))
print(st,len(names),round(time.time()-t))
