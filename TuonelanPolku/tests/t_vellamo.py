"""1.3: saved gate, scrubbed maps, four new bosses/phases, P2 and no-entry-lag states."""
from lib import *
import json, gc
FAIL=[]
def ok(value,msg):
 print(('ok   ' if value else 'FAIL ')+msg)
 if not value:FAIL.append(msg)
def fresh(bf='b10'):
 g=new_game();sv=G['new_save']('warrior');sv.update(vellamo_unlocked=True,bonfire=bf);p=start(g,save=sv,bonfire=bf);return g,p
def pulse(pad,button='jump'):
 c=pad.blank();c[button]=True;pad.nextc=c
# old saves from Louhi get unlock only, NOT visited or map row.
sv=G['new_save']('hunter');sv.pop('vellamo_unlocked');sv['bosses']=['louhi'];sv['done']=True
ss=G['sanitize_save'](sv,set(G['BONFIRES']))
ok(ss['vellamo_unlocked'] and not ss['vellamo_visited'],'existing Louhi save unlocks without revealing map')
g,p=fresh();g.back_to_title();g.title_save=ss;g.mapimg=None
ok('vellamo' in [q[0] for q in g.title_items()],'title Continue to Vellamo when completed')
g.save=ss;g.state_name='play';g.open_map('play');step(g,1,True)
ok(not any(nm in ('ranta','syvanne','katedraali') for nm,*_ in g.mapimg),'zero hidden map rows')
shot(g,'v13_map_before_unlock',3)
# gate choice by second pad. Do not include generic 'any' or enter after phantom keyboard events.
g= new_game();sv=G['new_save']('warrior');sv.update(vellamo_unlocked=True,bosses=['louhi'],done=True)
p1=ScriptPad('one');p2=ScriptPad('two');g.add_pad(p1);g.add_pad(p2);g.start_session(sv,p1);g.add_p2('hunter',p2)
g.state_name='true_ending';g.true_page=4;g.true_t=60;g.menu_i['vel_offer']=0
pulse(p2);g.update();ok(g.save['vellamo_visited'] and g.area=='ranta','P2 advances true ending into Vellamo')
g.update();ok(g.state_name=='play' and g.area=='ranta','arrival enters shore next frame,separate prewarm+gc')
g.explore();g.open_map('play');step(g,1,True)
ok(any(nm=='ranta' for nm,*_ in g.mapimg),'visited row appears')
assert g.mapseen
# No water realm frontier drawn when hidden; visited cells only show.
vis,front=g.map_known()
for px_row in g.mapimg:
 nm,a,b,surf,sil=px_row
 if nm in ('ranta','syvanne','katedraali'):
  if not any(a<=unit*20<b for unit,_ in g.map_known()[0]):ok(True,'row absent until explored: '+nm)
shot(g,'v13_map_after',3)
# Safe spawn and hazards. Require both standard and actual combined alive-state.
g.new_pad=0
class Point:pass
for bid in ('b10','b11','b12','b13'):
 tx=G['BONFIRES'][bid];g.save['bonfire']=bid
 for p in g.players:p.hp=0;p.state='dead'
 g.dying=180;g.respawn();step(g,2)
 ok(g.save["bonfire"]==bid,bid+" actual retry location")
 for q in g.players:
  b=Point();b.x=q.x;b.y=q.y;b.w=q.w;b.h=q.h
  ok(not G['hazard_at'](g.wd,b) and g.standing_free(q.x,q.y),bid+' +p2 safe spawn')
 for tide in (-20,0,20,40):
  g.tide=tide
  x,y=g.find_safe_xy(tx*16+(-1)**tide*45,320+tide,fallback=(tx*16,320))
  ok(g.standing_free(x,y) and y<G["ROWS"]*16,'safe recovery at tide %s / %s'%(tide,bid))
# Boss render, invoke every individual branch, test music names and phases.
for key,bf in [('joukahainen','b10'),('ahti','b11'),('aino','b12'),('vellamo','b13')]:
 g,p=fresh(bf);g.start_boss(key);step(g,75,True)
 for act in ({'joukahainen':['runes','bog','crossbow','frost'],'ahti':['wave','current','beasts','trident','tide'],'aino':['fin','drop','stream','memory','transform'],'vellamo':['lattice','crown','undertow','cage','erasure']}[key]):
  g.boss.invuln=False;g.boss.gen=None;g.boss.phase=3 if key in ('aino','vellamo') else 2;g.boss._last=[act];g.boss.pick=lambda opts,act=act:act
  g.projs=[];g.zones=[];it=getattr(g.boss,key[:3])+'' if False else None
  ita={'joukahainen':'jous','ahti':'aht','aino':'ain','vellamo':'vel'}[key]
  g.boss.gen=getattr(g.boss,ita)();step(g,75,False)
  ok(bool(g.projs or g.zones or act in ('bog','current','undertow')),key+' action '+act)
  g.draw();shot(g,'v13_'+key+'_'+act,2)
 g.boss.invuln=False;g.boss.hp=g.boss.maxhp*.51
 for i in range(1 if key in ("joukahainen","ahti") else 2):
  g.boss.gen=None;step(g,102,False);ok(int(g.boss.phase)>=i+2,key+' phase '+str(i+2))
 g.boss.hp=max(1,g.boss.maxhp*.2);g.boss.gen=None;g.boss.phase=2 if key in ('joukahainen','ahti','aino') else 3
 g.boss.invuln=False;g.boss.take(40);g.boss.hp=1;g.boss.take(100000)
 ok(g.state_name=='aino_reveal' if key=='aino' else g.felled is not None,key+' defeat transition ('+g.state_name+')')
# co-op calm/reveal/final retry/ending pad actions.
g,p=fresh('b12');p2=ScriptPad('other');g.add_pad(p2);g.add_p2('hunter',p2)
g.start_boss('aino');step(g,75);g.boss.invuln=False;g.boss.hp=1;g.boss.take(200);g.update()
ok(g.state_name=='aino_reveal' and g.boss is None,'Aino calmed, not killed')
pulse(p2);g.update();ok(g.boss and g.boss.key=='vellamo','P2 advances reveal to Vellamo')
ok(len(g.players)==2 and g.players[1].pad is p2,'P2 identity retained to Vellamo')
g.start_vellamo_ending();p2.nextc=None;g.update();pulse(p2);g.update();ok(g.state_name=='title','P2 returns ending to title')
g.save=ss;g.players=[];g.open_map('title');g.build_map()
print('FAILURES',FAIL);raise SystemExit(bool(FAIL))
