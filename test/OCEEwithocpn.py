import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import pickle
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OCtokenbasedreplay2, OC_escaping_edge
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
from preprocessing import get_log_information, get_model_information
'''oceloutputpath=parent_dir+'/sample_logs/OCPN/BPI0to1ocpn.pkl'

with open(ocpnoutputpath, "rb") as file:
    ocel = pickle.load(file)'''
outputpath = parent_dir+'/test/output/BPIOCEEmodel.txt'
#ocpn_vis_factory.save(ocpn_vis_factory.apply(BPI0to1ocpn), "./BPI0to1ocpn.png")
with open(outputpath, 'w') as file:
    file.write(f"--------New File--------")
          
prefix = parent_dir+'/sample_logs/jsonocel/FilteredBPI/'
path = prefix+f"BPI50to150executionprocess.jsonocel"
ocel = ocel_import_factory.apply(path)
info = get_log_information(ocel)
with open(outputpath, 'a') as file:
        file.write(f"-----Start {path}-----\n\
                ----information-------\
            Number of solving objects:{info['number of (solving) objects']}\n\
            Number of solving events:{info['number of events']}\n\
            Number of involving objects {len(info['object list'])}\n")
        
restricted_model_list = [(3,10),(50,150),(550,1550),(5000,15000)]


prefix2 = parent_dir+'/sample_logs/OCPN/'



for ele in restricted_model_list:
    #path = prefix+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    #ocel = ocel_import_factory.apply(path)
    out_path = prefix2+f"BPI{ele[0]}to{ele[1]}model.pkl"
    with open(out_path, "rb") as file:
        ocpn = pickle.load(file)
    #ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})

    
    modelinfo1 = get_model_information(ocpn)
    with open(outputpath, 'a') as file:
        file.write(f"the information of {out_path} is {modelinfo1}")

    
        
    time0= time.time() 
    result =OC_escaping_edge(ocel,ocpn)
    time1= time.time() 
    with open(outputpath, 'a') as file:
        file.write(f"-----Start {path}-----\n\
                   ----BST OCEE-------\
            evaluation:{result}\n\
            time:{time1-time0}\n")