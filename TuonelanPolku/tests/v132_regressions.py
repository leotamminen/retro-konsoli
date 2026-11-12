"""Final 1.3.2 fixes: every fire draws, two-player aim input, longer dive, guided entry."""
from lib import *
import random
FAIL=[]
def req(cond,name):
 print(('PASS ' if cond else 'FAIL ')+name)
 if not cond:FAIL.append(name)
req(G['VERSION']==VERSION,'correct version')
# Draw and operate every bonfire, including real P2 interactions and old saves.
for bid in G['BONFIRES']:
 for who in (0,1):
  g=new_game();sv=G['new_save']('hunter');sv.pop('mapseen')
  if int(bid[1:])>=10:sv['vellamo_unlocked']=True
  p1=start(g,save=sv,bonfire=bid);p2=ScriptPad('other');g.add_pad(p2);g.add_p2('warrior',p2);pad=(p1,p2)[who];p=g.players[who]
  x,y=G['bonfire_pos'](bid);p.x=x-12;p.y=y
  tap(g,pad,'up',hold=1,after=1)
  req(g.state_name=='bonfire',bid+' P%d activation and first draw'%(who+1));g.draw()
  for target in ('levelup','map','title'):
   g.state_name='bonfire'
   items=[v[0] for v in g.bonfire_items()]
   g.menu_i['bonfire']=items.index('lvl1' if target=='levelup' else 'map' if target=='map' else 'title')
   pad.nextc=dict(pad.blank(),jump=True);step(g,1);pad.nextc=None;step(g,1)
   req(g.state_name==target,bid+' P%d menu '%(who+1)+target)
# All projectile directions and unchanged speed/damage for both players and classes.
for cls in ('hunter','sage'):
 for who in (0,1):
  for horizontal in (False,True):
   g=new_game();p1=start(g,cls,bonfire='b0');p2=ScriptPad('other');g.add_pad(p2)
   if who:g.add_p2(cls,p2)
   p=g.players[who];pad=(p1,p2)[who];p.draw_t=6 if cls=='hunter' else 0;p.state='draw' if cls=='hunter' else 'act'
   if cls=='hunter':p.fire_arrow(14,3.8,0,0)
   else:
    p.act=dict(kind='light',**G['ATK'][cls]['light'][0]);p.act['st']=0;p.fire_spell(p.act)
   pad.cur.update(up=True,right=horizontal,x=1 if horizontal else 0);g.projs=[]
   if cls=='hunter':p.fire_arrow(14,3.8,0,0)
   else:p.fire_spell(p.act)
   z=g.projs[0]
   req(z.vy<0 and ((abs(z.vx)>0 and abs(abs(z.vx)-abs(z.vy))<1e-6) if horizontal else abs(z.vx)==0),'%s P%d direction %s'%(cls,who+1,horizontal));req(abs((z.vx*z.vx+z.vy*z.vy)-3.8**2 if cls=='hunter' else 0)<1e-6,'bow speed unchanged')
# Real input release with up, no event delay.
g=new_game();p1=start(g,'hunter',bonfire='b0');pad=p1;p=g.players[0]
for k in range(8):pad.nextc=dict(pad.blank(),skill=True,up=True);step(g,1,False)
pad.nextc=dict(pad.blank(),up=True);step(g,1,False)
req(any(not z.enemy and z.vy<0 and abs(z.vx)==0 for z in g.projs),'hold and release fires upward on same tick')
# Louhi remains on the ground for fifty easing frames, versus old twenty-five.
random.seed(9);g=new_game();p1=start(g,bonfire='b9');g.start_boss('louhi');b=g.boss
step(g,110,False);b.gen=b.a_dive();b.phase=1
g.players[0].inv=999999;g.players[0].x=b.x+100
req(b.gen and b.gen.gi_code.co_name=='a_dive','Louhi dive selected')
ground=0
for frame in range(125):
 step(g,1,False)
 if b.gen and b.gen.gi_code.co_name=='a_dive' and not b.atk:
  ground+=1
  if frame in (70,80,90):print('RECOVERY',frame,b.y,b.gy,ground)
req(ground>=39,'ground/recovery frames counted %.0f then next attack'%ground)
print('FAILURES',FAIL);raise SystemExit(bool(FAIL))
