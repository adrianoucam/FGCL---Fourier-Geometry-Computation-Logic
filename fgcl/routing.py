"""Small CPU CVRP/VRPTW lab: verified heuristic candidates, never optimality claims.

Classical routing equations and FGCL spectral diagnostics: docs/ROUTING.md.
Internal customer indices are 1..n, depot is 0; original IDs are preserved.
"""
from dataclasses import dataclass
import math
import operator
import numpy as np
from .fourier import bochner_riesz_filter

MAX_CUSTOMERS = 1000


@dataclass(frozen=True)
class RoutingInstance:
    name: str
    coordinates: np.ndarray
    demands: np.ndarray
    capacity: float
    windows: np.ndarray | None = None
    service: np.ndarray | None = None
    distance: str = 'EUC_2D'
    ids: tuple | None = None
    vehicles: int | None = None

    def __post_init__(self):
        xy = np.array(self.coordinates, dtype=float, copy=True)
        q = np.array(self.demands, dtype=float, copy=True)
        if xy.ndim != 2 or xy.shape[1] != 2 or not 2 <= len(xy) <= MAX_CUSTOMERS+1:
            raise ValueError('Use 1 a 1000 clientes com coordenadas [N,2], incluindo depósito.')
        if q.shape != (len(xy),) or not np.isfinite(xy).all() or not np.isfinite(q).all():
            raise ValueError('Coordenadas e demandas devem ser finitas e compatíveis.')
        if not np.isfinite(self.capacity) or self.capacity <= 0 or np.any(q < 0) or q[0] != 0:
            raise ValueError('Capacidade positiva, demandas não negativas e demanda do depósito zero.')
        if self.distance not in ('EUC_2D', 'EXACT_2D'):
            raise ValueError('Distância suportada: EUC_2D (floor(d+0.5)) ou EXACT_2D.')
        windows = None if self.windows is None else np.array(self.windows, dtype=float, copy=True)
        if windows is not None and (windows.shape != (len(xy), 2) or not np.isfinite(windows).all()
                                    or np.any(windows[:, 0] < 0) or np.any(windows[:, 0] > windows[:, 1])):
            raise ValueError('Janelas devem ser finitas, não negativas e início <= fim.')
        service = np.zeros(len(xy)) if self.service is None else np.array(self.service, dtype=float, copy=True)
        if service.shape != (len(xy),) or not np.isfinite(service).all() or np.any(service < 0) or service[0] != 0:
            raise ValueError('Serviço deve ser não negativo; serviço do depósito deve ser zero.')
        ids = tuple(range(len(xy))) if self.ids is None else tuple(operator.index(i) for i in self.ids)
        if len(ids) != len(xy) or len(set(ids)) != len(ids):
            raise ValueError('IDs devem ser inteiros únicos, um por nó.')
        if self.vehicles is not None and operator.index(self.vehicles) < 1:
            raise ValueError('Número disponível de veículos deve ser positivo.')
        for key, value in (('coordinates', xy), ('demands', q), ('windows', windows), ('service', service)):
            if value is not None:
                value.setflags(write=False)
            object.__setattr__(self, key, value)
        object.__setattr__(self, 'ids', ids)

    def to_dict(self):
        return {'name': str(self.name), 'coordinates': self.coordinates.tolist(),
                'demands': self.demands.tolist(), 'capacity': float(self.capacity),
                'windows': None if self.windows is None else self.windows.tolist(),
                'service': self.service.tolist(), 'distance': self.distance,
                'ids': list(self.ids), 'vehicles': self.vehicles}


def distance_matrix(instance):
    """Symmetric Euclidean costs; TSPLIB uses nearest integer, ties upward."""
    xy = instance.coordinates
    matrix = np.hypot(xy[:, 0, None]-xy[None, :, 0], xy[:, 1, None]-xy[None, :, 1])
    return np.floor(matrix+.5) if instance.distance == 'EUC_2D' else matrix


def route_schedule(instance, route, matrix=None):
    """Earliest-departure schedule, speed=1, start-of-service windows.

    route contains customers only; depot is implicitly added at each end.
    This validator does not check global coverage; use validate_routes for that.
    """
    matrix = distance_matrix(instance) if matrix is None else matrix
    route = [operator.index(i) for i in route]
    if not route or any(i <= 0 or i >= len(instance.demands) for i in route):
        raise ValueError('Uma rota deve conter índices de clientes válidos, sem depósito.')
    clock = 0. if instance.windows is None else float(instance.windows[0, 0])
    departure = clock
    visits = [{'node': 0, 'arrival': clock, 'start': clock, 'departure': clock, 'waiting': 0., 'load': 0.}]
    load = 0.
    cost = 0.
    violations = []
    previous = 0
    for node in route+[0]:
        travel = float(matrix[previous, node])
        arrival = clock+travel
        start = arrival if instance.windows is None else max(arrival, float(instance.windows[node, 0]))
        waiting = start-arrival
        if instance.windows is not None and start > instance.windows[node, 1]+1e-9:
            violations.append(f'Janela de tempo violada no nó {instance.ids[node]}.')
        load += float(instance.demands[node])
        clock = start+float(instance.service[node])
        cost += travel
        visits.append({'node': node, 'arrival': arrival, 'start': start,
                       'departure': clock, 'waiting': waiting, 'load': load})
        previous = node
    if load > instance.capacity+1e-9:
        violations.append('Capacidade excedida.')
    return {'nodes': [0]+route+[0], 'customers': len(route), 'load': load,
            'cost': cost, 'departure': departure, 'return': clock,
            'waiting': sum(v['waiting'] for v in visits), 'duration': clock-departure,
            'visits': visits, 'feasible': not violations, 'violations': violations}


