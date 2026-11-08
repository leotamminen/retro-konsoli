from lib import *
def press(pad,actions):
 pad.nextc=dict(pad.blank(),**actions)
def release(pad):pad.nextc=None;step(g,1,False)
def req(x,msg):
 if not x: raise AssertionError(msg)
g=new_game();sv=G['new_save']('warrior');sv.update(bonfire='b9',done=True,bosses=['louhi']);pad=start(g,save=sv,bonfire='b9');p2=ScriptPad('second');g.add_pad(p2);g.add_p2('hunter',p2)
for state in ('vellamo_arrival','aino_reveal','vellamo_ending'):
 g.state_name=state;g.reveal_t=3;g.vel_end_t=1;g.t_ui=0
 press(p2,{'jump':True});step(g,1,False);req(g.state_name!=' '+state,state+' 0-frame P2 action missing')
 press(p2,{})
 release(p2)
for bf in ('b10','b11','b12','b13'):
 g=new_game();sv=G['new_save']('warrior');sv.update(vellamo_unlocked=True,vellamo_visited=True,bonfire=bf);p1=start(g,save=sv,bonfire=bf);p2=ScriptPad('two');g.add_pad(p2);g.add_p2('hunter',p2)
 for tide in (0,32):
  g.respawn();req(g.save['bonfire']==bf,('actual retry',bf));g.tide=tide;g.arena=None
  for pl in g.players:
   g.update();press(pl.pad,{});g.update();req(pl.state=='free',('retry ready',bf,tide))
   req(pl.on_ground,(bf,tide,'not grounded'));req(pl.hp==pl.maxhp,'retry HP')
   pressed=pl.pad;press(pressed,{'jump':True});y=pl.y;step(g,1,False);req(pl.y<y,('coop identical jump',bf,tide));pressed.nextc=None;step(g,1,False)
print('v13_input: OK zero-frame P2, high/low-tide respawn b10-b13')
for tide in (-20,32):
 g=new_game();sv=G['new_save']();sv.update(vellamo_unlocked=True,bonfire='b11');p=start(g,save=sv,bonfire='b11');q=ScriptPad('p2');g.add_pad(q);g.add_p2('hunter',q);g.start_boss('ahti');g.tide=tide;step(g,75,False)
 for pl in g.players:
  pl.pad.nextc=pl.pad.blank();g.update();pl.pad.nextc=dict(pl.pad.blank(),jump=True);y=pl.y;g.update();req(pl.y<y,('real boss tide',pl.idx,tide,pl.on_ground,pl.state,pl.y,y))
print('v13_input: real boss tides both pads OK')
# Real title routing: commit with a second device and preserve both identities.
active=ScriptPad('title-active');other=ScriptPad('title-other')
g=new_game();g.add_pad(active);g.add_pad(other)
sv=G['new_save']('warrior')
sv.update(done=True,bosses=['louhi'],p2={'cls':'hunter','level':1,'stats':{'vit':0,'end':0,'str':0,'foc':0},'souls':120})
G['write_save'](sv);g.open_title();tap(g,active,'down',hold=1,after=0)
active.nextc=dict(active.blank(),jump=True);g.update()
req(g.state_name in ('vellamo_arrival','play'),'P2-selected Continue to Vellamo')
req(g.players[0].pad is active and g.players[1].pad is other,'title P2 identities preserved')
print('v13_input: actual P2 title Continue routes and retains both pads')
