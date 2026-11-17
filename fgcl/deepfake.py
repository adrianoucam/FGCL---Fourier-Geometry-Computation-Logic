"""Image-level evaluation of existing PyTorch classifiers; no training or fabricated accuracy."""
import csv,json,time
from pathlib import Path
import numpy as np
from .core import spectral_mask,perturb_image

def evaluate_folder(root, predictor, out_dir, strength=.25, seed=42, limit=None):
    """predictor accepts float RGB HWC [0,1], returns (class_name, confidence).
    Directory: root/<class>/*.png|jpg|jpeg|webp. Splits must be pre-established externally.
    """
    from PIL import Image
    root=Path(root);out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    classes=sorted(p.name for p in root.iterdir() if p.is_dir())
    if not classes:raise ValueError('No class directories')
    rows=[]
    for cls in classes:
        paths=sorted(p for p in (root/cls).rglob('*') if p.suffix.lower() in ('.jpg','.jpeg','.png','.webp'))
        for path in paths[:limit] if limit else paths:
            x=np.asarray(Image.open(path).convert('RGB'),dtype=np.float32)/255.
            mask=spectral_mask(x.shape[:2],seed=seed)
            y=perturb_image(x,mask,strength)
            t=time.perf_counter();clean,pc=predictor(x);changed,pp=predictor(y);dt=time.perf_counter()-t
            rows.append(dict(path=str(path),label=cls,clean_pred=clean,perturbed_pred=changed,clean_conf=float(pc),perturbed_conf=float(pp),flipped=int(clean!=changed),mse=float(np.mean((x-y)**2)),seconds=dt))
    if not rows:raise ValueError('No images found')
    with (out/'predictions.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    report={'samples':len(rows),'flip_rate':float(np.mean([r['flipped'] for r in rows])),'mean_mse':float(np.mean([r['mse'] for r in rows])),'clean_accuracy':float(np.mean([r['clean_pred']==r['label'] for r in rows])),'perturbed_accuracy':float(np.mean([r['perturbed_pred']==r['label'] for r in rows])),'strength':strength,'seed':seed,'note':'Accuracy assumes predictor class labels exactly match folder names; group video identities to avoid leakage.'}
    (out/'metrics.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report

def torch_predictor(model, class_names, device='cpu', image_size=224, normalize=True):
    """Adapter for torch.nn.Module returning class logits; checkpoint loading is caller responsibility."""
    import torch
    from PIL import Image
    from torchvision.transforms import functional as F
    model=model.to(device).eval()
    def predict(x):
        im=Image.fromarray((np.clip(x,0,1)*255).astype('uint8'))
        t=F.to_tensor(F.resize(im,[image_size,image_size]))
        if normalize:t=F.normalize(t,[.485,.456,.406],[.229,.224,.225])
        with torch.inference_mode():
            logits=model(t.unsqueeze(0).to(device));logits=logits.logits if hasattr(logits,'logits') else logits
            prob=torch.softmax(logits,dim=1)[0];idx=int(prob.argmax())
        return class_names[idx],float(prob[idx])
    return predict
