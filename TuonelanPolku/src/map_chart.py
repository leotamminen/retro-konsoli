"""Explored-cell map: unseen realm is neither drawn nor implied. Small area surfaces not full map."""
def explored_region_map(s):
    if getattr(s,'mapimg',None):return
    rows=[]
    for nm,a,b in AREAS:
        if nm in ('ranta','syvanne','katedraali') and (not s.save or not s.save.get('vellamo_unlocked') or not s.save.get('vellamo_visited')):continue
        base,top={'forest':((70,80,62),(110,150,80)),'swamp':((70,78,56),(140,160,80)),'river':((84,84,120),(150,190,220)),'pohjola':((36,40,57),(83,105,150)),'ranta':((15,47,47),(67,135,112)),'syvanne':((15,29,59),(66,105,164)),'katedraali':((20,41,32),(98,134,112))}[nm]
        surf=pygame.Surface(((b-a)*2,ROWS));surf.fill((14,12,20));sil=pygame.Surface(surf.get_size());sil.fill((14,12,20))
        for tx in range(a,b):
            for ty in range(ROWS):
                v=GRID[ty][tx];x=(tx-a)*2
                if v==SOLID:surf.fill(top if GRID[ty-1][tx]!=SOLID else base,(x,ty,2,1));sil.fill((34,32,42),(x,ty,2,1))
                elif v==PLAT:surf.fill((150,110,70),(x,ty,2,1))
                elif v==WATER:surf.fill((50,90,170),(x,ty,2,1));sil.fill((28,30,46),(x,ty,2,1))
                elif v==THORN:surf.fill((180,60,70),(x,ty,2,1))
                elif v==LADDER:surf.fill((170,120,70),(x,ty,2,1))
        rows.append((nm,a,b,surf,sil))
    s.mapimg=rows
