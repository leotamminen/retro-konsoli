"""Localized Ahti tide with real lift/pull. Base move_body and World remain byte-equivalent."""
Classic_phys=Player.phys
def tide_phys(p,fric=.82,grav=True):
    if isinstance(p,Player) and isinstance(p.g,GameCore) and p.g.arena=='ahti':
        water=228-p.g.tide
        p.in_water=p.y-PH_>water
        if p.in_water:
            # shallow tide has mild horizontal wave motion, increased buoyancy in phase 2
            p.vy=min(2.8,p.vy-.045);p.vx+=math.sin(p.g.frames*.04)*.025
            if p.vy<0:p.vy*=.94
    else:p.in_water=False
    return Classic_phys(p,fric,grav)
Player.phys=tide_phys
def water_level(g):return 228-g.tide if g.arena=='ahti' else 0
GameCore.water_level=water_level
# New realm water is traversable water; base-game water/insta-kill hazard stays unchanged.
_Legacy_hazard_at=hazard_at
def hazard_region(wd,b):
    if b.x>=486*TILE and wd.tile(int(b.x//TILE),19)==WATER:return False
    return _Legacy_hazard_at(wd,b)
hazard_at=hazard_region
# Sanitization stays explicit and backwards compatible; do not preserve a victory in a defeated boss.
Save_sanitize=sanitize_save
def sanitize_v13(d,valid_bonfires=None,valid_ids=None):
    sv=Save_sanitize(d,valid_bonfires,valid_ids)
    if sv is None:return None
    # These fields may have appeared in experiments but have no active semantics.
    sv.pop('vellamo_clear',None)
    return sv
sanitize_save=sanitize_v13
