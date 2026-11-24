# Parcel data build

`refresh.sh` rebuilds `../lots.json` (the address list behind the calculator) from the City of Bellingham's public GIS at maps.cob.org: parcels, sidewalks, street centerlines (with the curb types from the City's 2024-25 street survey), street pavement, curb ramps, storm mains, street lights, alleys and the Pedestrian Master Plan. `check.py` blocks the update if the lot count moves more than 5% or the documented cases go missing. Raw downloads (*.json here) are not committed.


Curb codes per frontage (field 6): 0 no City record, 1 curb and gutter, 2 curb without gutter, 3 thickened edge, 4 no curb. 10+ means the block has two curb types; the better one is assigned to the side with mapped sidewalk. CurbType2 is a secondary type, not the opposite side (downtown Cornwall Ave, curbed on both sides, reads C&G / NONE). Known error: Mill Ave at 36th St reads NONE (May 2025) but the 2022 aerial shows new curb and sidewalk.
