from pathlib import Path
import numpy as np
cache=Path(r"D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\.cache\source\5869447f")
rows=[]
for p in sorted(cache.glob("sub*.npz"),key=lambda x:int(x.stem[3:])):
 if p.stem=="sub27": continue
 with np.load(p,allow_pickle=True) as z:
  e=np.linalg.eigvalsh(z["cov_data"]); e=e[e>e.max()*1e-10]
  rows.append((p.stem,len(e),float(e.min()),float(e.max()),float(np.median(e)),float(e.max()/e.min())))
for ix,name in ((1,"rank"),(2,"min"),(3,"max"),(4,"median"),(5,"condition")):
 v=[r[ix] for r in rows]; q=next(r[ix] for r in rows if r[0]=="sub33"); print(name,"sub33",q,"median",np.median(v),"min",np.min(v),"max",np.max(v))
print("lowest min eigen:",sorted(rows,key=lambda r:r[2])[:5])
