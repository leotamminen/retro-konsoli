"""Complete Finnish/English UI strings, replacing all draft/HACK text."""
for key,fi,en in [
('real_1','Sampo ei ollut osasi palkinto. Palkintosi on valo, jonka annoit kansalle.','The Sampo was not your prize. Your prize is the light you returned to the people.'),
('area_pohjola','Pohjola','Pohjola'),('area_ranta','Aallon ranta','The Shimmering Shore'),('area_syvanne','Vellamon syvänteet','Vellamo’s Depths'),('area_katedraali','Veden alle vajonnut temppeli','The Drowned Cathedral'),
('boss_joukahainen','Joukahainen, kostava laulaja','Joukahainen, Avenging Singer'),('boss_ahti','Ahti, vesien herra','Ahti, Lord of Waters'),('boss_aino','Aino, meren neito','Aino, Maid and Sister of the Sea'),('boss_vellamo','Vellamo, veden emäntä','Vellamo, Mistress of Waters'),
('vel_offer','Vellamon valtakunnan portti on avautunut. Aino odottaa syvyyksissä.','Passage to Vellamo’s realm has opened. Aino waits in the depths.'),
('vel_choice','Jatka Vellamon valtakuntaan','Continue to Vellamo’s realm'),('vel_stay','Päävalikkoon','Main menu'),
('vel_ending','Viimeinen laulu vaimeni. Aino nousi laineilta kuultona, eikä Vellamo enää pidättänyt häntä. Nimetön vaeltaja saattoi hänet rannalle, pois vanhasta kohtalostaan. Aino sai vihdoin valita oman tiensä.','The singing fell silent. Aino rose from the waves, free. Vellamo could detain her no longer. The wanderer led her to shore, away from her old fate. Aino was finally free to choose her own path.'),
('aino_calm','Aino rauhoittui. Meren uhri ei ollut vihollinen. Hänen tiensä vapauteen oli vihdoin selvä.','Aino calmed. The sea had not made her an enemy; her path to freedom was at last clear.'),
('v_reveal','VELLAMO: "Et vie Ainoa minun merestäni!"','VELLAMO: "You shall not take Aino from my sea!"'),
('end_stats','Aika: %s   Kuolemat: %d   Taso: %d','Time: %s   Deaths: %d   Level: %d'),
('revel_a','Aino pysähtyi. Hänen vapautensa oli lähellä.','Aino stopped. Her freedom was within reach.'),
('revel_v','Vellamo, veden emäntä: "Et vie Ainoa minun merestäni!"','Vellamo, Mistress of Waters: "You shall not take Aino from my sea!"')]:_t(key,fi,en)
def draw_reveal(s):
    c=s.canvas;c.fill((4,14,20));t=s.reveal_t
    spr=newboss_frame('aino','maiden',1,t//20);c.blit(spr,(64,105))
    for i,line in enumerate(wrap(s.font,tr('revel_v' if t>70 else 'revel_a'),290)):
        if i<3:s.text(line,160,13+i*10,(150,218,205))
    if t>50:
        sp=newboss_frame('vellamo','reveal',1,t//16);sp=pygame.transform.flip(sp,True,False);c.blit(sp,(169,65))
    for i in range(3):
        x=17+i*108
        pygame.draw.polygon(c,(9,29,39),[(x,0),(x+7,0),(x+46,169),(x+31,169)])
    for i in range(9):
        x=18+i*37;y=24+(i*31)%135
        pygame.draw.circle(c,(42,84,101),(x,y),1,1)
    pygame.draw.arc(c,(39,91,111),(48,132,83,16),.2,2.9,1)
    pygame.draw.arc(c,(35,77,97),(145,143,129,11),.2,2.9,1)
    s.rich(tr('hint_next'),160,171,(180,210,216),s.tiny)
end_stats_fn=lambda sv:tr('end_stats',fmt_time(sv['time']),sv['deaths'],1+sum(sv['stats'].values()))
def draw_true_ending(s):
    c=s.canvas;c.fill((7,10,19));pg=s.true_page
    if pg<3:
        for i,line in enumerate(wrap(s.font,tr('real_%d'%pg),260)):s.text(line,160,70+i*15-len(wrap(s.font,tr('real_%d'%pg),260))*5,(220,222,209))
    else:
        s.text(tr('real_title'),160,42,(245,221,158),s.font);s.text(end_stats_fn(s.save),160,86,(245,221,158),s.font)
    if pg==4:s.menu_box([tr('vel_choice'),tr('vel_stay')],s.menu_i.get('vel_offer',0),cy=150,minw=170)
    else:s.rich(tr('hint_next'),160,156,(150,170,180),s.tiny)
def draw_vellamo_ending(s):
    s.canvas.fill((3,20,34));s.text(tr('boss_vellamo'),160,13,(169,230,217),s.mid)
    for i,line in enumerate(wrap(s.font,tr('vel_ending'),270)):s.text(line,160,43+i*12,(200,238,224))
    s.text(end_stats_fn(s.save),160,126,(243,211,150),s.font);s.rich(tr('hint_next'),160,163,(167,207,204),s.tiny)
for b,nm,en in [('b10','Aallon ranta','Shimmering Shore'),('b11','Syvänteen tulentekopaikka','Depths Bonfire'),('b12','Temppelin tulipaikka','Cathedral Bonfire'),('b13','Vapauden ranta','Shore of Freedom')]:_t('bf_'+b,nm,en)
