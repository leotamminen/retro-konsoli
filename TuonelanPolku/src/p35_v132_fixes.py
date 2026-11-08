"""1.3.2: complete bonfire names, directional shots and obvious Vellamo entrance."""
VERSION='1.3.2'
for b,nm,en in [
 ('b9','Pohjolan nuotio','Pohjola Bonfire'),('b10','Aallon ranta','Shimmering Shore'),
 ('b11','Syvänteen nuotio','Depths Bonfire'),('b12','Temppelin nuotio','Cathedral Bonfire'),
 ('b13','Vapauden ranta','Shore of Freedom'),
 ('vel_entrance','VELLAMON VALTAKUNTA  >','VELLAMO\'S REALM  >'),
 ('p_vellamo','Jatka Vellamon valtakuntaan','Enter Vellamo\'s realm'),
 ('vel_sign','Vellamon portti on heti nuotion oikealla puolella. Mene portille ja paina ylös.','\'Vellamo\'s gate is right by the bonfire. Go to it and press up.\'')]:_t(b,nm,en)
# Explicit entries are also safe for code that reads BF_KEYS directly.
BF_KEYS.update({('b%d'%i):'bf_b%d'%i for i in range(9,14)})
_VELLAMO_GATE=(454*TILE+8,320)
def _gate_unlocked(s):
    sv=s.save or {}
    return "louhi" in sv.get("bosses", []) and not sv.get("vellamo_visited")
_interact132=GameCore.interact
def interact132(s,p,near):
 if near==('vellamo_gate','gate'):
  if _gate_unlocked(s):sfx('confirm',.7);s.enter_vellamo()
  return
 return _interact132(s,p,near)
GameCore.interact=interact132
_items132=GameCore.interactables
def items132(s):
 out=_items132(s)
 if _gate_unlocked(s):out.append((_VELLAMO_GATE[0],_VELLAMO_GATE[1],'vellamo_gate','gate'))
 return out
GameCore.interactables=items132
_world132=GameCore.draw_world
def world132(s,c,t):
 _world132(s,c,t)
 if not _gate_unlocked(s) or s.area!='pohjola':return
 x=int(_VELLAMO_GATE[0]-s.cam[0]);y=int(_VELLAMO_GATE[1]-s.cam[1])
 # Tiny cached primitives only: a bright, readable portal and anchored sign.
 pygame.draw.rect(c,(35,116,133),(x-8,y-43,16,43),1)
 pygame.draw.rect(c,(67,182,184),(x-5,y-40,10,37),1)
 for k in range(3):pygame.draw.circle(c,(124,224,205),(x-6+k*6,y-35-((t//5+k*7)%25)),1)
 s.text(tr('vel_entrance'),x,y-51,(164,234,205),s.tiny)
GameCore.draw_world=world132
_dead132=GameCore.on_boss_dead
def dead132(s,b):
 _dead132(s,b)
 if b.key=='louhi':s.msg(tr('vel_sign'),(160,240,210))
GameCore.on_boss_dead=dead132
_area132=GameCore.update_area
def area132(s):
 _area132(s)
 if s.frames==3 and _gate_unlocked(s) and s.area=='pohjola':s.msg(tr('vel_sign'),(160,240,210))
GameCore.update_area=area132
# Direction comes from the same current pad state as all other actions.
# Pure vector changes only: no event reads, timers, or buffering.
def aim_up132(s,z,speed):
 horizontal=(1 if s.pad.held('right') else -1 if s.pad.held('left') else 0)
 if horizontal:z.vx=horizontal*speed/math.sqrt(2);z.vy=-speed/math.sqrt(2)
 else:z.vx=0.0;z.vy=-speed
# Wrap only projectile construction helpers. Directional velocity is a multiplier of
# the existing shot speed; all damage, focus, charge and projectile life stay as-is.
_arrow132=Player.fire_arrow
def fire_arrow132(s,dmg,speed,vy,charge,poise=8,n=1,spread=0.0):
 before=len(s.g.projs);_arrow132(s,dmg,speed,vy,charge,poise,n,spread)
 if s.pad.held('up'):
  for z in s.g.projs[before:]:aim_up132(s,z,speed)
Player.fire_arrow=fire_arrow132
_spell132=Player.fire_spell
def fire_spell132(s,a):
 before=len(s.g.projs);_spell132(s,a)
 if s.pad.held('up'):
  for z in s.g.projs[before:]:aim_up132(s,z,math.hypot(z.vx,z.vy))
Player.fire_spell=fire_spell132
