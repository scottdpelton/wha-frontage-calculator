import json,math,collections
import front as F
from shapely.geometry import Point
from shapely.strtree import STRtree
R=json.load(open('ramps.json'))
rp=[Point(f['geometry']['x'],f['geometry']['y']) for f in R]; rd=[f['attributes']['TRUNCATEDDOME']=='Yes' for f in R]
rt=STRtree(rp)
d=json.load(open('lots3.json')); S=d['streets']
idx={}
for i,a in enumerate(F.attrs):
    ad=(a['Site_Address'] or '').strip()
    if ad and ad not in idx: idx[ad]=i
pc={a['OBJECTID']:a['PARCEL_CODE'] for a in json.load(open('pcodes.json'))}
for i,a in enumerate(F.attrs):
    if not a['Site_Address'] and pc.get(a['OBJECTID']): idx.setdefault('PARCEL '+pc[a['OBJECTID']],i)
c=collections.Counter()
for x in d['lots']:
    names={S[f[0]] for f in x[3] if S[f[0]] not in ('Unmapped right-of-way','Alley')}
    code=0
    if len(names)>=2 and x[0] in idx:
        poly=F.polys[idx[x[0]]]
        # corner point: where centerlines of two of the lot's streets meet, nearest the lot
        best=None
        nl=list(names)
        for a in range(len(nl)):
            for b in range(a+1,len(nl)):
                for ja in F.BYNAME.get(nl[a].upper(),[]):
                    if F.sl[ja].distance(poly)>90: continue
                    for jb in F.BYNAME.get(nl[b].upper(),[]):
                        if F.sl[jb].distance(poly)>90: continue
                        g=F.sl[ja].intersection(F.sl[jb])
                        if g.is_empty: 
                            # near-miss intersections
                            if F.sl[ja].distance(F.sl[jb])>15: continue
                            from shapely.ops import nearest_points
                            g=nearest_points(F.sl[ja],F.sl[jb])[0]
                        if g.geom_type!='Point': g=g.centroid if hasattr(g,'centroid') else g
                        dd=g.distance(poly)
                        if dd<120 and (best is None or dd<best[0]): best=(dd,g)
        if best:
            pt=best[1]; near=[k for k in rt.query(pt.buffer(90)) if rp[k].distance(pt)<90 and rp[k].distance(poly)<60]
            code=3 if not near else (1 if all(rd[k] for k in near) else 2)
    c[code]+=1
    x[4]=code
json.dump(d,open('lots3.json','w'),separators=(',',':'))
print(c)
