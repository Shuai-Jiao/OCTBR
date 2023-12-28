import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import pickle
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OCtokenbasedreplay2, solve_token_flooding, calculate_S_component
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

outputpath = parent_dir+'/test/output/cached_BST.txt'
path = parent_dir+"/sample_logs/jsonocel/order_process.jsonocel"
ocel = ocel_import_factory.apply(path)
print(ocel is None)
ocpnoutputpath=parent_dir+'/sample_logs/OCPN/order_process.pkl'
#outputpath = parent_dir+'/test/output/BPIbackwardreplay.txt'
with open(ocpnoutputpath, "rb") as file:
    order_process_ocpn = pickle.load(file)

time0 = time.time()
result = OCtokenbasedreplay2(ocel,order_process_ocpn,'shortest_path',False,False)
time1 = time.time()
result2 = quality_measure_factory.apply(ocel, order_process_ocpn)
time2 = time.time()
print(f'ground truth(p,f):{result2} and time is {time2-time1}')

with open(outputpath, 'w') as file:
        file.write(f"-----Start {path}-----\n\
                   ----Backward replay OCTBR-------\
            evaluation:{result}\n\
            time:{time1-time0}\n")