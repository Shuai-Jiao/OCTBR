import sys
import os
from ocpa.objects.log.importer.csv import factory as csv_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
from ocpa.objects.log.exporter.ocel.versions.export_ocel_json import apply as ocelexport
from ocpa.objects.log.importer.ocel import factory as json_import_factory
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
from token_based_replay import OCtokenbasedreplay
from preprocessing import get_log_information, get_model_information
import time
import pickle
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OC_Conformance, OCtokenbasedreplay

ocpnoutputpath=parent_dir+'/sample_logs/OCPN/BPIfullocpn.pkl'
with open(ocpnoutputpath, "rb") as file:
    BPIfullocpn = pickle.load(file)
ocpnoutputpath=parent_dir+'/sample_logs/OCPN/BPI0to1ocpn.pkl'
with open(ocpnoutputpath, "rb") as file:
    BPI0to1ocpn = pickle.load(file)

modelinfo1 = get_model_information(BPIfullocpn)
modelinfo2 = get_model_information(BPI0to1ocpn)
print(f"the information of BPIfullocpn is {modelinfo1}")
print(f"the information of BPI0to1ocpn is {modelinfo2}")
outputpath = parent_dir+'/test/output/BPIevaluate2.txt'
with open(outputpath, 'w') as file:
    file.write(f"the information of BPIfullocpn is {modelinfo1};\n\
               the information of BPI0to1ocpn is {modelinfo2}")

prefix = parent_dir+'/sample_logs/jsonocel/FilteredBPI/'
filteredlist = [(1,2),(2,3),(3,10),(10,50)\
             ,(50,150),(150,550),(550,1550)]

print('flattened TBR-------',)

for ele in filteredlist:
    path = prefix+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    print(f"-----Start {path}-----")
    ocel = json_import_factory.apply(file_path= path)
    #ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
    info = get_log_information(ocel)
    print(f"----information-------\n\
          Number of solving objects:{info['number of (solving) objects']}\n\
          Number of solving events:{info['number of events']}\n\
            Number of involving objects {len(info['object list'])}")
    with open(outputpath, 'a') as file:
        file.write(f"-----Start {path}-----\n\
                   ----information-------\
            Number of solving objects:{info['number of (solving) objects']}\n\
            Number of solving events:{info['number of events']}\n\
            Number of involving objects {len(info['object list'])}\n")
    time0 = time.time()
    fitness1 = OC_Conformance(PNtranslate_OCPA2PM4PY(BPI0to1ocpn),ELtranslate_OCPA2PM4PY(ocel))
    time1 = time.time()
    fitness2 = OC_Conformance(PNtranslate_OCPA2PM4PY(BPIfullocpn),ELtranslate_OCPA2PM4PY(ocel))
    time2 = time.time()

    print(f'FTBR (with 0to1) is done, fitness:{fitness1}, time:{time1-time0}')
    print(f'FTBR (with full) is done, fitness:{fitness2}, time:{time2-time1}')
    with open(outputpath, 'a') as file:
        file.write(f"------OCTBR------\n\
                FTBR (with 0to1) is done, fitness:{fitness1}, time:{time1-time0}\n\
                FTBR (with full) is done, fitness:{fitness2}, time:{time2-time1}\n")
    