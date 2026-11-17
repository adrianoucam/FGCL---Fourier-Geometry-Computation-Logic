"""Strict import subset: CVRP EUC_2D VRPLIB, Solomon VRPTW, or FGCL JSON.

No downloads. Unsupported edge types/sections are rejected, not approximated.
"""
import json
import re
import numpy as np
from .routing import RoutingInstance, MAX_CUSTOMERS


def read_instance(text, format='auto'):
    text = text.lstrip('\ufeff').strip()
    if not text or len(text.encode('utf-8')) > 2_000_000:
        raise ValueError('Instância vazia ou maior que 2 MB.')
    if format == 'auto':
        format = 'json' if text.startswith('{') else ('vrplib' if 'NODE_COORD_SECTION' in text else 'solomon')
    if format == 'json':
        data = json.loads(text)
        allowed = {'name','coordinates','demands','capacity','windows','service','distance','ids','vehicles'}
        if not isinstance(data, dict) or set(data)-allowed:
            raise ValueError('JSON da instância possui campos não suportados.')
        return RoutingInstance(**data)
    if format == 'solomon':
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        upper = [line.upper() for line in lines]
        if 'VEHICLE' not in upper or 'CUSTOMER' not in upper:
            raise ValueError('Formato não reconhecido. Use JSON FGCL, CVRP VRPLIB ou Solomon.')
        vehicle_position = upper.index('VEHICLE')
        customer_position = upper.index('CUSTOMER')
        fleet = next((line.split() for line in lines[vehicle_position+1:customer_position]
                      if re.fullmatch(r'\d+\s+[\d.]+', line)), None)
        if fleet is None:
            raise ValueError('Cabeçalho Solomon deve declarar número de veículos e capacidade.')
        rows = []
        for line in lines[customer_position+1:]:
            if re.match(r'^\d+\s', line):
                fields = line.split()
                if len(fields) != 7:
                    raise ValueError('Solomon requer 7 colunas por nó.')
                rows.append([float(value) for value in fields])
        rows = np.asarray(rows)
        if rows.ndim != 2 or len(rows) < 2 or len(rows) > MAX_CUSTOMERS+1:
            raise ValueError('Solomon: use depósito mais 1 a 1000 clientes.')
        if not np.all(rows[:,0] == np.floor(rows[:,0])) or rows[0,0] != 0:
            raise ValueError('Solomon: IDs inteiros e depósito 0 na primeira linha.')
        # Solomon distances convention is exact Euclidean here, never silently rounded.
        return RoutingInstance(lines[0], rows[:,1:3], rows[:,3], float(fleet[1]),
                               rows[:,4:6], rows[:,6], 'EXACT_2D',
                               tuple(int(i) for i in rows[:,0]), int(fleet[0]))
    if format != 'vrplib':
        raise ValueError('Formato não suportado.')
    headers, sections = {}, {}
    section = None
    supported = {'NODE_COORD_SECTION', 'DEMAND_SECTION', 'DEPOT_SECTION'}
    for line in text.splitlines():
        line = line.strip()
        if not line or line == 'EOF':
            continue
        if line.endswith('_SECTION'):
            if line not in supported:
                raise ValueError('Seção VRPLIB não suportada: '+line)
            section = line
            if section in sections:
                raise ValueError('Seção VRPLIB repetida.')
            sections[section] = []
        elif section:
            sections[section].append(line.split())
        else:
            fields = re.split(r'\s*:\s*|\s+', line, maxsplit=1)
            if len(fields) == 2:
                headers[fields[0]] = fields[1]
    if headers.get('TYPE') != 'CVRP' or headers.get('EDGE_WEIGHT_TYPE') != 'EUC_2D':
        raise ValueError('VRPLIB: apenas TYPE CVRP com EDGE_WEIGHT_TYPE EUC_2D; use JSON para VRPTW.')
    allowed_headers = {'NAME','TYPE','COMMENT','DIMENSION','CAPACITY','EDGE_WEIGHT_TYPE',
                       'EDGE_WEIGHT_FORMAT','NODE_COORD_TYPE','DISPLAY_DATA_TYPE','VEHICLES'}
    if set(headers)-allowed_headers:
        raise ValueError('Cabeçalho VRPLIB não suportado: '+', '.join(sorted(set(headers)-allowed_headers)))
    if headers.get('EDGE_WEIGHT_FORMAT','FUNCTION') != 'FUNCTION':
        raise ValueError('VRPLIB: apenas distâncias calculadas por função EUC_2D.')
    if headers.get('NODE_COORD_TYPE','TWOD_COORDS') != 'TWOD_COORDS':
        raise ValueError('VRPLIB: apenas coordenadas bidimensionais.')
    n = int(headers.get('DIMENSION', 0))
    if not 2 <= n <= MAX_CUSTOMERS+1 or not supported <= sections.keys():
        raise ValueError('VRPLIB: dimensão inválida ou seções ausentes.')
    coordinates = {}
    demands = {}
    for fields in sections['NODE_COORD_SECTION']:
        if len(fields) != 3 or int(fields[0]) in coordinates:
            raise ValueError('Coordenadas VRPLIB inválidas ou IDs repetidos.')
        coordinates[int(fields[0])] = [float(fields[1]), float(fields[2])]
    for fields in sections['DEMAND_SECTION']:
        if len(fields) != 2 or int(fields[0]) in demands:
            raise ValueError('Demandas VRPLIB inválidas ou IDs repetidos.')
        demands[int(fields[0])] = float(fields[1])
    depot_values = [int(value) for fields in sections['DEPOT_SECTION'] for value in fields]
    if len(depot_values) != 2 or depot_values[-1] != -1:
        raise ValueError('Suporte a exatamente um depósito, seguido por -1.')
    depot = depot_values[0]
    if len(coordinates) != n or set(coordinates) != set(demands) or depot not in coordinates:
        raise ValueError('IDs de coordenadas, demandas e depósito incompatíveis com DIMENSION.')
    ids = [depot]+sorted(i for i in coordinates if i != depot)
    return RoutingInstance(headers.get('NAME','VRPLIB'), [coordinates[i] for i in ids],
                           [demands[i] for i in ids], float(headers['CAPACITY']), ids=tuple(ids),
                           vehicles=int(headers['VEHICLES']) if 'VEHICLES' in headers else None)


