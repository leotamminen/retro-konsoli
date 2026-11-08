from lib import *
pygame.init();canvas=pygame.Surface((320,180));canvas.fill((5,14,20))
def to_local(key):
    c=pygame.Surface((152,154)) if False else None
    # Save sprites through a temporary fake drawing target in world coordinates.
    tmp=pygame.Surface((320,180),pygame.SRCALPHA)
    if key=='turso':G['turso_draw'](tmp,0,0,195,154,120,70,0,0,False,False)
    elif key in ('hiisi','tytti'):
        p={'hiisi':G['hiisi_frame']('idle',0,False,False,False),'tytti':G['tytti_frame']('idle',0,False,False,False)}[key]
        tmp.blit(p,(120-p.get_width()//2,148-p.get_height()))
    elif key=='louhi':
        p=G['louhi_frame']('windup',0,False,1);tmp.blit(p,(120-p.get_width()//2,155-p.get_height()//2+23))
    else:
        po={'joukahainen':'idle','ahti':'attack','aino':'maiden','vellamo':'windup'}[key]
        p=G['newboss_frame'](key,po,1,0);tmp.blit(p,(123-p.get_width()//2,155-p.get_height()))
    r=tmp.get_bounding_rect();return tmp.subsurface(r).copy()
names=['hiisi','turso','tytti','louhi','joukahainen','ahti','aino','vellamo']
labels=['HIISI','IKU-TURSO','TYTTI','LOUHI','JOUKAHAINEN','AHTI','AINO','VELLAMO']
width=1280;cellw=320;cellh=360;out=pygame.Surface((width,cellh*2));out.fill((9,20,30))
for i,key in enumerate(names):
    col=i%4;row=i//4;x=col*cellw;y=row*cellh;cx=x+cellw//2
    out.fill((19,36,50),(x+7,y+7,cellw-14,cellh-14))
    out.fill((36,65,80),(x+9,y+9,cellw-18,2))
    spr=to_local(key);fac=min(2.0,272/spr.get_height(),270/spr.get_width());dim=(round(spr.get_width()*fac),round(spr.get_height()*fac))
    out.blit(pygame.transform.scale(spr,dim),(cx-dim[0]//2,y+300-dim[1]))
    img=G['PixelFont'](tall=True,scale=2).render(labels[i],False,(218,228,211));out.blit(img,img.get_rect(center=(cx,y+323)))
    if True:
        tag='ALKUPERAISET POMOT' if row==0 else 'VELLAMO 1.3.1'
pygame.image.save(out,'screenshots/131_boss_lineup.png')
# Padded versions: confirms the four bosses and maiden occupy their full 192x160 sheet.
for key in ('joukahainen','ahti','aino','vellamo'):
    G['newboss_frame'](key,'maiden' if key=='aino' else 'windup',1,0)
print('lineup saved',width,cellh*2)
