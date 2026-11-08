def map_y(s,i):
    return 15+i*18 if s.save and s.save.get('vellamo_unlocked') and s.save.get('vellamo_visited') else 17+i*39

def dr_map_fog(s):
    s.build_map();c=s.canvas;s.msgs.clear()
    if s.save is not None:s.draw_play_scene()
    c.blit(s.dimmer,(0,0));c.fill((10,8,14),(0,0,W,H))
    s.text(tr('m_map'),W//2,7,(255,225,150),s.font)
    vis,front=s.map_known();compact=bool(s.save and s.save.get('vellamo_unlocked') and s.save.get('vellamo_visited'))
    for i,(nm,a,b,surf,sil) in enumerate(s.mapimg):
        newrow=nm in ('ranta','syvanne','katedraali');y=map_y(s,i);x=(W-surf.get_width())//2
        if compact:
            surf=pygame.transform.scale(surf,(surf.get_width(),22));sil=pygame.transform.scale(sil,(surf.get_width(),22))
        known=any(a<=cx*MAP_CW+MAP_CW-1 and cx*MAP_CW<b for cx,cy in vis)
        pygame.draw.rect(c,(18,16,24) if known else (10,8,14),(x-1,y-1,surf.get_width()+2,surf.get_height()+2))
        for cx in range(a//MAP_CW,(b-1)//MAP_CW+1):
            for cy in range((ROWS+MAP_CH-1)//MAP_CH):
                src=surf if (cx,cy) in vis else (sil if not newrow and (cx,cy) in front else None)
                if src is None:continue
                t0=max(a,cx*MAP_CW);t1=min(b,cx*MAP_CW+MAP_CW)
                r=pygame.Rect((t0-a)*2,int(cy*MAP_CH*surf.get_height()/ROWS),(t1-t0)*2,int(min(MAP_CH,ROWS-cy*MAP_CH)*surf.get_height()/ROWS))
                if r.w>0 and r.h>0:c.blit(src,(x+r.x,y+r.y),r)
        for k,ar in ARENAS.items():
            if a<=ar['x0']<b:
                if 'arena:'+k not in s.mapseen:
                    h=max(2,int((ar['ground']-ar['y0']+2)*surf.get_height()/ROWS))
                    c.fill((10,8,14),(x+(ar['x0']+1-a)*2,y+int(ar['y0']*surf.get_height()/ROWS),(ar['x1']-ar['x0']-1)*2,h));continue
                done=k in s.save['bosses'];mx=x+(ar['x0']+10-a)*2;my=y+int((ar['y0']+6)*surf.get_height()/ROWS)
                pygame.draw.rect(c,(90,90,100) if done else (220,60,60),(mx-2,my-2,5,5),1);c.fill((90,90,100) if done else (220,60,60),(mx,my,1,1))
        for bid,tx in BONFIRES.items():
            if a<=tx<b and bid in s.save['seen']:
                by=floor_row(tx,BF_START[bid]);c.fill((255,170,70),(x+(tx-a)*2-1,y+int((by-3)*surf.get_height()/ROWS),4,3));c.fill((255,235,150),(x+(tx-a)*2,y+int((by-3)*surf.get_height()/ROWS),2,1))
        for p in s.players:
            tx=p.x/TILE
            if a<=tx<b and (s.t_ui//15)%2==0:
                col=(255,255,255) if p.idx==0 else P2_TINT[p.cls];c.fill(col,(x+int((tx-a)*2)-1,y+int(p.y/TILE*surf.get_height()/ROWS)-2,3,3))
        if known:s.text(tr('area_'+nm),x+3,y-5,(220,215,200),s.tiny,'l')
    s.text(tr('map_legend'),W//2,H-6,(170,170,180),s.tiny)
GameUI.dr_map=dr_map_fog
