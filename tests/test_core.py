import unittest
import numpy as np
from fgcl.core import spectral_mask,perturb_image,hypercube_projection,projected_lattice,occupancy,stress_curve
from fgcl.sat import planted_3sat,validate,dimacs
class Tests(unittest.TestCase):
 def test_mask(self):
  m=spectral_mask((32,48),seed=2);self.assertTrue(np.all(m>=0));self.assertLessEqual(m.max(),1.000001)
  self.assertTrue(np.allclose(m,np.roll(np.roll(m[::-1,::-1],1,axis=0),1,axis=1)))
 def test_identity(self):
  x=np.random.default_rng(1).random((16,20,3));m=spectral_mask(x.shape[:2]);self.assertTrue(np.allclose(perturb_image(x,m,0),x))
 def test_geometry(self):
  self.assertEqual(hypercube_projection(5).shape,(32,2));self.assertEqual(projected_lattice(3,2).shape,(125,2));self.assertEqual(occupancy(hypercube_projection(5))['n'],32)
 def test_scaling(self):self.assertEqual(len(stress_curve([10,100])['R']),2)
 def test_sat(self):
  for clustered in [True,False]:
   clauses,a=planted_3sat(12,40,seed=4,clustered=clustered);self.assertTrue(validate(clauses,a));self.assertIn('p cnf 12 40',dimacs(clauses,12))
if __name__=='__main__':unittest.main()
