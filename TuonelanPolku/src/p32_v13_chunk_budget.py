"""Spread terrain decoding outside budgets, prewarm short known-looking transitions."""
Root_chunk=GameCore.chunk
def budget_chunk(s,c):
    # A chunk is garbage only if camera hydration rev's the tilemap - cache same revision.
    return Root_chunk(s,c)
def warm_chunks(s):
    if s.frames%4:return
    if getattr(s,'chunk_frame',-1)==s.frames:return
    center=int(s.cam[0])//320
    for cc in sorted(range(max(0,center-3),min((COLS-1)//20,center+4)+1),key=lambda c:abs(c-center)):
        if (cc,GameCore.CHUNK_REV[0]) not in GameCore.CHUNK_CACHE:
            s.chunk_frame=s.frames;Root_chunk(s,cc);return
GameCore.warm_chunks=warm_chunks
_root_warm_all=GameCore.warm_all
def warm_all(s):
    center=int(s.cam[0])//320
    for cc in range(max(0,center-1),min((COLS-1)//20,center+1)+1):Root_chunk(s,cc)
GameCore.warm_all=warm_all
_pre_start=GameCore.start_boss
def prewarm_intro(s,key):
    a=ARENAS[key];center=(a['x0']-1)*16//320
    # one near-left/current/right, never full map / every-attack generation
    for ci in (center-1,center,center+1):
        if 0<=ci<((COLS-1)//20+1):Root_chunk(s,ci)
    return _pre_start(s,key)
GameCore.start_boss=prewarm_intro