def read_solution(text, instance, numbering='internal'):
    """JSON {routes:[[...]]} or CVRPLIB .sol. Depot must be omitted.

    internal: 1..n means position in normalized instance; external: original IDs.
    Numbering is explicit because some benchmarks use different conventions.
    """
    if numbering not in ('internal','external'):
        raise ValueError('Numeração de solução: internal ou external.')
    if text.lstrip().startswith('{'):
        data = json.loads(text)
        routes = data['routes']
        if 'numbering' in data and data['numbering'] != numbering:
            raise ValueError('Selecione a mesma numeração declarada no JSON da solução.')
    else:
        routes = []
        for line in text.splitlines():
            if line.strip().lower().startswith('route'):
                if ':' not in line:
                    raise ValueError('Solução .sol: esperado Route #k: clientes.')
                routes.append([int(i) for i in line.split(':',1)[1].split()])
    if not isinstance(routes,list) or not routes:
        raise ValueError('Nenhuma rota encontrada na solução.')
    by_id = {node: i for i,node in enumerate(instance.ids)}
    output = []
    for route in routes:
        if not isinstance(route,list) or any(type(i) is not int for i in route):
            raise ValueError('Rotas devem ser listas de IDs inteiros.')
        if numbering == 'external':
            try:
                route = [by_id[i] for i in route]
            except KeyError as error:
                raise ValueError('ID externo desconhecido na solução.') from error
        output.append(route)
    return output
