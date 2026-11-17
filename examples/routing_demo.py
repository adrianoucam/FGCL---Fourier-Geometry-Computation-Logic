"""Reproducible routing smoke example, no external data or solver download."""
import argparse
import json
from fgcl.route_app import run_experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--customers',type=int,default=80)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--capacity',type=float,default=60)
    parser.add_argument('--time-windows',action='store_true')
    parser.add_argument('--out',default='results/routing')
    args = parser.parse_args()
    result = run_experiment({'customers':args.customers,'seed':args.seed,'capacity':args.capacity,
                             'problem':'VRPTW' if args.time_windows else 'CVRP'},args.out)
    print(json.dumps({'instance':result['instance']['name'],
                      'status':result['solution']['status'],
                      'baselines':result['solution']['baselines'],
                      'elapsed_seconds':result['provenance']['elapsed_seconds'],
                      'output_directory':args.out},indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
