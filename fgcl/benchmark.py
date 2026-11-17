"""Group-aware image benchmark. Evaluation only; never trains or loads checkpoints implicitly."""
import csv,hashlib,json,platform,time
from pathlib import Path
import numpy as np
from .spectral import apply_variant,match_mse,spectral_features
from .metrics import classification_metrics,bootstrap_delta

def load_manifest(path):
    """CSV columns path,label,group,split; split must equal test for all rows."""
    path=Path(path)
    with path.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if not rows:raise ValueError('empty manifest')
    for r in rows:
        if not all(r.get(k) for k in ('path','label','group','split')):raise ValueError('manifest needs path,label,group,split')
        if r['split']!='test':raise ValueError('evaluation accepts only split=test; use separate manifests')
        loc=Path(r['path']);r['path']=str(loc if loc.is_absolute() else (path.parent/loc).resolve())
        if not Path(r['path']).is_file():raise FileNotFoundError(r['path'])
    return rows

def evaluate_manifest(manifest,predictor,out_dir,classes,methods=('cairo_positive','random_positive','lowpass','highpass'),strength=.2,target_mse=None,seed=42,limit=None):
    """predictor(image RGB float HWC) -> probability vector in exact classes order."""
    from PIL import Image
    rows=load_manifest(manifest)
    if limit:rows=rows[:limit]
    classes=list(classes)
    if len(set(classes))!=len(classes):raise ValueError('duplicate class names')
    if not set(r['label'] for r in rows)<=set(classes):raise ValueError('manifest labels absent from classes')
    methods=tuple(dict.fromkeys(methods))
    if not methods:raise ValueError('at least one method required')
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    entries=[];all_scores={'clean':[]};all_scores.update({m:[] for m in methods})
    y=[];groups=[];start=time.perf_counter()
    def predict(x):
        p=np.asarray(predictor(x),dtype=float)
        if p.shape!=(len(classes),) or not np.isfinite(p).all() or np.any(p<0) or not np.isclose(p.sum(),1,atol=1e-3):
            raise ValueError('predictor must return normalized class probability vector')
        return p
    for index,r in enumerate(rows):
        x=np.asarray(Image.open(r['path']).convert('RGB'),dtype=np.float32)/255.
        clean=predict(x);all_scores['clean'].append(clean);y.append(classes.index(r['label']));groups.append(r['group'])
        variants={'clean':(x,0.,0.,True)}
        for m in methods:
            if target_mse is None:
                z=apply_variant(x,m,strength,seed+index);mse=float(np.mean((x-z)**2));s=strength;reachable=True
            else:z,s,mse,reachable=match_mse(x,m,target_mse,seed+index)
            variants[m]=(z,s,mse,reachable)
            all_scores[m].append(predict(z))
        for m,(z,s,mse,reachable) in variants.items():
            score=clean if m=='clean' else all_scores[m][-1]
            entries.append({'path':r['path'],'label':r['label'],'group':r['group'],'method':m,'prediction':classes[int(score.argmax())],
                'confidence':float(score.max()),'scores_json':json.dumps(score.tolist()),'strength':s,'mse':mse,'target_reachable':reachable,
                'spectral_descriptor_json':json.dumps(spectral_features(z).tolist())})
    with (out/'predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=entries[0].keys());w.writeheader();w.writerows(entries)
    report={'version':'0.2.0','classes':classes,'samples':len(rows),'groups':len(set(groups)),
      'methods':{},'config':{'seed':seed,'strength':strength,'target_mse':target_mse,'methods':methods},
      'manifest_sha256':hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
      'elapsed_seconds':time.perf_counter()-start,'python':platform.python_version(),
      'limitations':['Group IDs are user supplied and cannot be independently validated', 'Image MSE is not a perceptual metric', 'AUC is undefined if only one label is present']}
    for m,p in all_scores.items():
        scores=np.asarray(p);item=classification_metrics(y,scores,classes)
        if m!='clean':
            item['paired_delta']=bootstrap_delta(y,all_scores['clean'],scores,classes,groups,iterations=200,seed=seed)
            subset=[e for e in entries if e['method']==m]
            item['mean_mse']=float(np.mean([e['mse'] for e in subset]))
            item['unreachable_targets']=sum(not e['target_reachable'] for e in subset)
            item['flip_rate']=float(np.mean(scores.argmax(1)!=np.asarray(all_scores['clean']).argmax(1)))
        report['methods'][m]=item
    (out/'metrics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    return report
