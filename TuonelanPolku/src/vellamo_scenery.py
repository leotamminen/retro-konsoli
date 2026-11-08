# Cached, tiled water surfaces: no large allocation or gradient per game frame.
def vellamo_bg(name):
    if name not in _WL_BG:
        sf=pygame.Surface((W,H));top,bot=PAL[name]['sky']
        for y in range(H):
            f=y/(H-1);pygame.draw.line(sf,tuple(int(top[i]*(1-f)+bot[i]*f) for i in range(3)),(0,y),(W,y))
        # Three slender rays. Tapered edges make the water luminous, not scanlined.
        ray=mk(W,H)
        for i in range(3):
            x=21+i*145
            pygame.draw.polygon(ray,(top[0]+6,top[1]+11,top[2]+12),[(x,0),(x+9,0),(x+83,H),(x+41,H)])
            pygame.draw.polygon(ray,(top[0]+3,top[1]+6,top[2]+5),[(x+13,0),(x+19,0),(x+57,H),(x+40,H)])
        sf.blit(ray,(0,0))
        # Irregular gentle caustics only in the upper band of the tile.
        for i in range(10):
            x=7+i*37;y=11+(i*11)%35
            pygame.draw.arc(sf,(top[0]+9,top[1]+16,top[2]+18),(x,y,19,8),.12,2.92,1)
        _WL_BG[name]=sf
    return _WL_BG[name]
_WL_BG={'blank_fog':mk(1,1)}
def water_layers(ar):
    if ar not in _PAR13:
        sh=mk(480,180)
        if ar=='ranta':
            # Reeds and old rocks recede below the luminous water surface.
            for i in range(18):
                x=i*31;y=148-(i*19)%38
                pygame.draw.ellipse(sh,(37,90,90),(x-10,y,38,56-y))
                pygame.draw.line(sh,(43,108,89),(x,180),(x+(i%3)-1,y+2),2)
                for j in range(3):pygame.draw.line(sh,(44,101,85),(x,y+8+j*7),(x-7+(i%2)*12,y+3+j*7),1)
        elif ar=='syvanne':
            # Kelp ribbons stand far apart; contrast drops into dark water.
            for i in range(19):
                x=i*26;hy=42+(i*29)%63
                pygame.draw.lines(sh,(30,78,81),False,[(x,180),(x+4,151),(x-2,135),(x+6,115),(x+3,hy)],3)
                for j in range(3):
                    y=hy+j*20
                    pygame.draw.ellipse(sh,(37,91,80),(x-7+(j%2)*7,y,11,4))
                pygame.draw.circle(sh,(56,116,106),(x+3,hy),3)
        else:
            # Sunken cathedral: round arches and surviving paired columns.
            for x in (-8,106,230,354):
                pygame.draw.rect(sh,(43,94,94),(x,61,88,119))
                pygame.draw.ellipse(sh,PAL[ar]['sky'][0],(x+10,79,64,82))
                for xx in (x+4,x+70):
                    pygame.draw.rect(sh,(65,124,109),(xx,76,11,104))
                    pygame.draw.rect(sh,(76,136,118),(xx-3,72,17,5))
                    for yy in range(83,165,10):pygame.draw.line(sh,(50,102,95),(xx+3,yy),(xx+3,yy+5),1)
                pygame.draw.arc(sh,(65,126,110),(x+6,70,75,90),0,math.pi,4)
                pygame.draw.line(sh,(62,124,112),(x,61),(x+88,61),3)
            pygame.draw.line(sh,(54,105,99),(0,178),(480,178),3)
        for i in range(13):
            xx=17+(i*109)%432;yy=23+(i*59)%111
            if ar!='katedraali' or yy<74:
                pygame.draw.circle(sh,(65,123,127),(xx,yy),2,1)
                pygame.draw.rect(sh,(91,150,145),(xx-1,yy-1,1,1))
        ps=mk(480,180);ps.blit(sh,(0,0));_PAR13[ar]=[(ps,.28,0)]
    return _PAR13[ar]
_PAR13={}

# Generic fog uses a source-alpha fill; a translucent ellipse without its
# fill would be completely opaque. Clear low-alpha water mist at the seam.
def water_fog(ar):
    key='mist_'+ar
    if key not in _WL_BG:
        sf=mk(640,64);sf.fill((0,0,0,0))
        for i in range(8):
            x=16+i*80;y=32+(i%3)*8
            pygame.draw.arc(sf,(40,82,103,25),(x-50,y-8,110,15),.18,2.95,2)
            pygame.draw.arc(sf,(53,105,120,17),(x-34,y-3,76,19),3.3,6.08,2)
        _WL_BG[key]=sf
    return _WL_BG[key]