def validate_routes(instance, routes, matrix=None):
    """Validate coverage, capacity, windows, depot return and fleet size."""
    matrix = distance_matrix(instance) if matrix is None else matrix
    errors = []
    seen = []
    schedules = []
    for number, route in enumerate(routes, 1):
        try:
            result = route_schedule(instance, route, matrix)
        except (ValueError, TypeError) as error:
            errors.append(f'Rota {number}: {error}')
            continue
        seen.extend(result['nodes'][1:-1])
        schedules.append(result)
        errors.extend(f'Rota {number}: {v}' for v in result['violations'])
    if sorted(seen) != list(range(1, len(instance.demands))):
        errors.append('Cada cliente deve ser visitado exatamente uma vez.')
    if instance.vehicles is not None and len(routes) > instance.vehicles:
        errors.append('Quantidade disponível de veículos excedida pela heurística.')
    return {'feasible': not errors, 'violations': errors, 'routes': schedules,
            'route_count': len(routes), 'cost': sum(r['cost'] for r in schedules),
            'waiting': sum(r['waiting'] for r in schedules),
            'duration': sum(r['duration'] for r in schedules)}


def nearest_neighbor(instance, matrix=None):
    """Deterministic nearest feasible append, tie by internal ID; unlimited construction fleet."""
    matrix = distance_matrix(instance) if matrix is None else matrix
    remaining = set(range(1, len(instance.demands)))
    routes = []
    while remaining:
        route = []
        while remaining:
            last = route[-1] if route else 0
            candidate = next((i for i in sorted(remaining, key=lambda i: (matrix[last, i], i))
                              if route_schedule(instance, route+[i], matrix)['feasible']), None)
            if candidate is None:
                break
            route.append(candidate)
            remaining.remove(candidate)
        if not route:
            raise ValueError('Construção falhou: cliente não atendido nem por rota individual. Não é prova de inviabilidade global.')
        routes.append(route)
    return routes


def clarke_wright(instance, matrix=None):
    """Parallel savings, endpoint merges in both traversal directions with schedule checks.

    Classical savings adapted by FGCL for time-window feasibility. Negative or
    zero savings are ignored. No optimality guarantee or fixed-fleet repair.
    """
    matrix = distance_matrix(instance) if matrix is None else matrix
    n = len(instance.demands)
    routes = {i: [i] for i in range(1, n)}
    owner = {i: i for i in range(1, n)}
    for route in routes.values():
        if not route_schedule(instance, route, matrix)['feasible']:
            raise ValueError('Inicialização de economias falhou em uma rota individual; não é certificado de inviabilidade.')
    left, right = np.triu_indices(n-1, 1)
    left, right = left+1, right+1
    savings = matrix[0, left]+matrix[0, right]-matrix[left, right]
    for index in np.argsort(-savings, kind='stable'):
        if savings[index] <= 1e-9:
            break
        i, j = int(left[index]), int(right[index])
        a, b = owner[i], owner[j]
        if a == b or i not in (routes[a][0], routes[a][-1]) or j not in (routes[b][0], routes[b][-1]):
            continue
        ra = routes[a] if routes[a][-1] == i else routes[a][::-1]
        rb = routes[b] if routes[b][0] == j else routes[b][::-1]
        options = (ra+rb, (ra+rb)[::-1])
        feasible = [r for r in options if route_schedule(instance, r, matrix)['feasible']]
        if not feasible:
            continue
        merged = min(feasible, key=lambda r: (route_schedule(instance, r, matrix)['duration'], r))
        routes[a] = merged
        del routes[b]
        for node in merged:
            owner[node] = a
    return list(routes.values())


