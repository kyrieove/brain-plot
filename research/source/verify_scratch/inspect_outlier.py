from pathlib import Path
import numpy as np, json
cache=Path(r"D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\.cache\source\5869447f")
conds=["Hmet","Hlit","Hrep","Lmet","Llit","Lrep"]
rows=[]
for p in sorted(cache.glob("sub*.npz"),key=lambda x:int(x.stem[3:])):
    sid=p.stem
    if sid=="sub27": continue
    with np.load(p,allow_pickle=True) as z:
        cov=z["cov_data"]
        rows.append((sid,float(np.sqrt(np.diag(cov).mean())*1e6),float(np.median(np.sqrt(np.diag(cov)))*1e6),z["evoked_data"],list(z["ch_names"]),np.array(z["nave"])))
sub33=next(x for x in rows if x[0]=="sub33")
print("noise_cov_rms_uV median/max/sub33",np.median([x[1] for x in rows]),max(x[1] for x in rows),sub33[1])
print("noise_cov_median_channel_uV median/sub33",np.median([x[2] for x in rows]),sub33[2])
for ci,c in enumerate(conds):
    a=np.abs(sub33[3][ci,:,80:101])*1e6
    per=a.max(axis=1)
    inds=np.argsort(per)[-5:][::-1]
    print(c,"n",sub33[5][ci],"peak chs",[(sub33[4][i],round(float(per[i]),2)) for i in inds],"mean channel peak",round(float(per.mean()),3),"ch peak ratio",round(float(per.max()/np.median(per)),2))


