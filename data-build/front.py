import json,math,sys
from shapely.geometry import Polygon,LineString,MultiLineString,Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
A=json.load(open('allparcels.json'));S=json.load(open('streets.json'));W=json.load(open('walks.json'))
polys=[];attrs=[]
for f in A:
    g=f.get('geometry')
    if not g: continue
    rs=[r for r in g['rings'] if len(r)>=4]
    if not rs: continue
    rs.sort(key=lambda r:-abs(Polygon(r).area))
    p=Polygon(rs[0]).buffer(0)
    if p.is_empty or p.area<300: continue
    polys.append(p);attrs.append(f['attributes'])
ptree=STRtree(polys)
sl=[];sa=[]
for f in S:
    g=f.get('geometry')
    if not g: continue
    for pth in g['paths']:
        if len(pth)>1: sl.append(LineString(pth));sa.append(f['attributes'])
stree=STRtree(sl)
wl=[];winc=[]
for f in W:
    if f.get('geometry') and f['attributes'].get('TRAIL')!='Yes':
        for p in f['geometry']['paths']:
            if len(p)>1: wl.append(LineString(p));winc.append(f['attributes'].get('INCOMPLETE')=='Yes')
wtree=STRtree(wl)
def inparcel(pt,skip):
    for j in ptree.query(pt):
        if j!=skip and polys[j].contains(pt): return True
    return False
def sides(poly):
    c=list(poly.exterior.coords)[:-1];n=len(c)
    if poly.exterior.is_ccw: c=c[::-1]   # clockwise: outward normal is left of travel
    segs=[]
    for i in range(n):
        a,b=c[i],c[(i+1)%n];L=math.hypot(b[0]-a[0],b[1]-a[1])
        if L<0.5: continue
        segs.append((a,b,L,math.atan2(b[1]-a[1],b[0]-a[0])))
    return segs
def analyze(i):
    poly=polys[i];out=[];addr=(attrs[i]['Site_Address'] or '')
    for a,b,L,ang in sides(poly):
        mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
        nx,ny=-math.sin(ang),math.cos(ang)      # left normal = outward for clockwise ring
        p8=Point(mx+nx*6,my+ny*6)
        if poly.contains(p8): nx,ny=-nx,-ny;p8=Point(mx+nx*6,my+ny*6)
        if inparcel(p8,i): kind='lot'
        elif inparcel(Point(mx+nx*26,my+ny*26),i): kind='alley'
        else: kind='street'
        out.append(dict(a=a,b=b,L=L,ang=ang,n=(nx,ny),kind=kind))
    # merge consecutive same-kind, near-collinear
    m=[]
    for s in out:
        if m and m[-1]['kind']==s['kind'] and abs(math.remainder(s['ang']-m[-1]['ang'],2*math.pi))<math.radians(25):
            m[-1]['L']+=s['L'];m[-1]['pts'].append(s['b'])
        else: m.append(dict(kind=s['kind'],L=s['L'],ang=s['ang'],n=s['n'],pts=[s['a'],s['b']]))
    if len(m)>1 and m[0]['kind']==m[-1]['kind'] and abs(math.remainder(m[0]['ang']-m[-1]['ang'],2*math.pi))<math.radians(25):
        m[0]['L']+=m[-1]['L'];m[0]['pts']=m[-1]['pts']+m[0]['pts'][1:];m.pop()
    res=[]
    for s in m:
        if s['kind']=='lot' or s['L']<12: continue
        line=LineString(s['pts'])
        if s['kind']=='alley': res.append(dict(name='Alley',len=round(s['L'],1),kind='alley'));continue
        # street name: nearest centerline roughly parallel, within 70 ft
        best=None;mid=line.interpolate(0.5,normalized=True)
        for strict in (True,False):
            for j in stree.query(line.buffer(120)):
                d=sl[j].distance(line)
                if d>(75 if strict else 120): continue
                c=sl[j].coords;ia=math.atan2(c[-1][1]-c[0][1],c[-1][0]-c[0][0])
                if strict and abs(math.remainder(ia-s['ang'],math.pi))>math.radians(35): continue
                q=sl[j].interpolate(sl[j].project(mid))
                if (q.x-mid.x)*s['n'][0]+(q.y-mid.y)*s['n'][1] < 0: continue
                if not strict and (sa[j]['Name'] or '~') in addr: d=d-100
                if best is None or d<best[0]: best=(d,sa[j],sl[j].distance(line))
            if best or s['L']>60: break
        T=max(12,min(70,best[2]-4)) if best else 22
        strip=line.buffer(T)
        cov=0;inc=False;idx=wtree.query(strip)
        if len(idx):
            near=unary_union([wl[k] for k in idx]).intersection(strip)
            if not near.is_empty:
                cov=min(1,line.intersection(near.buffer(T+1)).length/line.length)
                inc=any(winc[k] and wl[k].intersection(strip).length>0.3*line.length for k in idx)
        if best:
            a=best[1];cls='arterial' if a['ST_Class'] in (2,6,10) else 'local'
            res.append(dict(name=(a['Name'] or 'Unnamed street').title(),len=round(s['L'],1),kind='street',cls=cls,walk=cov>=0.5,inc=inc,cov=round(cov,2),paved=True,line=line))
        else:
            res.append(dict(name='Unmapped right-of-way',len=round(s['L'],1),kind='street',cls='local',walk=cov>=0.5,inc=inc,cov=round(cov,2),paved=False,line=line))
    return res
