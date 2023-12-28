import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import pickle
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OC_Conformance, OCtokenbasedreplay, OCtokenbasedreplay2, solve_token_flooding, calculate_S_component
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

ocpnoutputpath=parent_dir+'/sample_logs/OCPN/BPI0to1ocpn.pkl'
with open(ocpnoutputpath, "rb") as file:
    BPI0to1ocpn = pickle.load(file)
circle = calculate_S_component(BPI0to1ocpn)
print(f'the circle list is: {circle}')