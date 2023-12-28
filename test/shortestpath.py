import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
#simply sys.path.append(".") doesn't always work!!! not work in cluster.

#sys.path.append(".")
#import pm4py.objects
#print('import ~~~pm4py.objects')
#import pm4py.objects.petri_net
#print('import ~~~pm4py.objects.petri_net')
#from model import Flowermodel, create_flower_model, Restrictedmodel
#from preprocessing import PreprocessCSV, solve_ot_syntaxerror, parse_sublog
import pickle
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OC_Conformance, OCtokenbasedreplay, OCtokenbasedreplay2
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time

outputpath = parent_dir+'/test/output/BPIshortestreplay.txt'

'''ocpnoutputpath=parent_dir+'/sample_logs/OCPN/order_process.pkl'
#outputpath = parent_dir+'/test/output/BPIbackwardreplay.txt'
with open(ocpnoutputpath, "rb") as file:
    order_process_ocpn = pickle.load(file)
'''
#ocpn_vis_factory.save(ocpn_vis_facto
#ocpn_vis_factory.save(ocpn_vis_factory.apply(order_process_ocpn), "./order_process_ocpn.png")
with open(outputpath, 'w') as file:
    file.write(f"--------New File--------")

'''path = parent_dir+"/sample_logs/jsonocel/order_process.jsonocel"
ocel = ocel_import_factory.apply(path)
print(ocel is None)
#ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False}) 
time0= time.time() 
result = OCtokenbasedreplay2(ocel,order_process_ocpn,handle_silence="shortest_path")
time1= time.time() 
with open(outputpath, 'a') as file:
        file.write(f"-----Start {path}-----\n\
                   ----Shortest path replay OCTBR-------\
            evaluation:{result}\n\
            time:{time1-time0}\n")'''


ocpnoutputpath=parent_dir+'/sample_logs/OCPN/BPI0to1ocpn.pkl'

with open(ocpnoutputpath, "rb") as file:
    BPI0to1ocpn = pickle.load(file)

prefix = parent_dir+'/sample_logs/jsonocel/FilteredBPI/'
filteredlist = [(1,2),(2,3),(3,10),(10,50)\
             ,(50,150),(150,550),(550,1550)]

    
for ele in filteredlist:
    path = prefix+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    ocel = ocel_import_factory.apply(path)
    print(ocel is None)
    #ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
    time0= time.time() 
    result = OCtokenbasedreplay2(ocel,BPI0to1ocpn,handle_silence="shortest_path")
    time1= time.time() 
    with open(outputpath, 'a') as file:
        file.write(f"-----Start {path}-----\n\
                   ----Shortest path replay OCTBR-------\
            evaluation:{result}\n\
            time:{time1-time0}\n")