if __name__=='__main__':
    for i,a in enumerate(attrs):
        ad=a['Site_Address'] or ''
        if ad in ('3605 MILL AVE','2725 PEABODY ST','2730 PEABODY ST','2701 PEABODY ST'): print(ad,round(polys[i].area),analyze(i))
    # corner Peabody/W Maryland: parcels within 120 ft north of 2725 Peabody on same side
    ref=[polys[i] for i,a in enumerate(attrs) if a['Site_Address']=='2725 PEABODY ST'][0]
    for j in ptree.query(ref.buffer(130)):
        if polys[j].centroid.y>ref.centroid.y+20 and abs(polys[j].centroid.x-ref.centroid.x)<80: print('N of 2725:',attrs[j]['Site_Address'],round(polys[j].area),analyze(j))

BYNAME={}
for _j,_a in enumerate(sa): BYNAME.setdefault((_a['Name'] or '').upper(),[]).append(_j)
def walkcov(line,T):
    cov=0;inc=False;idx=wtree.query(line.buffer(T))
    if len(idx):
        strip=line.buffer(T);near=unary_union([wl[k] for k in idx]).intersection(strip)
        if not near.is_empty:
            cov=min(1,line.intersection(near.buffer(T+1)).length/line.length)
            inc=any(winc[k] and wl[k].intersection(strip).length>0.3*line.length for k in idx)
    return cov,inc
def addr_fix(i,res,ad):
    """If the address street is missing, add the parcel edges that face its centerline (within 45 ft, roughly parallel)."""
    st=' '.join(ad.split()[1:]).upper()
    if any(r['kind']=='street' and (r['name'].upper()==st or st in r['name'].upper() or r['name'].upper() in st) for r in res): return res,None
    js=BYNAME.get(st,[])
    if not js: return res,None
    poly=polys[i];segs=[]
    for a,b,L,ang in sides(poly):
        seg=LineString([a,b]);mid=seg.interpolate(0.5,normalized=True)
        for j in js:
            if sl[j].distance(mid)>45: continue
            c=sl[j].coords;q=sl[j].interpolate(sl[j].project(mid))
            # local direction of centerline near q
            t=sl[j].project(q);p1=sl[j].interpolate(max(0,t-5));p2=sl[j].interpolate(min(sl[j].length,t+5))
            ia=math.atan2(p2.y-p1.y,p2.x-p1.x)
            if abs(math.remainder(ia-ang,math.pi))>math.radians(35): continue
            # the centerline must lie outside the parcel on this side
            if poly.contains(q): continue
            segs.append((seg,j));break
    if not segs: return res,None
    line=unary_union([g for g,_ in segs]);L=line.length
    if L<12: return res,None
    # drop any existing frontage that overlaps these edges (it was mis-named)
    keep=[]
    for r in res:
        if r['kind']=='street' and r.get('line') is not None:
            ov=r['line'].intersection(line.buffer(2)).length
            if ov>0:
                r=dict(r);r['len']=round(r['len']-ov,1)
                if r['len']<12: continue
        keep.append(r)
    a=sa[segs[0][1]];cls='arterial' if a['ST_Class'] in (2,6,10) else 'local'
    cov,inc=walkcov(line,22)
    keep.append(dict(name=(a['Name'] or st).title(),len=round(L,1),kind='street',cls=cls,walk=cov>=0.5,inc=inc,cov=round(cov,2),paved=True,line=line,fixed=True))
    return keep,True
