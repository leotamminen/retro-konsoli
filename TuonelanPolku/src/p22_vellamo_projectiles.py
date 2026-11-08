_v13_init=Proj.__init__
def _v13_init_new(s,*args,curve=0,**kw):_v13_init(s,*args,**kw);s.curve=curve;s.wd=None
Proj.__init__=_v13_init_new
_v13_proj=Proj.update
def _v13_proj_new(s,g):
    s.wd=g.wd
    if s.kind not in ('runic','verse','memory','thornwave','bubble','swell'):_v13_proj(s,g);return
    s.t+=1;s.life-=1
    if s.life<=0:s.dead=True;return
    s.x+=s.vx;s.y+=s.vy;s.vy+=s.curve
    if s.kind=='bubble':s.vy-=.012
    if s.kind not in ('thornwave',) and g.wd.solid(int(s.x//TILE),int(s.y//TILE)):s.dead=True
Proj.update=_v13_proj_new
_v13_pdraw=Proj.draw
def _v13_pdraw_new(s,surf,cx,cy):
    if s.kind not in ('runic','verse','memory','thornwave','bubble','swell'):_v13_pdraw(s,surf,cx,cy);return
    x=int(s.x-cx);y=int(s.y-cy);co=s.col
    if s.kind in ('runic','memory'):pygame.draw.rect(surf,co,(x-2,y-6,4,12),1);pygame.draw.line(surf,co,(x-5,y+3),(x+5,y-3),1)
    elif s.kind=='thornwave':pygame.draw.polygon(surf,co,[(x-4,y+7),(x,y-8),(x+4,y+7)])
    elif s.kind=='bubble':pygame.draw.circle(surf,co,(x,y),6,1);pygame.draw.circle(surf,(223,250,234),(x+2,y-2),1)
    elif s.kind=='verse':
        pygame.draw.arc(surf,co,(x-8,y-10,15,21),-math.pi/2,math.pi,1);pygame.draw.circle(surf,co,(x-4,y+8),3)
    else:pygame.draw.arc(surf,co,(x-13,y-22,27,40),0,math.pi,3);pygame.draw.arc(surf,(173,233,227),(x-6,y-13,13,23),0,math.pi,1)
Proj.draw=_v13_pdraw_new
_v13_zdraw=Zone.draw
def _v13_draw_zone(s,surf,cx,cy):
    if s.style not in ('bog','tentacle','tidepike','cage','frost'):_v13_zdraw(s,surf,cx,cy);return
    x=int(s.x-cx);y=int(s.y-cy);a=125
    if not s.active:
        pygame.draw.line(surf,(170,225,224),(x-int(s.w/2),y),(x+int(s.w/2),y),2);pygame.draw.line(surf,(168,215,200),(x,y-s.h),(x,y-8),1)
    elif s.style=='bog':pygame.draw.ellipse(surf,(18,50,49),(x-20,y-8,40,8));pygame.draw.ellipse(surf,(87,136,109),(x-16,y-5,32,8),1)
    elif s.style=='tentacle':
        for j in range(5):pygame.draw.circle(surf,(30+j*5,104+j*12,93),(x+int(13*math.sin(j*.8+s.t*.05)),y-j*17),15-j*2)
    elif s.style=='tidepike':pygame.draw.polygon(surf,(178,225,213),[(x-11,y),(x,y-110),(x+2,y-67),(x+18,y-60),(x+10,y-80),(x+8,y-53)])
    elif s.style=='cage':
        for dx in range(-35,36,12):pygame.draw.line(surf,(68,179,148),(x+dx,y+2),(x+dx,y-92),3)
        pygame.draw.line(surf,(112,185,165),(x-35,y-92),(x+35,y-92),3)
    else:pygame.draw.polygon(surf,(168,206,226),[(x-11,y),(x-13,y-60),(x,y-96),(x+12,y-25),(x+4,y-40)])
_zone_rect=Zone.rect
Zone.rect=lambda s:((s.x-24,s.y-20,48,5) if s.style=='bog' and s.active else _zone_rect(s))

_old_zone_update=Zone.update
def _v13_zone_update(s,g):
    _old_zone_update(s,g)
    if s.style=='bog' and s.active:
        for p in g.players:
            if abs(p.x-s.x)<24 and abs(p.y-s.y)<32:
                bo=getattr(p,'bog',None)
                if bo!=s:
                    p.bog=s;p.bog_t=90;p.vx=0;p.y=s.y;p.vy=0
                elif p.pad.pressed("jump"):
                    p.bog_t=0;p.bog=None;p.y-=18;p.vy=JUMP_V;p.inv=max(p.inv,80);s.dead=True
                else:
                    p.bog_t-=1
                    if s.t%90==0:p.take_hit(12*D()['dmg'],s.x,0,tags=('magic',))
                    if p.bog_t<=0:p.bog=None;s.dead=True
Zone.update=_v13_zone_update
