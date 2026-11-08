"""Aquatic bosses: unique telegraphed songs, waters, transformations, and sea-vines."""
class WaterBoss(Boss):
    def __init__(s,g,key,x,y):
        Boss.__init__(s,g,key,x,y);s.fly=False;s.vb='idle'
    def physics(s):
        s.vx *= 0.82; s.vy=min(MAX_FALL,s.vy+GRAV); move_body(s.g.wd,s)
        s.x=max(s.L+36, min(s.R-48, s.x))
    def hurt_rect(s):
        return (s.x-30, s.y-min(s.h, 108), 60, min(s.h, 108))
    def trans(s):
        s.atk=None;s.invuln=True;s.vb='roar';sfx('roar',.9);s.g.shake(3,38)
        for i in range(90):s.warn=90-i;s.warn_t=i;yield
        s.phase=2 if s.phase<2 else 3;s.invuln=False;s.vb='idle'
        MUSIC.request(s.key+('3' if s.phase==3 else '2'))
    def tell(s,n):
        n=tele(n);s.vb='windup'
        for i in range(n):s.warn=n-i;s.warn_t=i;yield
        s.warn=0;s.vb='attack'
    def wait(s,n):
        s.vb='idle'
        for _ in range(rest(n)):yield
    def shoot(s,kind,x,y,vx,vy,dmg=30,life=180,curve=0,col=(103,210,203)):
        s.g.projs.append(Proj(kind,x,y,vx,vy,dmg*D()['dmg'],10,28,tags=('magic',),life=life,curve=curve,col=col))
    def burst(s,n,speed=1.7,kind='runic'):
        for i in range(n):
            a=i*2*math.pi/n;s.shoot(kind,s.x,s.y-50,math.cos(a)*speed,math.sin(a)*speed,life=140)
    def brain(s):
        yield from s.tell(62);s.invuln=False
        yield from s.wait(22)
        while True:
            if s.key=='joukahainen':yield from s.jous()
            elif s.key=='ahti':yield from s.aht()
            elif s.key=='aino':yield from s.ain()
            else:yield from s.vel()
    def direction(s,x):return 1 if x>=s.x else -1
class Joukahainen(WaterBoss):
    def __init__(s,g,x,y):WaterBoss.__init__(s,g,'joukahainen',x,y)
    def jous(s):
        opts=['runes','bog','crossbow'] if s.phase<2 else ['runes','bog','crossbow','frost']
        s.actname=s.pick([(o,1) for o in opts])
        if s.actname=='runes':
            yield from s.tell(40)
            for j in range(5):
                for y in (250,277,304):s.shoot('verse',s.x-20,y,-2.0 if s.g.players[0].x<s.x else 2.0,0,22,curve=.008 if s.phase>=2 else 0)
                yield from s.wait(8)
        elif s.actname=='bog':
            yield from s.tell(48);t=s.mid_target()
            if t:s.g.zones.append(Zone(t.x,320,48,14,28,180,12*D()['dmg'],'bog',0))
            yield from s.wait(75)
        elif s.actname=='crossbow':
            yield from s.tell(29);t=s.mid_target();a=-math.pi
            if t:s.face=s.direction(t.x);a=math.atan2(t.y-16-s.y+57,t.x-s.x)
            for deg in (-12,0,12) if s.phase>=2 else (0,):
                angle=a+deg*math.pi/180;s.shoot('thornwave',s.x,s.y-57,math.cos(angle)*4,math.sin(angle)*4,34,curve=.012,col=(187,133,109))
            yield from s.wait(22)
        else:
            yield from s.tell(50)
            for j in range(4):s.g.zones.append(Zone(s.L+40+j*70,320,24,140,30+j*13,20,32*D()['dmg'],'frost',2.4))
            yield from s.wait(32)
