"""Local browser application: python -m fgcl.route_app --port 8765.

Stdlib HTTP + NumPy only. Bound to loopback; not a production hosting server.
"""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import uuid
import numpy as np
from .routing import synthetic_instance, solve, validate_routes, spectral_route
from .routing_io import read_instance, read_solution
from .reproducibility import experiment_record


def run_experiment(payload, output_dir):
    seed = int(payload.get('seed',42))
    if payload.get('instance_text'):
        instance = read_instance(payload['instance_text'])
    else:
        instance = synthetic_instance(customers=int(payload.get('customers',80)), seed=seed,
                                      capacity=float(payload.get('capacity',60)),
                                      time_windows=payload.get('problem','CVRP') == 'VRPTW',
                                      clustered=payload.get('distribution','clustered') == 'clustered')
    cutoff = float(payload.get('cutoff',.2))
    if not .01 <= cutoff <= .5:
        raise ValueError('Corte espectral deve estar entre 0.01 e 0.5.')
    config = {'seed': seed, 'capacity': float(instance.capacity), 'distance': instance.distance,
              'improve': bool(payload.get('improve',True)), 'cutoff': cutoff,
              'source': 'uploaded' if payload.get('instance_text') else 'synthetic',
              'vehicles': instance.vehicles, 'solution_numbering': payload.get('numbering','internal'),
              'customers': len(instance.demands)-1, 'time_windows': instance.windows is not None,
              'two_opt_max_checks': 20000, 'two_opt_passes': 2, 'spectral_order': 1.,
              'travel_speed': 1., 'tolerance': 1e-9}
    arrays = {'coordinates': instance.coordinates, 'demands': instance.demands,
              'service': instance.service}
    if instance.windows is not None:
        arrays['windows'] = instance.windows
    for key in ('instance_text','solution_text'):
        if payload.get(key):
            arrays[key] = np.frombuffer(payload[key].encode('utf-8'), dtype=np.uint8)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    path = Path(output_dir)/f'{stamp}-{uuid.uuid4().hex[:8]}.json'
    with experiment_record(path, seed=seed, config=config, inputs=arrays,
                           sources=['clarke-wright-1964','cvrplib-conventions','fgcl-bochner-riesz']) as metrics:
        solution = solve(instance, improve=config['improve'], cutoff=cutoff)
        if payload.get('solution_text'):
            routes = read_solution(payload['solution_text'], instance, config['solution_numbering'])
            report = validate_routes(instance, routes)
            for schedule in report['routes']:
                schedule['spectral'] = spectral_route(instance, schedule['nodes'][1:-1], cutoff=cutoff)
            solution['imported_solution'] = report
        metrics.update({key: solution[key] for key in ('status','method','route_count','cost','feasible')})
    record = json.loads(path.read_text(encoding='utf-8'))
    result = {'instance': instance.to_dict(), 'solution': solution, 'provenance': record}
    # Keep the complete reproducible artifact, including routes and instance.
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')
    temporary.replace(path)
    return result


def create_server(port=8765, output_dir='results/routing'):
    static = Path(__file__).with_name('route_web')

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, content_type):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            files = {'/': ('index.html','text/html; charset=utf-8'),
                     '/app.js': ('app.js','text/javascript; charset=utf-8'),
                     '/style.css': ('style.css','text/css; charset=utf-8')}
            item = files.get(self.path)
            if item is None:
                return self.send(404,b'Not found','text/plain')
            return self.send(200,(static/item[0]).read_bytes(),item[1])

        def do_POST(self):
            if self.path != '/api/solve':
                return self.send(404,b'Not found','text/plain')
            try:
                if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                    raise ValueError('Use application/json.')
                size = int(self.headers.get('Content-Length',0))
                if not 0 < size <= 4_100_000:
                    raise ValueError('Requisição vazia ou maior que 4.1 MB.')
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload,dict):
                    raise ValueError('Requisição deve ser objeto JSON.')
                result = run_experiment(payload,output_dir)
                data = json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8')
                self.send(200,data,'application/json; charset=utf-8')
            except (ValueError, TypeError, KeyError, OverflowError) as error:
                data = json.dumps({'error':str(error)},ensure_ascii=False).encode('utf-8')
                self.send(400,data,'application/json; charset=utf-8')

        def log_message(self, format, *args):
            pass

    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    parser = argparse.ArgumentParser(description='FGCL Route Lab — visualizador acadêmico CVRP/VRPTW')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--out',default='results/routing')
    args = parser.parse_args()
    server = create_server(args.port,args.out)
    print(f'FGCL Route Lab: http://127.0.0.1:{server.server_port}',flush=True)
    print('CPU · dados locais · Ctrl+C para encerrar',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
