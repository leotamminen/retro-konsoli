from lib import *
def req(c,v):
 if not c:raise AssertionError(v)
# No ordinary gate access, no Vellamo row, existing Louhi migration preserved.
g=new_game();v=G['new_save']();start(g,save=v,bonfire='b9',pad=(p:=ScriptPad('p')))
p.nextc=dict(p.blank(),right=True,x=1);step(g,600,False);req(g.save['vellamo_visited']==False,'locked visited');req(g.players[0].x<486*16,'physical locked border');step(g,2);g.open_map('play');step(g,1,True);g.build_map();req(len(g.mapimg)==4,'hidden map rows')
v['bosses']=['louhi'];v['done']=True;g.save_game();sv,st=G['load_save']();req(sv['vellamo_unlocked'] and not sv['vellamo_visited'],'Louhi migration')
g=new_game();p=start(g,save=sv,bonfire='b9');req(g.wd.opened('d_vellamo'),'migrated open session gate')
# Bog finite/escapable and one per-player record, not a center-clamp every frame.
g=new_game();v=G['new_save']();v.update(vellamo_unlocked=True,bonfire='b10');p=start(g,save=v,bonfire='b10');g.start_boss('joukahainen');step(g,65,False);b=g.boss;b.invuln=False;b.gen=None;b.phase=2;b.pick=lambda opts:'bog';b.gen=b.jous();step(g,155,False);req(any(z.style=='bog' for z in g.zones),'bog attack')
p.nextc=dict(p.blank(),jump=True);step(g,1,False);req(g.players[0].vy<0 and g.players[0].y<320,'0-frame bog escape')
g.start_aino_reveal();assert g.save['bonfire']=='b13';g.players[0].x=624*16;g.respawn();assert g.save['bonfire']=='b13','Vellamo retry'
print('v13_gate_bog: locked border/migration/explored rows, escapable bog and nearby retry OK')
