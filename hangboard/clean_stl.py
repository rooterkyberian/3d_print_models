"""Weld STL vertices at 0.00001 mm and remove collapsed export triangles."""
import numpy as np
from pathlib import Path
def clean(path):
 path=Path(path);raw=path.read_bytes()
 dtype=np.dtype([('normal','<f4',3),('v','<f4',(3,3)),('attr','<u2')])
 records=np.frombuffer(raw,dtype=dtype,offset=84).copy()
 # The unit is mm; this is far below the 0.04 mm tessellation tolerance.
 v=np.round(records['v'].astype(float),5).astype('float32')
 cr=np.cross(v[:,1].astype(float)-v[:,0],v[:,2].astype(float)-v[:,0])
 ln=np.linalg.norm(cr,axis=1);keep=ln>2e-10
 result=records[keep].copy();result['v']=v[keep];result['normal']=(cr[keep]/ln[keep,None]).astype('float32')
 path.write_bytes(raw[:80]+len(result).to_bytes(4,'little')+result.tobytes())
 print('STL cleanup:',len(records)-len(result),'collapsed triangles removed;',len(result),'retained',flush=True)
if __name__=='__main__':clean(Path(__file__).parent/'hangboard.stl')
