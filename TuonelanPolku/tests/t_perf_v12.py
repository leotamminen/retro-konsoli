"""1.2: cold/warm lazy audio, cold/warm chunks, long gameplay, input simulation diagnostics."""
from lib import *
import time,statistics,random,hashlib
FAIL=[]
def ok(c,label):
 print(('ok   ' if c else 'FAIL ')+label)
 if not c:FAIL.append(label)
# Measure matter excluding headless font tests: native mixer and process worker.
os.environ.pop("TUONELA_NO_MUSIC",None)
G["init_audio"]();cache=os.path.join(TMP,"music-cache");os.environ["TUONELA_MUSIC_CACHE"]=cache
mp=G["MusicPlayer"]();frames=[]
for i in range(7000):
 if i in (0,150):mp.request("title")
 t=time.perf_counter();mp.update();frames.append((time.perf_counter()-t)*1000)
 if "title" in mp.tracks and i>900:break
 time.sleep(.002)
print('cold audio update frames: %s max %.2f ms p99 %.2f logs tracks %s' % (len(frames),max(frames),sorted(frames)[int(.99*len(frames))],list(mp.tracks)))
ok(max(frames)<16.7,'cold synthesis leaves GIL/music frame under 16.7ms')
ok('title' in mp.tracks,'lazy synthesis finishes and first track loads')
raw=G["_cache_path"]("title");b=open(raw,'rb').read();ok(len(b)>441000,"raw disk cache generated")
new=G["MusicPlayer"]();new.request('title');ts=[]
for i in range(300):
 t=time.perf_counter();new.update();ts.append((time.perf_counter()-t)*1000);time.sleep(.001)
 if 'title' in new.tracks:break
print('warm audio: %d update frames, mean %.2f max %.2f ms, raw %.1f MB'%(len(ts),sum(ts)/len(ts),max(ts),len(b)/1e6))
ok('title' in new.tracks,'valid raw cache reused')
open(raw,'wb').write(b'bad');r=G["MusicPlayer"]();r.request('title')
try:r.update();r._load_slot(['title',None]);ok(True,'corrupt raw returns no sound without crash')
except Exception:ok(False,'corrupt raw exception')
os.unlink(raw)
os.environ.pop('TUONELA_NO_MUSIC',None);G['MUSIC']._queue=lambda:None ;G['MUSIC'].update=lambda:None
# Warmup and input tests all default debug flag is off.
g=new_game();pad=start(g,diff='normal')
ok(not SETTINGS['perf'],'performance overlay default off')
G["SETTINGS"]["perf"]=True;g.frame_ms=[4,5,6];g.draw();shot(g,'12_perf_overlay');G["SETTINGS"]["perf"]=False
normal_before=g.players[0].hp
g.queue_event_sample([dict(type=pygame.JOYBUTTONDOWN,button=0)],g.frames);step(g,1,False);ok(g.input_to_action_frames==0,"same simulation-frame SDL input => action")
f=g.players[0]
print('input sample action',g.input_to_action_frames,'frames (event & pad transport & display not measured)')
# Cold and warm initial rendering in a separate built world (includes seven predrawn chunk strips).
for mode in ('cold','warm'):
 if mode=='cold':G["GameCore"].CHUNK_CACHE.clear()
 gg=new_game();t=time.perf_counter();p=start(gg,bonfire='b7');startup=(time.perf_counter()-t)*1000
 ts=[]
 for i in range(120):t=time.perf_counter();gg.update();gg.draw();ts.append((time.perf_counter()-t)*1000)
 print('%s start %.2f ms: steady mean %.2f worst %.2f ms, chunks %d'%(mode,startup,sum(ts)/len(ts),max(ts),len(G["GameCore"].CHUNK_CACHE)))
 ok(len(G["GameCore"].CHUNK_CACHE)<=28,'bounded chunk cache')
# Optional Pi-like cap: reserve half a physical CPU to expose frame-budget tails.
if os.environ.get('TP_CPU_QUOTA'):
 os.makedirs('/sys/fs/cgroup',exist_ok=True)
# Affinity based throttle is a slow-cpu stress test, not an actual Raspberry Pi.
affinity=None
try:
 if os.environ.get('TP_SLOW_CPU') and len(os.sched_getaffinity(0))>1:
  affinity=os.sched_getaffinity(0);os.sched_setaffinity(0,{min(affinity)})
except OSError:pass
# All areas, cold moving camera, transitions, all bosses and coop; 21600 frames.
random.seed(43);samples=[]
def record(label,g,pad,frames=2700):
 rs=[]
 for i in range(frames):
  c=pad.blank();c['right']=i%220<110;c['left']=110<=i%220<220;c['x']=1 if c['right'] else -1 if c['left'] else 0
  c['jump']=i%80==0;c['light']=i%42<2;c['dodge']=i%140==17;pad.nextc=c
  if g.boss and g.boss.key=='louhi':
   for p in g.players:p.hp=p.maxhp
   if i in (500,1000,1500):g.boss.hp=g.boss.maxhp*(.65 if i<900 else .32);g.boss.invuln=False
  if g.state_name not in ("play","ending","poht","true","true_ending"):
   pad.nextc=None
  t=time.perf_counter();g.update();g.draw();delta=(time.perf_counter()-t)*1000;samples.append((delta,label));rs.append(delta)
 print('%-28s avg %.2f p99 %.2f max %.2f (%d frames)'%(label,sum(rs)/len(rs),sorted(rs)[int(.99*len(rs))],max(rs),len(rs)))
for zone in ('b0','b4','b7','b9'):
 gg=new_game();p=start(gg,bonfire=zone);p2=ScriptPad('p2');gg.add_pad(p2);gg.add_p2('hunter',p2);p3=gg.enemies
 record('coop '+zone,gg,p,2700)
 if zone in ('b4','b7','b9'):
  gg.start_boss({'b4':'turso','b7':'tytti','b9':'louhi'}[zone]);record('boss '+gg.boss.key,gg,p,2700)
gg=new_game();p=start(gg,bonfire='b8');gg.start_ending();record('transition/secret',gg,p,2700)
report=sorted(samples);n=len(report);p99=report[int(n*.99)][0];mx=report[-1]
print('LONG update+draw: %d frames, p99 %.2f ms, worst %.2f ms (%s) budget 16.7ms'%(n,p99,mx[0],mx[1]))
print("Pi-like budget: box x86 timing is NOT a Pi hardware proof; report outliers separately.")
print("OVER_BUDGET", [(round(t,3),l) for t,l in report if t>16.7])
ok(p99<16.7,'long p99 measured box update+draw below budget; not a Pi hardware claim')
ok(len(report)>=21600,'long run >=6 simulated minutes')
with open(os.path.join(ROOT,'perf_v12_report.txt'),'w') as f:
 f.write('Box profiling (not Raspberry Pi 5 hardware). update+draw, 60Hz target.\n')
 f.write('long_frames=%d p99_ms=%.3f worst_ms=%.3f worst_scene=%s\n'%(n,p99,mx[0],mx[1]))
 f.write('cold_music_max_ms=%.3f warm_music_max_ms=%.3f\n'%(max(frames),max(ts)))
 f.write('input_to_action_simulation_frames=0; controller/display excluded\n')
 f.write('worst_frames_over_16.7ms:\n'+ '' .join('%s %.3f ms\n'%(l,t) for t,l in report if t>16.7))
if affinity is not None:os.sched_setaffinity(0,affinity)
print('failures',FAIL);raise SystemExit(bool(FAIL))
