from fetch import q,pull,b
M=b+"/Maps/"
pull(M+"Grp_Transportation/MapServer/21","OBJECTID,TYPE,SURFACETYPE","1=1",1000,'pave.json',off=1)
pull(M+"Grp_Utilities/MapServer/5","OBJECTID","1=1",2000,'cb.json',off=0)
pull(M+"Grp_Utilities/MapServer/12","OBJECTID,DIAMETER","1=1",2000,'smain.json',off=2)
pull(M+"Grp_Utilities/MapServer/56","OBJECTID,Owner","1=1",2000,'lights.json',off=0)
pull(M+"Grp_Transportation/MapServer/25","OBJECTID,Recommendation,Status,Score,Tier","1=1",1000,'pmp.json',off=2)
pull(M+"Grp_Transportation/MapServer/38","OBJECTID,SURFACETYPE,WIDTH","1=1",1000,'alleys.json',off=2)
import json
r=q(M+"ReportLayers/MapServer/2/query",where="Site_Address IS NULL",outFields="OBJECTID,PARCEL_CODE",returnGeometry='false',resultRecordCount=50000)
json.dump([f['attributes'] for f in r.get('features',[])],open('pcodes.json','w')); print('pcodes',len(r.get('features',[])),r.get('exceededTransferLimit'))
