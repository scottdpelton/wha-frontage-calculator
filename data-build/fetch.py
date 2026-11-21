import json,urllib.request,urllib.parse,sys
from concurrent.futures import ThreadPoolExecutor
b="https://maps.cob.org/arcgis4/rest/services"
def q(u,**p):
    p=dict(p,f='json')
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,data=urllib.parse.urlencode(p).encode()),timeout=120))
        except Exception as e: err=e
    raise err
def pull(u,fields,where,page,out,sr=2285,off=2,n=None):
    cnt=q(u+"/query",where=where,returnCountOnly='true')['count']
    def one(o):
        r=q(u+"/query",where=where,outFields=fields,returnGeometry='true',outSR=sr,maxAllowableOffset=off,resultOffset=o,resultRecordCount=page,orderByFields='OBJECTID')
        return r.get('features',[]) if 'features' in r else (print('ERR',o,r.get('error')) or [])
    with ThreadPoolExecutor(6) as ex: res=list(ex.map(one,range(0,cnt,page)))
    feats=[f for r in res for f in r]; json.dump(feats,open(out,'w')); print(out,cnt,len(feats))
if __name__=="__main__":
  pull(b+"/Maps/ReportLayers/MapServer/2","OBJECTID,PARCEL_CODE,Land_Use_Code,Land_Use_Description,Site_Address,legal_acreage,Mapped_Area","Site_City='BELLINGHAM'",1000,'parcels.json')
  pull(b+"/Maps/Grp_Transportation/MapServer/16","OBJECTID,STREETNAME,STREETSIDE,INCOMPLETE,WIDTH,FeatureLengthFeet,TRAIL","1=1",1000,'walks.json')
  pull(b+"/Maps/Grp_Transportation/MapServer/34","OBJECTID,Name,ST_Class,Jurisdiction,HWY_Number","1=1",1000,'streets.json')
  pull(b+"/maps_StatePlane/Grp_Planning_StatePlane/MapServer/8","ZONING_DESIGNATION,GENERAL_USE_TYPE,NEIGHBORHOOD_NAME","1=1",200,'zoning.json',off=5)
