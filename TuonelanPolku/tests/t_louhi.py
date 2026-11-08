"""Tytti fake ending, interruption, checkpoint, Louhi fight/ending and old-save route."""
import traceback,random,time
from lib import *
R=[]
def ok(v,label):R.append((bool(v),label));print(("PASS " if v else "FAIL ")+label)
def act(p,key,frames=1):
    for i in range(frames):
        p.nextc=dict(p.blank(),x=1 if key=="right" else -1 if key=="left" else 0,right=key=="right",left=key=="left",**({key:True} if key in ('jump','light') else {}));step(g,1,draw=(i%3==0))
    p.nextc=None
#Original boss combat ending handoff test.
g=new_game();start(g,bonfire='b8');g.start_boss('tytti');g.boss.invuln=False;g.boss.hp=0;g.boss.take(99999,pl=g.players[0]);g.ending_t=260;step(g,1);ok(g.state_name=='ending','Tytti fake ending starts')
step(g,70);act(g.last_pad,'jump');step(g,160);ok(g.state_name=='interrupt','Louhi interrupts during original ending text');shot(g,'12_louhi_interrupt');step(g,210);ok(g.state_name=='poht','black screen follows interrupt')
step(g,45);shot(g,'12_pohjola_dark');step(g,75);ok(g.state_name=='play' and g.save['bonfire']=='b9','Pohjola spawns at immediate checkpoint')
p=g.last_pad=g.players[0].pad;p.idx=-1
for i in range(500):
    p.nextc=pad_blank_safe=None;p.nextc=dict(p.blank(),x=1,right=True);g.update();p.nextc=None
    if g.boss:break
ok(g.boss is not None and g.boss.key=='louhi','walking right starts Louhi')
seen={1}
for i in range(2800):
    if g.players[0].alive():g.players[0].hp=g.players[0].maxhp
    if g.boss and not g.boss.dead:
        seen.add(int(g.boss.phase));g.boss.invuln=False
        if i in (500,1500):g.boss.hp=g.boss.maxhp*(.65 if i==500 else .32)
    step(g,1,draw=i%20==0)
    if i in (550,1650):g.draw();shot(g,'12_louhi_phase%d'%(2 if i==550 else 3))
ok({1,2,3}<=seen,'all three Louhi phases reachable')
g.boss.invuln=False;g.boss.hp=1;g.boss.take(99999,pl=g.players[0]);step(g,247);ok(g.state_name=='true','true ending blackout starts');step(g,130);ok(g.state_name=='true_ending','real ending text visible');shot(g,'12_real_ending')
# retries retain secret area and no ending loop.
g=new_game();start(g,bonfire='b9');g.start_boss('louhi');g.boss.gen=None;g.boss.hp=g.boss.maxhp;g.players[0].die();step(g,215);ok(g.state_name=='play' and g.save['bonfire']=='b9','death returns to Pohjola checkpoint without fake ending')
old=G['new_save']();old['bosses']=['hiisi','turso','tytti'];old['done']=True
ss=G['sanitize_save'](old);ok(ss and ss['louhi_unlocked'],'pre-1.2 completed save unlocks secret')
print('FAILURES',[n for v,n in R if not v]);raise SystemExit(any(not v for v,n in R))
