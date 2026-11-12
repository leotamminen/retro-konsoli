from lib import *
import json
SETTINGS['lang']='fi'
ARENAS=G['ARENAS'];manifest=[]
def get(bf,key=None,cls='warrior'):
 g=new_game();sv=G['new_save'](cls);sv.update(vellamo_unlocked=True,vellamo_visited=True,bonfire=bf,done=True,bosses=['louhi'],time=7220,deaths=4,stats={'vit':5,'str':8,'end':3,'foc':0});pad=start(g,cls,save=sv,bonfire=bf);step(g,80,True);g.area_popup=None
 if key:g.start_boss(key);step(g,70,False);g.area_popup=None
 return g,pad
for bf,area in [('b10','ranta'),('b11','syvanne'),('b12','katedraali')]:
 g,p=get(bf);pl=g.players[0];pl.spawn(G['BONFIRES'][bf]*16+70,320);g.snap_cam();g.area_popup=(area,80)
 g.draw();shot(g,'131_'+area,3);manifest.append('131_'+area)
g,p=get('b10');g.players[0].spawn(494*16,320);g.snap_cam();g.aino_glimpse=(508*16,45);g.draw();shot(g,'131_aino_glimpse',3)
for key,bf in [('joukahainen','b10'),('ahti','b11'),('aino','b12'),('vellamo','b13')]:
 g,p=get(bf,key,'hunter');a=ARENAS[key]
 for ph in ({'joukahainen':(1,2),'ahti':(1,2),'aino':(1,2,3),'vellamo':(1,2,3)}[key]):
  b=g.boss;b.phase=ph;b.invuln=False
  b.x=(a['x0']+15)*16;b.y=320
  pose={'joukahainen':('idle','windup'),'ahti':('idle','attack'),'aino':('maiden','fish','fish'),'vellamo':('idle','windup','reveal')}[key][ph-1]
  b.vb=pose;b.x_coralloop=ph
  g.cam=[(a['x0']-1)*16,148];g.area_popup=None
  # Actual generated projectile/zone shapes at attack range to show new motion language.
  if key=='joukahainen':
   for y in (257,281,305):b.shoot('verse',b.x-45,y,-2,0,curve=.006)
  elif key=='ahti':
   for dx in (-30,0,30):b.shoot('swell',b.x+dx,310,0,0)
   g.tide=16 if ph>=2 else 0
  elif key=='aino':
   for y in (241,270,300):b.shoot('bubble',b.x-35,-227+y if False else y,-1,0)
  else:
   for y in (243,262,282,302):b.shoot('memory',b.x-40,y,-2,.001,col=(145,153,219))
   if ph==2:b.g.zones.append(G['Zone'](b.x,320,70,95,20,25,43,'cage',2))
   if ph==3:
    for dx in (-72,72):b.g.zones.append(G['Zone'](b.x+dx,320,18,118,35,20,36,'frost',2))
  b.warn=ph*6;b.warn_t=1
  g.draw();shot(g,'131_%s_phase%d'%(key,ph),3)
# The two boss/maiden forms in reveal are drawn by the narrative UI handler.
g,p=get('b12','aino');g.boss.hp=1;g.boss.invuln=False;g.boss.take(999,pl=g.players[0]);g.reveal_t=95;g.draw();shot(g,'131_vellamo_reveal',3);g.start_vellamo_ending();g.draw();shot(g,'131_vellamo_ending',3)
# Both title/save/stories computed with old-save unlock only and after actual water-arrival.
g,p=get('b9');g.save['vellamo_unlocked']=False;g.save['vellamo_visited']=False;g.save['bosses']=['hiisi','louhi'];g.mapimg=None;g.open_map('play');g.draw();shot(g,'131_map_before_unlock',3)
g.save['vellamo_unlocked']=True;g.enter_vellamo();g.update();g.state_name='play';g.explore();g.open_map('play');g.draw();shot(g,'131_map_after',3)
open('artifacts/screens_manifest131.json','w').write(json.dumps(dict(captures=sorted([f[:-4] for f in os.listdir(os.path.join(ROOT,'screenshots')) if f.startswith('131_') and f.endswith('.png')]),interactive_capture_coordinate_fixture='Boss follows genuine draw state fixture at arena mid to visually inspect each phase, actual boss combat bots separately.',coordinate_size=[320,180]),indent=2))
print('captured curated phase,realm,story,map,ending shots')
