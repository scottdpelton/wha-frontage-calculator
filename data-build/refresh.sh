#!/usr/bin/env bash
# Rebuilds ../lots.json from the City of Bellingham's public GIS (maps.cob.org). Needs python3 + shapely.
set -euo pipefail
cd "$(dirname "$0")"
python3 fetch.py        # parcels, sidewalks, street centerlines, zoning
python3 fetchall.py     # all parcel polygons
python3 fetch2.py       # pavement, catch basins, storm mains, street lights, pedestrian plan, alleys, parcel codes
python3 -c "import json,urllib.request,urllib.parse
u='https://maps.cob.org/arcgis4/rest/services/Maps/Grp_Transportation/MapServer/10/query'
q=lambda **p: json.load(urllib.request.urlopen(urllib.request.Request(u,data=urllib.parse.urlencode(dict(p,f='json')).encode()),timeout=120))
ids=q(where='1=1',returnIdsOnly='true')['objectIds'];F=[]
for i in range(0,len(ids),500): F+=q(objectIds=','.join(map(str,ids[i:i+500])),outFields='OBJECTID,TRUNCATEDDOME',returnGeometry='true',outSR=2285)['features']
json.dump(F,open('ramps.json','w'));print('ramps',len(F))"
python3 build3.py
python3 corners.py
python3 check.py ../lots.json
cp lots3.json ../lots.json
echo "lots.json refreshed"
