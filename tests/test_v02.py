import csv,json,tempfile,unittest
from pathlib import Path
import numpy as np
from fgcl.spectral import spectral_features,apply_variant,match_mse
from fgcl.metrics import classification_metrics,bootstrap_delta
from fgcl.benchmark import evaluate_manifest,load_manifest
from fgcl.xai import cosine_stability

class V02Tests(unittest.TestCase):
 def test_features(self):
  x=np.random.default_rng(0).random((16,20,3))
  f=spectral_features(x);self.assertEqual(f.shape,(24,));self.assertTrue(np.isfinite(f).all())
 def test_variants(self):
  x=np.random.default_rng(1).random((24,32,3))
  for method in ('cairo_positive','random_positive','lowpass','highpass','identity'):
   y=apply_variant(x,method,.3,seed=4);self.assertEqual(y.shape,x.shape);self.assertTrue(np.isfinite(y).all())
  y,s,mse,ok=match_mse(x,'lowpass',.001);self.assertTrue(ok);self.assertAlmostEqual(mse,.001,delta=1e-5)
 def test_metrics(self):
  y=[0,0,1,1];p=np.array([[.9,.1],[.7,.3],[.2,.8],[.1,.9]])
  r=classification_metrics(y,p,['real','fake']);self.assertEqual(r['macro_f1'],1.);self.assertEqual(r['roc_auc_ovr_macro'],1.)
  b=bootstrap_delta(y,p,p,['real','fake'],['a','a','b','b'],iterations=30);self.assertEqual(b['delta_accuracy'],0.)
 def test_manifest_benchmark(self):
  from PIL import Image
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);rows=[]
   for i in range(4):
    cls='real' if i<2 else 'fake';path=root/f'{i}.png';Image.fromarray(np.full((20,20,3),30 if i<2 else 220,dtype=np.uint8)).save(path)
    rows.append({'path':path.name,'label':cls,'group':f'video{i//2}','split':'test'})
   man=root/'manifest.csv'
   with man.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['path','label','group','split']);w.writeheader();w.writerows(rows)
   def predictor(x):return np.array([.9,.1]) if x.mean()<.5 else np.array([.1,.9])
   result=evaluate_manifest(man,predictor,root/'out',['real','fake'],methods=['lowpass'],limit=4)
   self.assertEqual(result['methods']['clean']['accuracy'],1.)
   self.assertTrue((root/'out'/'predictions.csv').exists())
   with (root/'out'/'predictions.csv').open() as f:
    self.assertEqual(len(list(csv.DictReader(f))),8)
 def test_reject_train(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'m.csv';p.write_text('path,label,group,split\nx,real,v1,train\n')
   with self.assertRaises(ValueError):load_manifest(p)
 def test_xai(self):self.assertAlmostEqual(cosine_stability([1,2],[1,2]),1.)
if __name__=='__main__':unittest.main()
