# 1.3.1: independently constructed large, animated character sprites; cached only.
def _young_singer(pose,ph,t):
    s=mk(192,160);skin=(226,187,145);fur=(87,65,48);fur_hi=(151,119,78)
    tunic=(135,64,45);vest=(42,83,78);pants=(61,71,56);wood=(152,105,60)
    if pose=='roar':skin=(242,201,166)
    # Upright narrow northern minstrel, long legs, no hood or crown.
    pygame.draw.polygon(s,(42,40,34),[(85,98),(99,98),(108,131),(114,146),(108,150),(96,149),(90,136)])
    pygame.draw.polygon(s,pants,[(88,96),(94,104),(91,128),(83,141),(91,145),(99,130),(101,113),(107,125),(120,138),(126,143),(122,148),(111,147),(105,143),(96,131)])
    pygame.draw.rect(s,(74,46,29),(104,137,10,8));pygame.draw.rect(s,(91,58,32),(112,140,16,4))
    pygame.draw.polygon(s,tunic,[(88,53),(106,52),(111,79),(106,111),(86,111),(82,82)])
    pygame.draw.polygon(s,vest,[(91,58),(99,67),(106,58),(106,98),(94,106),(88,94)])
    for yy in (73,82,91,100):pygame.draw.line(s,(205,156,89),(91,yy),(103,yy+2),1)
    pygame.draw.polygon(s,(177,129,69),[(83,97),(113,95),(112,102),(85,108)])
    for xx in range(84,112,6):pygame.draw.line(s,fur_hi,(xx,101+(xx%3)),(xx+1,109),2)
    # Wind-blown wool scarf and knife sheath.
    pygame.draw.polygon(s,vest,[(87,49),(105,51),(99,60),(91,65),(63,60),(73,53)])
    pygame.draw.polygon(s,(78,133,123),[(84,55),(83+((t%4)-2)*2,77),(79,99),(86,89)])
    pygame.draw.line(s,wood,(77,104),(80,126),4);pygame.draw.rect(s,(191,185,132),(76,127,7,2))
    pygame.draw.rect(s,skin,(99,46,5,11))
    # Face in left profile, fur cap with a folded Cossack edge (not spikes).
    pygame.draw.ellipse(s,fur,(87,13,30,36));pygame.draw.ellipse(s,skin,(91,23,22,30))
    pygame.draw.polygon(s,skin,[(91,32),(88,37),(93,39),(91,44),(94,50),(103,49),(104,36)])
    pygame.draw.ellipse(s,fur,(86,14,30,20));pygame.draw.rect(s,fur,(86,24,13,16));pygame.draw.rect(s,fur_hi,(87,22,27,7))
    for xx in range(89,111,4):pygame.draw.line(s,(181,150,112),(xx,22),(xx+1,28),1)
    pygame.draw.polygon(s,(59,112,101),[(104,18),(119,14+(t%2)),(115,22),(111,26)])
    pygame.draw.line(s,(219,221,174),(107,18),(117,14+(t%2)),1)
    pygame.draw.line(s,(48,37,33),(90,32),(94,31),1);pygame.draw.rect(s,(23,33,31),(91,35,1,1))
    pygame.draw.polygon(s,(71,43,31),[(89,43),(95,41),(96,48),(91,49)])
    pygame.draw.rect(s,(215,184,140),(91,42,4,2))
    # Singing arm extends toward the player; bow and quiver are clearly not a trident.
    bow_y=59 if pose!='windup' else 53
    pygame.draw.line(s,tunic,(88,59),(80,76),7);pygame.draw.line(s,skin,(80,76),(66,64),4)
    pygame.draw.line(s,tunic,(106,58),(116,69),6);pygame.draw.line(s,skin,(116,69),(123,59),4)
    pygame.draw.circle(s,skin,(124,57),4)
    pygame.draw.arc(s,wood,(43,bow_y-27,49,66),.5,5.85,3)
    pygame.draw.arc(s,fur_hi,(43,bow_y-26,48,65),.5,5.85,1)
    pygame.draw.line(s,(215,216,187),(65,bow_y-26),(65,bow_y+39),1)
    pygame.draw.line(s,(155,163,143),(65,bow_y+6),(124,bow_y+1),2)
    pygame.draw.polygon(s,(213,224,197),[(59,bow_y+6),(68,bow_y+3),(68,bow_y+9)])
    for yy in (47,54,61):pygame.draw.line(s,wood,(116,yy),(115,yy+27),1)
    # Floating sung runes: angular syllables, not crown/antlers.
    for i in range(1+ph):
        x=25+(i%2)*22;y=30+i*20-((t//4)%3)
        pygame.draw.line(s,(147,216,194),(x,y),(x+7,y+4),(2));pygame.draw.line(s,(163,230,203),(x+7,y+4),(x+2,y+10),(2))
        pygame.draw.line(s,(147,216,194),(x+2,y+10),(x+8,y+14),(2));pygame.draw.rect(s,(225,247,199),(x+11,y+1,1,1))
    if ph>=2:
        pygame.draw.arc(s,(227,177,94),(33,72,66,33),3.3,5.85,2)
        for x in (30,41,53):pygame.draw.line(s,(206,184,112),(x,90),(x+12,81),1)
    return s

def _sea_king(pose,ph,t):
    s=mk(192,160);skin=(134,151,127);coat=(36,89,83);moss=(64,111,65);seaweed=(88,133,75)
    # Immense barnacled shoulders rising from a rough sea, unlike Turso's bare serpent.
    pygame.draw.polygon(s,(22,63,68),[(16,151),(24,124),(39,106),(56,86),(73,80),(120,82),(148,100),(165,131),(172,151)])
    pygame.draw.polygon(s,coat,[(28,140),(37,104),(59,92),(73,82),(116,83),(143,103),(158,139),(158,154),(28,153)])
    pygame.draw.ellipse(s,skin,(59,26,79,75))
    # Reedy hair/gills and broad old-king nose, no glowing red hooded eyes.
    pygame.draw.polygon(s,(59,89,59),[(63,40),(47,56),(51,83),(62,77),(70,38)])
    pygame.draw.polygon(s,(59,89,59),[(132,42),(146,55),(140,82),(128,76),(121,40)])
    pygame.draw.ellipse(s,(174,182,144),(81,43,39,47))
    pygame.draw.polygon(s,(154,162,124),[(96,47),(87,61),(98,66),(91,73),(102,77),(111,66),(110,50)])
    pygame.draw.line(s,(50,75,58),(82,54),(93,53),3);pygame.draw.line(s,(50,75,58),(107,53),(120,54),3)
    pygame.draw.rect(s,(219,211,130),(85,56,3,2));pygame.draw.rect(s,(219,211,130),(111,56,3,2))
    pygame.draw.line(s,(94,109,87),(91,75),(108,75),2)
    # Salt beard: masses, ridges and hanging kelp; central shaded mouth is visible.
    for i in range(7):
        xx=74+i*8;bottom=112+((i*11+t)%14)
        pygame.draw.ellipse(s,moss if i%2 else seaweed,(xx,70,18,bottom-70))
        pygame.draw.line(s,(119,153,83),(xx+7,78),(xx+4,102),1)
    for i in (1,3,5):
        x=76+i*8;pygame.draw.line(s,(45,104,74),(x,105),(x-4+((t+i)%4),130),3)
        pygame.draw.polygon(s,(88,136,75),[(x,111),(x-12,108),(x,116),(x+9,121)])
    # Shell diadem resting on brow, materially different from pointed witch crown.
    for xx in (77,91,105,119):
        pygame.draw.arc(s,(155,182,170),(xx-8,18,20,19),0,math.pi,3)
        pygame.draw.line(s,(80,135,128),(xx+1,21),(xx+1,30),1)
    pygame.draw.rect(s,(61,114,111),(76,31,56,4))
    for x,y in ((75,37),(133,36),(101,18),(109,34)):pygame.draw.circle(s,(186,205,177),(x,y),2)
    # Shell breastplate/moss, crab claws at ends of bulky shoulder line.
    for i in range(12):
        x=42+(i*19)%96;y=97+(i*13)%25
        pygame.draw.ellipse(s,(103,133,96),(x,y,10,7));pygame.draw.ellipse(s,(163,174,128),(x+2,y,7,3))
    for x,sg in ((31,-1),(145,1)):
        pygame.draw.arc(s,(94,123,89),(x-10,94,28,38),0,5.8,4)
        pygame.draw.polygon(s,(108,145,100),[(x,113),(x+sg*16,100),(x+sg*19,110),(x+sg*7,117),(x+sg*15,124),(x+sg*1,127)])
    # Strong asymmetric trident silhouette, its shaft ends below the water line.
    try_y=18 if pose!='attack' else 42
    pygame.draw.line(s,(115,139,109),(168,try_y+22),(164,155),4)
    pygame.draw.line(s,(215,201,132),(167,try_y+23),(162,152),1)
    for dx,dy in ((-12,0),(0,-10),(12,0)):
        pygame.draw.line(s,(143,181,155),(168,try_y+25),(168+dx,try_y+dy),3)
        pygame.draw.polygon(s,(217,223,177),[(168+dx,try_y+dy-4),(164+dx,try_y+dy+7),(171+dx,try_y+dy+8)])
    pygame.draw.line(s,(164,190,155),(154,try_y+27),(182,try_y+27),3)
    for i in range(6):
        x=17+i*31;pygame.draw.arc(s,(91,157,154),(x,138+(i%2)*4,39,18),0,math.pi,2)
    if ph>=2:
        for x in (40,61,142):pygame.draw.arc(s,(168,223,196),(x,85,15,65),1.2,4.1,1)
    return s

def _water_queen(pose,ph,t):
    s=mk(192,160);skin=(193,227,222);gown=(51,117,155);edge=(122,215,204);hair=(116,181,197)
    flow=(t%4)-2
    # Tall poised queen, tapered bare shoulders and a pearlescent bodice.
    pygame.draw.polygon(s,gown,[(90,70),(106,70),(111,91),(105,110),(101,126),(111,140),(134,156),(119,157),(100,148),(91,139),(73,151),(44,157),(58,146),(75,137),(84,118),(84,94)])
    pygame.draw.polygon(s,(78,159,173),[(91,71),(96,76),(91,96),(92,111),(86,127),(74,140),(51,154),(69,144),(82,129),(89,117),(89,89)])
    pygame.draw.polygon(s,(42,99,147),[(103,73),(110,91),(103,113),(98,124),(104,137),(127,153),(116,152),(99,141),(92,126),(99,108)])
    pygame.draw.polygon(s,edge,[(104,133),(122,158),(133,151),(139,143),(142,155),(126,159),(115,156)])
    pygame.draw.polygon(s,edge,[(78,137),(60,144),(47,151),(39,147),(43,156),(55,159),(70,153),(87,142)])
    # Water hair flows way beyond head, not a triangular hood.
    for side in (-1,1):
        for j in range(3):
            x=98+side*(10+j*4);y=39+j*7
            pygame.draw.lines(s,hair,False,[(x,y),(x+side*7,y+13),(x+side*(11+flow),y+25),(x+side*3,y+36)],5-j)
            pygame.draw.line(s,(168,219,216),(x+side,y),(x+side*7,y+19),1)
    pygame.draw.polygon(s,skin,[(90,37),(90,28),(103,28),(107,38),(104,57),(112,69),(87,69),(96,56)])
    pygame.draw.ellipse(s,skin,(90,27,16,29));pygame.draw.polygon(s,skin,[(97,36),(91,41),(98,44)])
    pygame.draw.line(s,(38,83,111),(91,37),(95,37),1);pygame.draw.line(s,(39,83,111),(101,37),(104,37),1)
    pygame.draw.line(s,(47,91,119),(92,49),(102,49),2)
    # Intricate shell/pearl diadem (rounded, not antlers).
    for i in range(5):
        x=85+i*6;yy=25-(2 if i in (1,3) else 0)
        pygame.draw.ellipse(s,(162,202,211),(x,yy,8,11));pygame.draw.arc(s,(235,232,207),(x+1,yy,6,9),.4,2.9,1)
        pygame.draw.circle(s,(224,237,218),(x+3,yy+3),1)
    for x in (79,116,96):pygame.draw.circle(s,(215,229,203),(x,31 if x!=96 else 20),2)
    # Exposed sculptural arms in a commanding song, separate from cape.
    if pose in ('windup','attack','reveal','roar'):
        pygame.draw.lines(s,skin,False,[(90,67),(76,66),(65,53),(56,42)],7)
        pygame.draw.lines(s,(124,184,182),False,[(65,53),(60,32)],3)
        pygame.draw.circle(s,(163,233,218),(58,36),9,2)
        pygame.draw.lines(s,skin,False,[(108,67),(124,72),(130,90)],7)
        pygame.draw.arc(s,(165,226,204),(133,81,20,16),1.2,5.7,2)
    else:
        pygame.draw.lines(s,skin,False,[(90,67),(80,85),(98,89)],7)
        pygame.draw.lines(s,skin,False,[(107,67),(120,83),(107,92)],7)
    pygame.draw.polygon(s,(135,203,206),[(89,65),(98,70),(108,64),(112,79),(101,88),(88,80)])
    pygame.draw.circle(s,(226,236,200),(98,79),4,1)
    # Fish-scale skirt dissolving to long forked water/tail shapes, not fabric cone.
    for row in range(3):
        for i in range(3-row):
            x=82+i*7+row*3;y=92+row*10
            pygame.draw.arc(s,edge,(x,y,11,9),0,math.pi,1)
    pygame.draw.lines(s,(139,216,210),False,[(84,118),(85,130),(91,139),(103,145),(115,156),(129,156)],1)
    if ph>=2:
        for j in range(3):pygame.draw.arc(s,(154,219,200),(23+j*14,103+j*11,121-j*9,22),0,math.pi,1)
    if ph>=3:
        pygame.draw.arc(s,(184,233,219),(47,6,95,135),.8,2.7,1)
        pygame.draw.circle(s,(207,249,229),(58,36),6,1)
    return s

def _braided_maiden(pose,ph,t):
    s=mk(192,160);skin=(240,200,166);dress=(127,157,158);hem=(186,210,185);hair=(165,116,59)
    # Ground-shy, visibly human young woman, bright dress and separated braids.
    pygame.draw.polygon(s,(72,75,83),[(86,125),(94,125),(92,148),(82,150),(79,147)])
    pygame.draw.polygon(s,(72,75,83),[(99,125),(108,125),(113,145),(109,150),(103,148)])
    pygame.draw.polygon(s,dress,[(86,68),(106,68),(112,92),(118,129),(78,129),(85,93)])
    pygame.draw.polygon(s,hem,[(85,105),(111,105),(118,129),(78,129)])
    pygame.draw.polygon(s,(150,180,176),[(87,71),(96,78),(105,71),(107,97),(87,98)])
    pygame.draw.rect(s,(219,207,147),(78,128,40,3))
    pygame.draw.ellipse(s,skin,(88,38,21,26));pygame.draw.rect(s,skin,(94,60,7,10))
    pygame.draw.ellipse(s,hair,(86,34,25,27));pygame.draw.polygon(s,hair,[(89,43),(87,57),(95,60),(95,40)])
    pygame.draw.polygon(s,skin,[(92,45),(102,42),(108,48),(102,50),(102,59),(94,58),(92,50)])
    pygame.draw.line(s,(101,59,38),(89,39),(105,40),2);pygame.draw.rect(s,(53,44,30),(104,46,1,1));pygame.draw.line(s,(147,71,62),(101,54),(105,54),1)
    for side in (-1,1):
        for j in range(5):
            x=97+side*(10+(j%2)*2);y=56+j*5
            pygame.draw.ellipse(s,hair,(x-4,y-2,8,7))
        pygame.draw.rect(s,(109,162,157),(93+side*9,77,7,3))
    for x,y in ((86,77),(111,83)):
        pygame.draw.line(s,skin,(x,y),(x-8,y+12),5);pygame.draw.circle(s,skin,(x-8,y+12),3)
    if pose in ('windup','attack','roar'):
        pygame.draw.arc(s,(156,224,210),(64,70,72,57),0,math.pi,3)
        pygame.draw.arc(s,(209,232,206),(68,78,64,36),0,math.pi,2)
    elif ph>=2:
        pygame.draw.arc(s,(148,220,200),(65,84,67,43),0,5.4,1)
    return s

def newboss_frame(key,pose,phase,t):
    k=(key,pose,pose=='fish',phase,t%4)
    if k in _BSPR:return _BSPR[k]
    if key=='aino' and pose=='fish':
        s=mk(192,160);jr=(t%4)
        pygame.draw.ellipse(s,(83,153,174),(37,62-jr,119,47));pygame.draw.polygon(s,(145,194,187),[(40,82-jr),(9,47-jr),(14,112-jr),(46,94-jr)])
        pygame.draw.ellipse(s,(132,207,198),(46,61-jr,114,47),2)
        for i in range(5):pygame.draw.arc(s,(189,221,188),(58+i*16,43-jr,34,55),.8,2.1,2)
        pygame.draw.circle(s,(239,215,162),(136,87),5);pygame.draw.circle(s,(23,45,64),(136,87),2)
        pygame.draw.arc(s,(58,112,146),(130,92,19,20),1,4,2)
        for i in range(4):pygame.draw.arc(s,(193,229,216),(53+i*18,87,29,12),0,math.pi,1)
    else:
        s={'joukahainen':_young_singer,'ahti':_sea_king,'aino':_braided_maiden,'vellamo':_water_queen}[key](pose,phase,t)
    s=_outline(s,(13,31,40)).subsurface((1,1,s.get_width(),s.get_height())).copy()
    _BSPR[k]=s
    return s

def aino_glimpse(surf,tx,t):
    spr=newboss_frame('aino','maiden' if tx<598 else 'fish',1,t//8)
    surf.blit(spr,(int(tx-spr.get_width()/2),int(100-spr.get_height()/2)))