def two_opt(instance, routes, matrix=None, max_checks=20000):
    """Bounded intra-route reversal; accepts strictly cheaper feasible candidates."""
    matrix = distance_matrix(instance) if matrix is None else matrix
    output = [list(r) for r in routes]
    checks = 0
    for position, route in enumerate(output):
        best = route_schedule(instance, route, matrix)['cost']
        for _ in range(2):
            improved = False
            for i in range(len(route)-1):
                for j in range(i+1, len(route)):
                    if checks >= max_checks:
                        return output
                    checks += 1
                    prev, first = (0 if i == 0 else route[i-1]), route[i]
                    last, after = route[j], (0 if j == len(route)-1 else route[j+1])
                    delta = matrix[prev,last]+matrix[first,after]-matrix[prev,first]-matrix[last,after]
                    if delta >= -1e-9:
                        continue
                    candidate = route[:i]+route[i:j+1][::-1]+route[j+1:]
                    result = route_schedule(instance, candidate, matrix)
                    if result['feasible'] and result['cost'] < best-1e-9:
                        route[:] = candidate
                        best = result['cost']
                        improved = True
            if not improved:
                break
        output[position] = route
    return output


def spectral_route(instance, route, cutoff=.2, order=1.):
    """FGCL filter on cyclic coordinate sequence; diagnostics only, not a new route.

    Sampling is by visit index, not physical time or arc length. Smoothed points
    need not be customers or preserve constraints; never used to compute cost.
    """
    xy = instance.coordinates[[0]+list(route)]
    smooth = bochner_riesz_filter(xy, cutoff=cutoff, order=order, axes=(0,))
    centered = xy-xy.mean(axis=0)
    denominator = float(np.sum(centered**2))
    return {'smooth_coordinates': np.vstack([smooth, smooth[0]]).tolist(),
            'coordinate_mse': float(np.mean((xy-smooth)**2)),
            'residual_energy_ratio': float(np.sum((xy-smooth)**2)/denominator) if denominator else 0.,
            'cutoff': float(cutoff), 'order': float(order),
            'interpretation': 'Diagnóstico por índice de visita; curva suavizada não é uma rota viável.'}


def solve(instance, improve=True, cutoff=.2):
    """Return both baselines and best validated candidate under stated objective."""
    matrix = distance_matrix(instance)
    objective = 'routes_then_distance' if instance.windows is not None else 'distance'
    candidates = []
    for method, constructor in (('nearest_neighbor', nearest_neighbor), ('clarke_wright', clarke_wright)):
        routes = constructor(instance, matrix)
        report = validate_routes(instance, routes, matrix)
        candidates.append({'method': method, 'customer_routes': routes, **report})
        if improve:
            refined = two_opt(instance, routes, matrix)
            candidates.append({'method': method+'+2opt', 'customer_routes': refined,
                               **validate_routes(instance, refined, matrix)})
    def key(candidate):
        value = ((candidate['route_count'], candidate['cost']) if objective == 'routes_then_distance'
                 else (candidate['cost'], candidate['route_count']))
        return (not candidate['feasible'], *value)
    selected = min(candidates, key=key)
    routes = selected['customer_routes']
    enriched = []
    for route, schedule in zip(routes, selected['routes']):
        enriched.append({**schedule, 'spectral': spectral_route(instance, route, cutoff=cutoff)})
    return {'status': 'FEASIBLE_HEURISTIC' if selected['feasible'] else 'NO_FEASIBLE_CANDIDATE',
            'optimality_proven': False, 'objective': objective, 'method': selected['method'],
            'feasible': selected['feasible'], 'violations': selected['violations'],
            'route_count': selected['route_count'], 'cost': selected['cost'],
            'waiting': selected['waiting'], 'duration': selected['duration'], 'routes': enriched,
            'baselines': [{k: c[k] for k in ('method','feasible','route_count','cost','waiting')}
                          for c in candidates],
            'capacity_lower_bound': math.ceil(float(instance.demands.sum())/instance.capacity),
            'limitations': ['Heurísticas não certificam ótimo ou inviabilidade global.',
                           'Distância euclidiana, frota homogênea, um depósito, velocidade 1.',
                           'Análise espectral não altera a solução ou seu custo.']}


def synthetic_instance(customers=80, seed=42, capacity=60., time_windows=False, clustered=True):
    customers = operator.index(customers)
    if not 1 <= customers <= MAX_CUSTOMERS:
        raise ValueError('Use 1 a 1000 clientes.')
    rng = np.random.default_rng(seed)
    if clustered:
        centers = rng.uniform(10, 90, (8, 2))
        xy = np.clip(centers[rng.integers(0, 8, customers)]+rng.normal(0, 8, (customers, 2)), 0, 100)
    else:
        xy = rng.uniform(0, 100, (customers, 2))
    xy = np.vstack([[50., 50.], xy])
    demands = np.r_[0., rng.integers(1, 10, customers)].astype(float)
    windows = None
    service = np.zeros(customers+1)
    if time_windows:
        ready = rng.uniform(0, 220, customers)
        windows = np.vstack([[0., 800.], np.column_stack([ready, ready+160])])
        service[1:] = 5.
    return RoutingInstance(f'FGCL-demo-{customers}-{seed}', xy, demands, capacity,
                           windows, service, distance='EUC_2D')
