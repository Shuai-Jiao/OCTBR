import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import pickle
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OC_Conformance, OCtokenbasedreplay, OCtokenbasedreplay2
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

import pickle
file_path = parent_dir+'/sample_logs/OCPN/order_process.pkl'
path = parent_dir+"/sample_logs/jsonocel/order_process.jsonocel"
ocel = ocel_import_factory.apply(path)
ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False}) 
with open(file_path, 'wb') as file:
    pickle.dump(ocpn, file)
'''ocpnoutputpath=parent_dir+'/sample_logs/OCPN/BPIfullocpn.pkl'
outputpath = parent_dir+'/test/output/BPIbackwardreplay.txt'
with open(ocpnoutputpath, "rb") as file:
    BPIfullocpn = pickle.load(file)


with open(outputpath, 'w') as file:
        file.write(f"-----Start-----\n")

prefix = parent_dir+'/sample_logs/jsonocel/FilteredBPI/'
filteredlist = [(1,2),(2,3),(3,10),(10,50)\
             ,(50,150),(150,550),(550,1550)]

    
for ele in filteredlist[0:1]:
    path = prefix+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    ocel = ocel_import_factory.apply(path)
    print(ocel is None)
    #ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
    time0= time.time() 
    result = OCtokenbasedreplay2(ocel,BPIfullocpn,handle_silence="backward_replay")
    time1= time.time() 
    with open(outputpath, 'a') as file:
        file.write(f"-----Start {path}-----\n\
                   ----Backward replay OCTBR-------\
            evaluation:{result}\n\
            time:{time1-time0}\n")'''