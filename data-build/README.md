# Parcel data build

`refresh.sh` rebuilds `../lots.json` (the address list behind the calculator) from the City of Bellingham's public GIS at maps.cob.org: parcels, sidewalks, street centerlines, street pavement, curb ramps, storm mains, street lights, alleys and the Pedestrian Master Plan. `check.py` blocks the update if the lot count moves more than 5% or the documented cases go missing. Raw downloads (*.json here) are not committed.