class Ahti(WaterBoss):
    def __init__(s,g,x,y):WaterBoss.__init__(s,g,'ahti',x,y)
    def aht(s):
        opts=['wave','current','beasts','trident'] if s.phase<2 else ['wave','current','beasts','tide']
        s.actname=s.pick([(o,1) for o in opts])
        if s.actname=='wave':
            yield from s.tell(40)
            for side in (-1,1):
                for i in range(6):s.shoot('swell',s.x,320-i*9,side*2.2,-.13,28,curve=.004)
            yield from s.wait(28)
        elif s.actname=='current':
            yield from s.tell(48);direction=random.choice((-1,1))
            for i in range(125):
                for p in s.g.players:
                    if p.alive() and p.state not in ('roll','hurt'):p.vx=max(-2.8,min(2.8,p.vx+direction*.09))
                if i%12==0:s.shoot('bubble',random.uniform(s.L,s.R),318,-direction*.5,-.5,18,life=130)
                yield
            yield from s.wait(18)
        elif s.actname=='beasts':
            yield from s.tell(52)
            for dx in (-92,62):s.g.zones.append(Zone(max(s.L,min(s.R,s.x+dx)),320,27,90,20,23,27*D()['dmg'],'tentacle',2.7))
            yield from s.wait(38)
        elif s.actname=='trident':
            yield from s.tell(38)
            for x in [s.L+35,s.L+95,s.L+155,s.L+215,s.R-22]:s.g.zones.append(Zone(x,320,22,113,18,25,37*D()['dmg'],'tidepike',2))
            yield from s.wait(24)
        else:
            yield from s.tell(44)
            for x in range(int(s.L+28),int(s.R),50):s.g.zones.append(Zone(x,315,29,180,10,150,22*D()['dmg'],'tentacle',2.6))
            yield from s.wait(30)
class Aino(WaterBoss):
    def __init__(s,g,x,y):WaterBoss.__init__(s,g,'aino',x,y)
    def die(s,pl):s.calm()
    def calm(s):s.hp=1;s.gen=None;s.g.start_aino_reveal()
    def ain(s):
        acts=['fin','drop','stream'] if s.phase<2 else ['fin','memory','stream','transform']
        if s.phase>=3:acts=['stream','memory','transform','fin']
        s.actname=s.pick([(o,1) for o in acts])
        if s.actname in ('fin','transform'):
            s.vb='fish';yield from s.tell(34);t=s.mid_target()
            if t:s.face=s.direction(t.x)
            for dx in (-45,0,45) if s.phase>=3 else (0,):s.shoot('thornwave',s.x,s.y-45,(-s.face*3.1+dx*.006),.3,28,curve=.024,col=(155,214,219))
            yield from s.wait(23);s.vb='maiden'
        elif s.actname=='drop':
            yield from s.tell(43);t=s.mid_target()
            if t:s.shoot('memory',t.x,110,0,.7,32,curve=.014,col=(192,181,231))
            yield from s.wait(40)
        elif s.actname=='stream':
            yield from s.tell(34)
            for side in (-1,1):
                for y in range(263,321,18):s.shoot('bubble',s.x,y,side*2.35,-.18,25,curve=-.001)
            yield from s.wait(20)
        else:
            yield from s.tell(45)
            for x in (s.L+38,s.L+105,s.R-40):s.g.zones.append(Zone(x,320,34,150,28,18,35*D()['dmg'],'frost',2))
            yield from s.wait(25)
class Vellamo(WaterBoss):
    def __init__(s,g,x,y):WaterBoss.__init__(s,g,'vellamo',x,y)
    def vel(s):
        acts=['lattice','crown','undertow'] if s.phase<2 else ['lattice','crown','undertow','cage']
        if s.phase>=3:acts=['lattice','crown','undertow','cage','erasure']
        s.actname=s.pick([(o,1) for o in acts])
        if s.actname=='lattice':
            yield from s.tell(48)
            for j in range(9 if s.phase<3 else 13):
                y=225+(j%5)*17;s.shoot('memory',s.x-28,y,-2.4,0,34,curve=.003*(1 if j%2 else -1),col=(156,166,211));yield from s.wait(4)
        elif s.actname=='crown':
            yield from s.tell(44)
            for x in range(int(s.L+20),int(s.R),52):s.g.zones.append(Zone(x,320,28,130,tele(35)+((x//20)%3)*11,21,36*D()['dmg'],'tidepike',3))
            yield from s.wait(28)
        elif s.actname=='undertow':
            yield from s.tell(43)
            for i in range(105):
                for p in s.g.players:
                    if p.alive():p.vx+=(s.x-p.x)*.0015
                if i%15==0:s.burst(5,1.35,'bubble')
                yield
            yield from s.wait(20)
        elif s.actname=='cage':
            yield from s.tell(46);t=s.mid_target()
            if t:s.g.zones.append(Zone(t.x,320,70,95,22,25,43*D()['dmg'],'cage',2))
            yield from s.wait(32)
        else:
            yield from s.tell(54);s.burst(13,2.0,'memory')
            for x in range(int(s.L+15),int(s.R),53):s.g.zones.append(Zone(x,320,18,118,25,15,36*D()['dmg'],'frost',2))
            yield from s.wait(30)
BOSS_CLS.update(joukahainen=Joukahainen,ahti=Ahti,aino=Aino,vellamo=Vellamo)
