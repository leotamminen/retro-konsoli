PTEMPO={'ranta': 96, 'syvanne': 78, 'katedraali': 96, 'joukahainen': 108, 'ahti': 112, 'aino': 124, 'vellamo': 132, 'vellamo2': 270, 'joukahainen2': 130, 'joukahainen3': 140, 'ahti2': 132, 'ahti3': 140, 'aino2': 136, 'aino3': 140, 'vellamo3': 140}
def compose_water(name):
    phase=2 if name=='vellamo2' else 1;tempo=PTEMPO.get(name,72)
    bars=48 if name=="vellamo2" else 24;steps=12;bar=round(60/tempo*3/2*RATE/12)*12;total=bars*bar;buf=[0.0]*(total+RATE);rnd=random.Random(name)
    scale=[45,48,50,53,55,57,60,62];cache={};beat=bar//steps
    def toneat(n,pos,amp):
        if n not in cache:cache[n]=_lead_note('reed' if 'aino' in name else 'flute',midi(n),1.5+bars%3,n)
        _mixin(buf,cache[n],pos,amp)
    for b in range(bars):
        root=scale[(b//2+sum(name.encode())%5)%4];pos=b*bar
        if name.startswith('joukahainen'):root=[45,52,48,40][b%4]
        elif name.startswith('ahti'):root=[33,36,40,29][(b//2)%4]
        elif name.startswith('aino'):root=[53,50,57,52][(b//2)%4]
        elif name.startswith('vellamo'):root=[38,39,32,31][(b//2)%4]
        for k in (0,3):
            n=0
            _mixin(buf,C(root,k),pos+k*beat,.055)
        for j in range(steps):
            tt=pos+j*beat
            if j%3==0:_mixin(buf,_V_bd,tt,.14 if b%3 else .2)
            pattern={'ranta':(0,3,6,9),'syvanne':(2,5,8,11),'katedraali':(0,4,7,11),'joukahainen':(1,3,7,10),'ahti':(0,6,9),'aino':(2,7,9,11),'vellamo':(0,3,8,11)}[next(k for k in ('ranta','syvanne','katedraali','joukahainen','ahti','aino','vellamo') if name.startswith(k))]
            if j in pattern:toneat(root+scale[(j+b)%len(scale)]%12+12,tt,.058 if b<4 else .11)
            if b>=bars//2 and j%2==0:_mixin(buf,_V_shaker,tt,.065+.01*(name=='vellamo'))
        time.sleep(.001)
    return [math.tanh(v*1.15)*.75 for v in buf[:total]]
_VC={}
def C(root,k):
    key=(root,k)
    if key not in _VC:_VC[key]=_lead_note('choir',midi(root-(12 if k else 0)),4.5,root)
    return _VC[key]
_V_bd=tone(93,40,.28,.45,'sine');_V_shaker=tone(7000,4000,.045,.15,'noise')
TRACK_ORDER+=tuple(PTEMPO)
for name,tempo in PTEMPO.items():TRACKS[name]={'key':1,'tempo':tempo,'meter':8}
MusicPlayer.LIKELY.update(ranta=['joukahainen'],syvanne=['ahti'],katedraali=['aino'],joukahainen=[],ahti=[],aino=['vellamo'],vellamo=['vellamo2'],vellamo2=[])
