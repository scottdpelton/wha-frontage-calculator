import json,urllib.request,urllib.parse
from concurrent.futures import ThreadPoolExecutor
u="https://maps.cob.org/arcgis4/rest/services/Maps/ReportLayers/MapServer/2/query"
def q(**p):
    p=dict(p,f='json')
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,data=urllib.parse.urlencode(p).encode()),timeout=120))
        except Exception as e: err=e
    raise err
P=json.load(open('parcels.json'));xs=[];ys=[]
for f in P:
    g=f.get('geometry')
    if g:
        for r in g['rings']:
            for x,y in r: xs.append(x);ys.append(y)
xs.sort();ys.sort();n=len(xs)
env=json.dumps({'xmin':xs[int(n*.001)]-500,'ymin':ys[int(n*.001)]-500,'xmax':xs[int(n*.999)]+500,'ymax':ys[int(n*.999)]+500,'spatialReference':{'wkid':2285}})
base=dict(where='1=1',geometry=env,geometryType='esriGeometryEnvelope',inSR=2285,spatialRel='esriSpatialRelIntersects')
ids=q(returnIdsOnly='true',**base)['objectIds'];print(len(ids))
def one(ch):
    r=q(objectIds=','.join(map(str,ch)),outFields='OBJECTID,Site_Address,Site_City,Land_Use_Code,Mapped_Area',returnGeometry='true',outSR=2285,maxAllowableOffset=1)
    return r.get('features',[])
chunks=[ids[i:i+400] for i in range(0,len(ids),400)]
with ThreadPoolExecutor(6) as ex: res=list(ex.map(one,chunks))
F=[f for r in res for f in r];json.dump(F,open('allparcels.json','w'));print(len(F))
