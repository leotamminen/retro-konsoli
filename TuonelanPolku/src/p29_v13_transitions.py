_old_true=GameCore.on_boss_dead
# on_dead else path already calls old core true-end handler; append unlock-safe gc trigger there.
_on13=GameCore.on_boss_dead
def dead13(s,b):
    _on13(s,b)
    if b.key=='louhi':
        s.wd.set_open('d_vellamo',True)
        s.save['vellamo_unlocked']=True
        s.save_game()
    gc.collect()
GameCore.on_boss_dead=dead13
_arena13=GameCore.start_boss
def arena13(s,key):
    _arena13(s,key)
    a=ARENAS[key]
    # Subsequent nearby chunks are cheap and loaded while under entry i-frames.
    for tx,dir in ((a['x0'],-1),(a['x0']+4,1)):
        if tx>=486:s.chunk(tx//20);break
GameCore.start_boss=arena13
_respawn13=GameCore.respawn
def respawn13(s):
    _respawn13(s)
    if s.save.get('vellamo_clear'):s.save['vellamo_clear']=True
GameCore.respawn=respawn13
_restore=GameCore.start_session
def session13(s,save,pad):
    _restore(s,save,pad)
    if save.get("p2") and len(s.players)==1:
        other=physical_pad(s, pad)
        if other is not None: s.add_p2(save["p2"]["cls"], other)
GameCore.start_session=session13
# No entry action lag on reveal, ending or arrival; handlers consume this frame's menu results.
_arrival=GameUI.up_vellamo_arrival
def arrival13(s):
    _arrival(s);gc.collect();pygame.event.clear()
GameUI.up_vellamo_arrival=arrival13
