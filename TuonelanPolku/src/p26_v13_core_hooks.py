# Palette entries and small-scoped sprite/glimpse positions.
Fireflies_old=GameCore.draw_light
class Scene13:
    def draw_light(s,c,t,cx,cy,pal):
        # base lookup is old: decorate fireflies after, not allocate a new large surface

        area=s.area
        if area in ('ranta','syvanne','katedraali'):
            fc={'ranta':(99,220,161),'syvanne':(128,200,198),'katedraali':(172,228,198)}[area]
            oldff=s.ffs;s.ffs=[];Fireflies_old(s,c,t,cx,cy,dict(pal,ambient={'ranta':(184,208,214),'syvanne':(187,209,231),'katedraali':(184,214,201)}[area]));s.ffs=oldff
            c.blit(s.dimmer,(0,0)) if False else None
            # Slow short water glints instead of a screen-wide line pattern.
            # Local, sparse low-contrast ripples; never span the whole viewport.
            for i in range(4):
                xx=(i*83+t//17)%317; yy=111+(i*19)%30
                w=5+int(3*math.sin(t*.017+i))
                pygame.draw.arc(c,(30,78,94),(xx,yy,w,5),.4,2.7,1)
            for f in s.ffs[:30]:
                if f[0]>cx-10 and f[0]<cx+330:c.fill(fc,(int(f[0]-cx),int(f[1]-cy),2,2))
        else:Fireflies_old(s,c,t,cx,cy,pal)
GameCore.draw_light=Scene13.draw_light
draw_light=Scene13.draw_light
# update shallow current instead of entering old water hazard damage outside this region
_hazard=GameCore.hazard
def hazard(s,p):
    if p.x>=486*TILE:
        p.vy=min(p.vy,.8);p.spawned=getattr(p,'spawned',False)
        return
    return _hazard(s,p)
GameCore.hazard=hazard
# Each glimpse's x coordinate is absolute: use world columns, not screen columns.
import builtins
# Low-tide water is slowed traversal, never old insta-kill region. Explicit floor spawns only.
