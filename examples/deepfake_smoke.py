"""Runs without PyTorch; a toy predictor, not a trained deepfake detector."""
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from fgcl.deepfake import evaluate_folder
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'data'
 for cls,level in [('original',40),('FaceSwap',200)]:
  (root/cls).mkdir(parents=True)
  Image.fromarray(np.full((32,32,3),level,dtype=np.uint8)).save(root/cls/'sample.png')
 def toy(x):
  score=float(x.mean());return ('FaceSwap' if score>.5 else 'original',max(score,1-score))
 print(evaluate_folder(root,toy,Path(tmp)/'out'))
