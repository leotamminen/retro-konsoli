def aquatic_brain(s):
    fall=0
    s.fly = s.kind != "rapu"
    while True:
        t=s.target()
        if t:s.see(t)
        if s.kind=='lampi':
            gx=s.hx+math.sin(s.t*.02)*28; gy=s.hy-62+math.sin(s.t*.05)*10
            s.vx=(gx-s.x)*.03; s.vy=(gy-s.y)*.03
            if t and s.t%130==0:
                s.g.projs.append(Proj('bubble',s.x,s.y-6,(t.x-s.x)*.008,-.25,14*D()['dmg'],7,12,tags=('magic',),life=110,col=(186,236,220)))
        elif s.kind=='rapu':
            if t and abs(t.x-s.x)<80 and s.t%90<18:
                s.vx=1.7 if t.x>=s.x else -1.7
            else:
                s.vx=0.4 if (s.t//70)%2==0 else -0.4
            s.vy=min(MAX_FALL,s.vy+GRAV)
        elif s.kind=='poltto':
            gx=s.hx+math.sin(s.t*.028)*42;gy=s.hy-45+math.sin(s.t*.07)*20
            s.vx=(gx-s.x)*.035;s.vy=(gy-s.y)*.035
            if t and s.t%100==0:s.g.projs.append(Proj('bubble',s.x,s.y-8,(t.x-s.x)*.013,-.5,17*D()['dmg'],8,17,tags=('magic',),life=140,col=(144,225,209)))
        elif s.kind=='merikala':
            if t:s.vx=(t.x-s.x)*.024;s.vy=(t.y-12-s.y)*.024+math.sin(s.t*.068)*.45
            s.vy=min(1.8,max(-1.8,s.vy))
        elif s.kind=='haaksi':
            gx=s.hx+math.sin(s.t*.015)*36; gy=s.hy-50
            s.vx=(gx-s.x)*.02; s.vy=(gy-s.y)*.02
            if t and s.t%160==0:
                s.g.projs.append(Proj('bubble',s.x,s.y-6,(t.x-s.x)*.006,-.2,12*D()['dmg'],7,12,tags=('magic',),life=100,col=(186,236,220)))
        elif s.kind=='koralli':
            if t and abs(t.x-s.x)<70 and s.t%110<16:
                s.vx=1.3 if t.x>=s.x else -1.3
            else:
                s.vx=0.25 if (s.t//90)%2==0 else -0.25
            s.vy=min(MAX_FALL,s.vy+GRAV)
        elif s.kind=='ankkuri':
            if t and abs(t.x-s.x)<90:
                s.vx=0.35 if t.x>=s.x else -0.35
            else:
                s.vx=0.15 if (s.t//100)%2==0 else -0.15
            s.vy=min(MAX_FALL,s.vy+GRAV)
        elif s.kind=='pylvas':
            s.vx=0; s.vy=min(MAX_FALL,s.vy+GRAV)
            if t and s.t%150==0:
                s.g.projs.append(Proj('verse',s.x,s.y-16,(1 if t.x>=s.x else -1)*1.1,0,14*D()['dmg'],7,12,tags=('magic',),life=120,col=(180,160,220)))
        else:
            gx=s.hx+math.sin(s.t*.045)*24;gy=s.hy-16;s.vx=(gx-s.x)*.038;s.vy=(gy-s.y)*.026
            if t and s.t%110==0:
                for z in (-1,0,1):s.g.projs.append(Proj('verse',s.x,s.y-15,z*1.2,-.6,22*D()['dmg'],7,11,tags=('magic',),life=135,curve=.03,col=(154,178,209)))
        yield
