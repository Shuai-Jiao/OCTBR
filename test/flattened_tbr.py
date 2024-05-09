import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import os
import sys
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
import pandas as pd
sys.path.append(".")
from flattened_token_based_replay import flattened_token_based_replay
import pickle
import time

text_path = parent_dir+'/test/output/test2.txt'
with open(text_path, 'w') as file:
    file.write(f"--------New File--------\n\
               flattened TBR\n")
    
ocpn_path=parent_dir+'/sample_logs/ocpn/BPI_model.pkl'
with open(ocpn_path, "rb") as file:
    ocpn = pickle.load(file)

prefix = parent_dir+'/sample_logs/jsonocel/filtered_BPI/'
log_list = [(1,2),(2,3),(3,10),(10,50)\
             ,(50,150),(150,550),(550,1550)]

for ele in log_list:
    ocel_path = prefix+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    ocel = ocel_import_factory.apply(ocel_path)
    time0 = time.time()
    result = flattened_token_based_replay(ocpn,ocel)
    time1 = time.time()
    with open(text_path, 'a') as file:
        file.write(f"-----Start {ocel_path}-----\n\
            flattened fitness:{result}\n\
            time:{time1-time0}")
