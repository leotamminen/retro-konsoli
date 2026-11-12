from lib import *
import time,hashlib
before={}
for ci in (0,6,10,17,20,23,24,26,29,33):
 t=time.perf_counter();s=G['render_chunk'](ci,G['World']());before[ci]=(pygame.image.tostring(s,'RGBA'),time.perf_counter()-t);print(ci,before[ci][1])
import pickle
pickle.dump(before,open('artifacts/chunks_pre.pkl','wb'))
