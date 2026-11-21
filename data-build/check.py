"""Sanity checks before a refreshed lots.json replaces the live one. Exit 1 on failure."""
import json,sys
new=json.load(open('lots3.json')); old=json.load(open(sys.argv[1]))
n,o=len(new['lots']),len(old['lots'])
L={x[0]:x for x in new['lots']}
fails=[]
if abs(n-o)/o>0.05: fails.append(f'lot count moved more than 5%: {o} -> {n}')
for a in ['3605 MILL AVE','3015 PEABODY ST','2855 CORNWALL AVE','PARCEL 380319019221']:
    if a not in L: fails.append('missing '+a)
if L.get('3605 MILL AVE') and len(L['3605 MILL AVE'][3])!=3: fails.append('3605 Mill Ave frontage count changed')
print('lots',o,'->',n); print('\n'.join(fails) or 'checks passed'); sys.exit(1 if fails else 0)
