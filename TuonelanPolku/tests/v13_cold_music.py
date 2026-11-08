from lib import *
import os,tempfile,time
os.environ['TUONELA_NO_MUSIC']='' ;G['init_audio']();os.environ['TUONELA_MUSIC_CACHE']=os.path.join(TMP,'new-cold-cache')
for name in ['ranta','syvanne','katedraali','joukahainen','joukahainen2','ahti','ahti2','aino','aino2','aino3','vellamo','vellamo2','vellamo3']:
 mp=G['MusicPlayer']();times=[]
 for k in range(2000):
  t=time.perf_counter();mp.request(name);mp.update();times.append((time.perf_counter()-t)*1000)
  if name in mp.tracks:break
  time.sleep(.002)
 path=G['_cache_path'](name)
 print(name,'process',mp.process,'buffered',name in mp.tracks,'ms_max',round(max(times),3),'p99',round(sorted(times)[int(len(times)*.99)],3),'disk_bytes',os.path.getsize(path) if os.path.exists(path) else 0,flush=True)
 assert name in mp.tracks, 'fork music did not load'
