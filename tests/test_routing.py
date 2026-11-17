import itertools
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from fgcl.routing import (RoutingInstance, distance_matrix, route_schedule, validate_routes,
                          nearest_neighbor, clarke_wright, two_opt, solve, spectral_route,
                          synthetic_instance)
from fgcl.routing_io import read_instance, read_solution
from fgcl.route_app import run_experiment


VRP = '''NAME : small
TYPE : CVRP
DIMENSION : 3
CAPACITY : 5
EDGE_WEIGHT_TYPE : EUC_2D
NODE_COORD_SECTION
10 0 0
11 3 0
90 3 4
DEMAND_SECTION
10 0
11 2
90 3
DEPOT_SECTION
10
-1
EOF
'''

SOLOMON = '''DEMO
VEHICLE
NUMBER CAPACITY
2 5
CUSTOMER
CUST NO. XCOORD YCOORD DEMAND READY DUE SERVICE
0 0 0 0 0 30 0
1 3 0 2 10 12 2
2 3 4 3 0 30 1
'''


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.instance = RoutingInstance('triangle',[[0,0],[3,0],[3,4]],[0,2,3],5,distance='EXACT_2D')

    def test_cost_against_manual_triangle_and_exhaustive_tiny_baseline(self):
        matrix = distance_matrix(self.instance)
        np.testing.assert_allclose(matrix,[[0,3,5],[3,0,4],[5,4,0]])
        result = solve(self.instance)
        self.assertTrue(result['feasible'])
        self.assertEqual(result['cost'],12)
        # Exhaustive enumeration only for this two-customer test oracle.
        oracle = min(sum(matrix[a,b] for a,b in zip([0]+list(p),list(p)+[0]))
                     for p in itertools.permutations([1,2]))
        self.assertEqual(result['cost'],oracle)
        self.assertFalse(result['optimality_proven'])

    def test_half_up_rounding_and_zero_distances(self):
        inst = RoutingInstance('ties',[[0,0],[.5,0],[2.5,0]],[0,1,1],3)
        self.assertEqual(distance_matrix(inst)[0,1],1)
        self.assertEqual(distance_matrix(inst)[0,2],3)
        coincident = RoutingInstance('same',[[0,0],[0,0]],[0,1],1)
        self.assertEqual(solve(coincident)['cost'],0)

    def test_time_window_schedule_and_depot_return(self):
        inst = read_instance(SOLOMON)
        result = route_schedule(inst,[1,2])
        self.assertTrue(result['feasible'])
        self.assertEqual(result['cost'],12)
        self.assertEqual(result['waiting'],7)
        self.assertEqual(result['return'],22)
        self.assertEqual(result['duration'],22)
        self.assertEqual(result['visits'][1]['start'],10)
        tight = RoutingInstance('tight',inst.coordinates,inst.demands,5,
                                [[0,20],[10,12],[0,30]],inst.service,distance='EXACT_2D')
        self.assertFalse(route_schedule(tight,[1,2])['feasible'])
        self.assertTrue(route_schedule(tight,[2,1])['feasible'])

    def test_global_validator_rejects_missing_duplicates_capacity_and_fleet(self):
        for routes in ([[1]],[[1,1,2]],[[0,1,2]],[[1,2,9]], [[]]):
            self.assertFalse(validate_routes(self.instance,routes)['feasible'])
        small = RoutingInstance('cap',self.instance.coordinates,[0,2,3],3,vehicles=1)
        self.assertFalse(validate_routes(small,[[1,2]])['feasible'])
        self.assertFalse(validate_routes(small,[[1],[2]])['feasible'])
        report = solve(small)
        self.assertEqual(report['status'],'NO_FEASIBLE_CANDIDATE')
        self.assertFalse(report['optimality_proven'])

    def test_two_opt_removes_crossing_without_changing_coverage(self):
        inst = RoutingInstance('square',[[0,0],[1,1],[0,1],[1,0]],[0,1,1,1],4,distance='EXACT_2D')
        original = [[1,2,3]]
        improved = two_opt(inst,original)
        self.assertEqual(original,[[1,2,3]])
        self.assertTrue(validate_routes(inst,improved)['feasible'])
        self.assertAlmostEqual(validate_routes(inst,improved)['cost'],4)
        self.assertLess(validate_routes(inst,improved)['cost'],validate_routes(inst,original)['cost'])

    def test_heuristics_are_reproducible_and_respect_constraints(self):
        for time_windows in (False,True):
            inst = synthetic_instance(30,seed=11,time_windows=time_windows)
            for constructor in (nearest_neighbor,clarke_wright):
                routes = constructor(inst)
                self.assertEqual(routes,constructor(inst))
                self.assertTrue(validate_routes(inst,routes)['feasible'])
                refined = two_opt(inst,routes)
                self.assertTrue(validate_routes(inst,refined)['feasible'])
                self.assertLessEqual(validate_routes(inst,refined)['cost'],validate_routes(inst,routes)['cost']+1e-9)

    def test_spectral_diagnostics_leave_route_and_cost_unchanged(self):
        route = [1,2]
        before = self.instance.coordinates.copy()
        cost = route_schedule(self.instance,route)['cost']
        report = spectral_route(self.instance,route)
        np.testing.assert_array_equal(before,self.instance.coordinates)
        self.assertEqual(route,[1,2])
        self.assertEqual(cost,route_schedule(self.instance,route)['cost'])
        self.assertGreaterEqual(report['coordinate_mse'],0)
        self.assertEqual(report['smooth_coordinates'][0],report['smooth_coordinates'][-1])

    def test_import_vrplib_solomon_json_and_numbering(self):
        inst = read_instance(VRP)
        self.assertEqual(inst.ids,(10,11,90))
        np.testing.assert_array_equal(read_instance(json.dumps(inst.to_dict())).coordinates,inst.coordinates)
        self.assertEqual(read_solution('Route #1: 1 2\nCost 12',inst),[[1,2]])
        self.assertEqual(read_solution('{"routes":[[11,90]]}',inst,'external'),[[1,2]])
        self.assertEqual(read_instance(SOLOMON).distance,'EXACT_2D')
        self.assertEqual(read_instance(VRP.replace('TYPE : CVRP','TYPE : CVRP\nVEHICLES : 2')).vehicles,2)
        for text in (VRP.replace('EUC_2D','ATT'),VRP.replace('TYPE : CVRP','TYPE : VRPTW'),
                     VRP.replace('DEMAND_SECTION','TIME_WINDOW_SECTION'),VRP.replace('90 3\n','11 3\n'),
                     VRP.replace('TYPE : CVRP','TYPE : CVRP\nDISTANCE : 10')):
            with self.assertRaises(ValueError):
                read_instance(text)

    def test_input_validation_and_failed_construction_not_infeasibility_certificate(self):
        for demands in ([1,2,3],[0,-1,3],[0,float('nan'),3]):
            with self.assertRaises(ValueError):
                RoutingInstance('bad',self.instance.coordinates,demands,5)
        with self.assertRaises(ValueError):
            synthetic_instance(1001)
        impossible = RoutingInstance('oversize',[[0,0],[1,1]],[0,9],2)
        with self.assertRaisesRegex(ValueError,'Não é prova'):
            nearest_neighbor(impossible)

    def test_complete_experiment_persists_instance_routes_hashes_and_import_violations(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_experiment({'instance_text':VRP,'seed':42,
                                     'solution_text':'Route #1: 1 1','improve':True},directory)
            self.assertTrue(report['solution']['feasible'])
            self.assertFalse(report['solution']['imported_solution']['feasible'])
            self.assertEqual(report['provenance']['status'],'completed')
            self.assertIn('instance_text',report['provenance']['input_sha256'])
            files = list(Path(directory).glob('*.json'))
            self.assertEqual(len(files),1)
            self.assertEqual(json.loads(files[0].read_text(encoding='utf-8')),report)


if __name__ == '__main__':
    unittest.main()
