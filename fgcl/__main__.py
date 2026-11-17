import argparse,csv,json
from pathlib import Path
from .core import hypercube_projection,projected_lattice,occupancy,stress_curve
from .sat import planted_3sat,validate,dimacs

def main():
    p=argparse.ArgumentParser(description='FGCL — Fourier, Geometry, Computation & Logic')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('geometry');a.add_argument('--mode',choices=['hypercube','lattice'],default='hypercube');a.add_argument('--dim',type=int,default=12);a.add_argument('--radius',type=int,default=2);a.add_argument('--seed',type=int,default=0);a.add_argument('--out',default='results/geometry')
    a=sub.add_parser('scaling');a.add_argument('--out',default='results/scaling.json')
    a=sub.add_parser('sat');a.add_argument('--vars',type=int,default=20);a.add_argument('--clauses',type=int,default=85);a.add_argument('--seed',type=int,default=0);a.add_argument('--clustered',action='store_true');a.add_argument('--out',default='results/sat')
    a=sub.add_parser('benchmark');a.add_argument('--manifest',required=True);a.add_argument('--out',default='results/benchmark');a.add_argument('--model-module',required=True,help='Python module containing build_model()');a.add_argument('--checkpoint',required=True);a.add_argument('--classes',nargs='+',required=True);a.add_argument('--device',default='cpu');a.add_argument('--methods',nargs='+',default=['cairo_positive','random_positive','lowpass','highpass']);a.add_argument('--strength',type=float,default=.2);a.add_argument('--target-mse',type=float);a.add_argument('--seed',type=int,default=42);a.add_argument('--limit',type=int)
    args=p.parse_args()
    if args.cmd=='geometry':
        points=hypercube_projection(args.dim,args.seed) if args.mode=='hypercube' else projected_lattice(args.dim,args.radius,args.seed)
        out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
        import numpy as np
        np.save(out/'points.npy',points);(out/'metrics.json').write_text(json.dumps(occupancy(points),indent=2))
        print((out/'metrics.json').read_text())
    elif args.cmd=='scaling':
        out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(stress_curve([10,100,1000,10000,100000]),indent=2));print(out)
    elif args.cmd=='benchmark':
        import importlib
        from .adapters import load_state_dict_strict,torch_probability_predictor
        from .benchmark import evaluate_manifest
        module=importlib.import_module(args.model_module)
        model=module.build_model(len(args.classes))
        load_state_dict_strict(model,args.checkpoint)
        predictor=torch_probability_predictor(model,args.classes,device=args.device)
        result=evaluate_manifest(args.manifest,predictor,args.out,args.classes,methods=args.methods,strength=args.strength,target_mse=args.target_mse,seed=args.seed,limit=args.limit)
        print(json.dumps({'samples':result['samples'],'output':args.out},indent=2))
    else:
        clauses,solution=planted_3sat(args.vars,args.clauses,args.seed,args.clustered)
        assert validate(clauses,solution)
        out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
        (out/'instance.cnf').write_text(dimacs(clauses,args.vars));(out/'witness.json').write_text(json.dumps(solution.astype(int).tolist()))
        print(f'Saved SAT instance and verified witness to {out}')
if __name__=='__main__':main()
