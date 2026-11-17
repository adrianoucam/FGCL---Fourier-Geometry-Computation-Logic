"""Dependency-light classification metrics with explicit undefined values."""
import numpy as np

def classification_metrics(y_true, scores, classes):
    y=np.asarray(y_true,dtype=int);p=np.asarray(scores,dtype=float)
    if p.shape!=(len(y),len(classes)):raise ValueError('score dimensions mismatch')
    if not np.isfinite(p).all():raise ValueError('nonfinite scores')
    pred=p.argmax(axis=1)
    out={'accuracy':float(np.mean(pred==y)), 'macro_f1':None, 'per_class':{}, 'roc_auc_ovr_macro':None}
    f1s=[];aucs=[]
    for i,name in enumerate(classes):
        tp=int(np.sum((y==i)&(pred==i)));fp=int(np.sum((y!=i)&(pred==i)));fn=int(np.sum((y==i)&(pred!=i)))
        precision=tp/(tp+fp) if tp+fp else 0.
        recall=tp/(tp+fn) if tp+fn else 0.
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.
        f1s.append(f1)
        positive=p[y==i,i];negative=p[y!=i,i]
        auc=None
        if len(positive) and len(negative):
            # Average ranks with tie groups, O(n log n), NumPy-only.
            _, inverse, counts = np.unique(p[:,i], return_inverse=True, return_counts=True)
            ends = np.cumsum(counts)
            ranks = (ends - (counts-1)/2)[inverse]
            auc=float((ranks[y==i].sum()-len(positive)*(len(positive)+1)/2)/(len(positive)*len(negative)))
            aucs.append(auc)
        out['per_class'][name]={'precision':precision,'recall':recall,'f1':f1,'support':int(np.sum(y==i)),'auc':auc}
    out['macro_f1']=float(np.mean(f1s));out['roc_auc_ovr_macro']=float(np.mean(aucs)) if aucs else None
    return out

def bootstrap_delta(y_true, clean, altered, classes, groups, iterations=200, seed=42):
    """Paired cluster bootstrap of accuracy difference; groups = video IDs."""
    y=np.asarray(y_true);a=np.asarray(clean);b=np.asarray(altered);g=np.asarray(groups)
    if not(len(y)==len(a)==len(b)==len(g)):raise ValueError('length mismatch')
    unique=np.unique(g);rng=np.random.default_rng(seed);samples=[]
    for _ in range(iterations):
        chosen=rng.choice(unique,len(unique),replace=True)
        ids=np.concatenate([np.flatnonzero(g==u) for u in chosen])
        samples.append(float(np.mean(b[ids].argmax(1)==y[ids])-np.mean(a[ids].argmax(1)==y[ids])))
    return {'delta_accuracy':float(np.mean(b.argmax(1)==y)-np.mean(a.argmax(1)==y)),
            'ci95_cluster_bootstrap':[float(v) for v in np.percentile(samples,[2.5,97.5])],
            'bootstrap_iterations':iterations,'groups':len(unique)}
