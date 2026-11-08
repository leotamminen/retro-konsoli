"""Identical pad semantics for title, true-ending offer, reveal and new ending."""
def new_title_items(s):
    items=[]
    save=s.title_save
    if save is not None:
        items.append(('cont',tr('m_continue')))
        if save.get('vellamo_unlocked') and save.get('done') and not save.get('vellamo_visited'):
            items.append(('vellamo',tr('vel_choice')))
        if save.get('ng_ready'):
            items.append(('ng',tr('m_ng')))
    return items+[('new',tr('m_new')),('info',tr('m_info')),('settings',tr('m_settings')),('quit',tr('m_quit'))]
GameUI.title_items=new_title_items
def up_title(s):
    result=s.menu_in();items=s.title_items();index=s.sel('title',len(items),result);key=items[index][0]
    if result['back']:s.menu_i['title']=len(items)-1
    if not result['ok']:return
    sfx('confirm',.7);s._title_commit_device=getattr(s,'last_accept_pad',None)
    if key=='vellamo':
        committing_pad=s.last_pad
        s.start_session(s.title_save,committing_pad);s.enter_vellamo()
    elif key=='cont':s.begin_session(s.title_save)
    elif key=='ng':s.begin_ng(s.title_save)
    elif key=='info':s.state_name='info';s.info_t=0
    elif key=='new':
        if s.title_save:s.confirm_i=1;s.menu_i['confirm']=1;s.state_name='confirm'
        else:s.new_game_flow()
    elif key=='settings':s.open_settings('title')
    elif key=='quit':s.running=False
GameUI.up_title=up_title
def up_true_end(s):
    result=s.menu_in();s.true_t+=1
    if s.true_page>=4:
        index=s.sel('vel_offer',2,result)
        if result['ok']:
            if index==0:s.save['vellamo_unlocked']=True;s.save_game();s.enter_vellamo()
            else:s.back_to_title()
    elif (result['ok'] or result['any']) and s.true_t>30:s.true_page+=1;s.true_t=0
GameUI.up_true_ending=up_true_end
def up_reveal(s):
    result=s.menu_in();s.reveal_t+=1
    if (result['ok'] and s.reveal_t>1) or s.reveal_t>240:s.state_name='play';s.start_boss('vellamo')
GameUI.up_aino_reveal=up_reveal
def up_ending(s):
    result=s.menu_in()
    if result['ok'] or result['back'] or s.vel_end_t>500:s.back_to_title()
GameUI.up_vellamo_ending=up_ending
GameUI.up_vellamo_arrival=lambda s:(setattr(s,'state_name','play'),pygame.event.clear(),s.prewarm_vellamo())
def dr_arrival(s):
    s.canvas.fill((4,15,26));s.text(tr('area_ranta'),160,53,(158,220,200),s.big)
    pygame.draw.line(s.canvas,(99,190,173),(36,143),(284,143),1)
GameUI.dr_vellamo_arrival=dr_arrival
