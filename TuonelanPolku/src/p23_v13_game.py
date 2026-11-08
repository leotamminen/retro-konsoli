"""Vellamo world, UI and saved continuation. Only the new columns change legacy hazard rules."""
import gc
VERSION='1.3.2'
_spawn=GameCore.spawn_enemies
def spawn_enemies(s):
    _spawn(s)
GameCore.spawn_enemies=spawn_enemies
_session=GameCore.start_session
def start_session(s,save,pad):
    _session(s,save,pad)
    if save and "louhi" in save.get("bosses", []):s.wd.set_open('d_vellamo',True)
    s.aino_glimpse=None;s.tide=0;s.vel_end_t=0;s.current=0
GameCore.start_session=start_session
_arena=GameCore.update_arena;_area=GameCore.update_area;_world=GameCore.draw_world
_old_boss=GameCore.start_boss;_dead=GameCore.on_boss_dead
class _V:
    def update_arena(s):
        _arena(s)
        if isinstance(s.boss,WaterBoss):
            k=s.boss.key;ph=s.boss.phase
            suffix='3' if ph>=3 else '2' if ph>=1.5 else ''
            MUSIC.request(k+suffix if k+suffix in TRACK_ORDER else k)
            if k=='ahti':s.tide=int(math.sin(s.frames*.015)*10)+(22 if ph>=2 else 0)
    def update_area(s):
        _area(s)
        if s.area not in ('ranta','syvanne','katedraali'):return
        tx=int(s.players[0].x//TILE);s.save['vellamo_visited']=True
        if not s.aino_glimpse and not s.boss:
            if 493<=tx<499:s.aino_glimpse=(510*TILE,0.)
            elif 548<=tx<554:s.aino_glimpse=(562*TILE,0.)
            elif 602<=tx<609:s.aino_glimpse=(615*TILE,0.)
        if s.aino_glimpse:
            x,t=s.aino_glimpse
            if t>28:x+=1.5
            s.aino_glimpse=(x,t+1) if t<150 else None
        if s.boss and s.boss.key=='vellamo' and s.boss.dead:s.vel_end_t+=1
        if s.vel_end_t>130:s.start_vellamo_ending()
    def draw_world(s,c,t):
        _world(s,c,t)
        if s.aino_glimpse:
            x=s.aino_glimpse[0]-s.cam[0];aino_glimpse(c,int(x),t)
        if s.area in ('ranta','syvanne','katedraali'):
            for x in (-12,77,198,281):
                y=124+int(math.sin(x*.07+t*.04)*3)+s.tide//2
                pygame.draw.arc(c,(65,127,146),(x,y,18,6),.15,2.9,1)
    def start_boss(s,key):
        _old_boss(s,key)
        if key in ('joukahainen','ahti','aino','vellamo'):
            for p in s.players:p.inv=180
    def on_dead(s,b):
        k=b.key
        if k in ('joukahainen','ahti'):
            if k not in s.save['bosses']:s.save['bosses'].append(k)
            s.wd.set_open('d_'+k+'_in',True);s.felled=(k,0)
            s.save['bonfire']='b11' if k=='joukahainen' else 'b12';s.save_game();return
        _dead(s,b)
        if k=='vellamo':s.save['aino_freed']=True;s.save['vellamo_done']=True;s.save['ng_ready']=True;s.save_game();s.vel_end_t=1
    def enter(s):
        sv=s.save;sv['vellamo_unlocked']=True;sv['vellamo_visited']=True;sv['bonfire']='b10'
        if 'b10' not in sv['seen']:sv['seen'].append('b10')
        s.save_game();s.poht_t=0
        s.mapimg = None
        s.start_session(sv,s.p_pad[0] if s.p_pad[0] else s.kb)
        s.state_name='vellamo_arrival'
        MUSIC.request('ranta');s.prewarm_vellamo()
    def prewarm(s):
        for ar in ('ranta','syvanne','katedraali'):sky_surface(ar);layers_for(ar);fog_surface(ar)
        for ph in (1,2,3):
            for k in ('joukahainen','ahti','aino','vellamo'):
                for po in ('idle','windup','attack','roar','fish','maiden','reveal'):newboss_frame(k,po,ph,0)
        for ch in range(24,28):s.chunk(ch)
    def reveal(s):
        s.reset_boss();s.state_name='aino_reveal';s.reveal_t=0
        for p in s.players:p.spawn((646+p.idx*6)*TILE,320);p.refill();p.inv=180
        s.save['bonfire']='b13'
        if 'b13' not in s.save['seen']:s.save['seen'].append('b13')
        s.save_game();gc.collect()
for k,v in [('update_arena',_V.update_arena),('update_area',_V.update_area),('draw_world',_V.draw_world),('start_boss',_V.start_boss),('on_boss_dead',_V.on_dead),('enter_vellamo',_V.enter),('prewarm_vellamo',_V.prewarm),('start_aino_reveal',_V.reveal)]:setattr(GameCore,k,v)
def _finish_vellamo(s):
    gc.collect();s.state_name='vellamo_ending';s.vel_end_t=0;s.save['vellamo_done']=True;s.save_game()
GameCore.start_vellamo_ending=_finish_vellamo
# Only supplement terrain rendering: returned cached strip remains the exact no-area surface.
mob_brain=Mob.brain
def _mb(s):
    if s.kind not in ('poltto','merikala','kutri','lampi','rapu'):return mob_brain(s)
    return aquatic_brain(s)
Mob.brain=_mb
_edraw=Enemy.draw
def _enemy_draw(s,surf,cx,cy):
    if not isinstance(s,WaterBoss):return _edraw(s,surf,cx,cy)
    spr=newboss_frame(s.key,getattr(s,'vb','idle'),max(1,min(3,round(s.phase))),s.t)
    if s.face>0:
        fk=('flip',s.key,getattr(s,'vb','idle'),max(1,min(3,round(s.phase))),s.t%4)
        if fk not in _BSPR:_BSPR[fk]=pygame.transform.flip(spr,True,False)
        spr=_BSPR[fk]
    px=int(s.x-cx-spr.get_width()//2);py=int(s.y-cy-spr.get_height())
    surf.blit(spr,(px,py));

Enemy.draw=_enemy_draw
def _mob_draw(s,surf,cx,cy):
    if s.kind not in ('poltto','merikala','kutri','lampi','rapu'):return enemy_draw(s,surf,cx,cy)
    x=int(s.x-cx);y=int(s.y-s.h/2-cy)
    if s.kind=='lampi':
        pygame.draw.circle(surf,(186,236,210),(x,y),6);pygame.draw.circle(surf,(255,255,220),(x,y-1),2)
        pygame.draw.line(surf,(120,190,170),(x,y+4),(x,y+12),1)
    elif s.kind=='rapu':
        pygame.draw.ellipse(surf,(168,92,64),(x-10,y-6,20,10))
        pygame.draw.line(surf,(120,60,40),(x-8,y),(x-14,y-6),2);pygame.draw.line(surf,(120,60,40),(x+8,y),(x+14,y-6),2)
        pygame.draw.circle(surf,(40,24,16),(x-3,y-2),1);pygame.draw.circle(surf,(40,24,16),(x+3,y-2),1)
    elif s.kind=='poltto':
        pygame.draw.circle(surf,(34,108,121),(x,y),8);pygame.draw.circle(surf,(113,216,183),(x,y),5)
        for i in range(5):pygame.draw.line(surf,(22,90,120),(x-8+i*4,y),(x-8+i*4,y-10),2)
    elif s.kind=='merikala':
        pygame.draw.ellipse(surf,(41,141,164),(x-14,y-8,25,16));pygame.draw.polygon(surf,(96,186,169),[(x-10,y),(x-25,y-8),(x-25,y+8)]);pygame.draw.circle(surf,(211,232,179),(x+7,y-2),2)
    else:
        pygame.draw.arc(surf,(146,171,219),(x-9,y-10,18,34),0,6.28,2)
        for i in range(3):pygame.draw.line(surf,(68,141,138),(x-7+i*7,y),(x-11+i*7,y+14),1)
enemy_draw=Mob.draw
Mob.draw=_mob_draw
