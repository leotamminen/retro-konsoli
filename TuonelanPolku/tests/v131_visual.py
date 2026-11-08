from lib import *
FAIL=[]
def ok(v,s):
 print(('ok   ' if v else 'FAIL ')+s)
 if not v:FAIL.append(s)
for key in ('joukahainen','ahti','aino','vellamo'):
 for pose in ('idle','windup','attack','roar','fish','maiden','reveal'):
  for phase in (1,2,3):
   for t in range(4):
    sp=G['newboss_frame'](key,pose,phase,t)
    ok(sp.get_size()==(192,160),key+' new cached sheet size')
    ok(sp.get_bounding_rect().w>0,key+' visible pixels')
for a in ('ranta','syvanne','katedraali'):
 bg=G['sky_surface'](a)
 ok(bg.get_at((10,5))!=bg.get_at((10,155)),a+' actual cached gradient')
 ok(bg.get_at((10,20))!=(0,0,0,255),a+' water pixels not erased')
 g=new_game();sv=G['new_save']('warrior');sv.update(vellamo_unlocked=True,vellamo_visited=True,bonfire={'ranta':'b10','syvanne':'b11','katedraali':'b12'}[a]);start(g,save=sv)
 panels=[]
 # Two actual area screens using natural update, not arbitrary floor teleports.
 pl=g.players[0];bid={'ranta':'b10','syvanne':'b11','katedraali':'b12'}[a];pl.spawn(G['BONFIRES'][bid]*16+70,320);g.snap_cam();step(g,3)
 g.draw();count=0
 # sample the top sky safely above the on-screen obstacles at every fixture
 for y in (8,16,24):
  for x in (14,72,152,234,298):
   q=g.canvas.get_at((x,y))
   if q[1]>=2 and q[2]>=4:count+=1
 ok(count>=5,a+' gradient visible through cached chunks')
for key in ('boss_joukahainen','boss_aino','vel_offer','vel_ending','area_syvanne'):
 assert G['TR']['fi'][key]
print('failures',len(FAIL));raise SystemExit(bool(FAIL))
