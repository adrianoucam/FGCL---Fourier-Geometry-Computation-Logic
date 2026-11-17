"""SAT stress generator: planted 3-SAT; not guaranteed hard or UNSAT."""
import numpy as np

def planted_3sat(n_vars=20,n_clauses=85,seed=0,clustered=False):
    if n_vars<3 or n_clauses<1:raise ValueError('n_vars >=3, n_clauses >=1')
    rng=np.random.default_rng(seed);assignment=rng.integers(0,2,size=n_vars).astype(bool)
    clauses=[]
    for _ in range(n_clauses):
        if clustered:
            center=int(rng.integers(0,n_vars)); pool=np.array([(center+i)%n_vars for i in range(min(n_vars,7))])
        else:pool=np.arange(n_vars)
        ids=rng.choice(pool,size=3,replace=False)
        signs=rng.choice([-1,1],size=3)
        clause=tuple(int((i+1)*s) for i,s in zip(ids,signs))
        if not any((lit>0)==assignment[abs(lit)-1] for lit in clause):
            j=int(rng.integers(0,3));lit=clause[j];clause=tuple(-v if k==j else v for k,v in enumerate(clause))
        clauses.append(clause)
    return clauses,assignment

def validate(clauses,assignment):
    return all(any((lit>0)==bool(assignment[abs(lit)-1]) for lit in clause) for clause in clauses)

def dimacs(clauses,n_vars):
    return f'p cnf {n_vars} {len(clauses)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in clauses)
