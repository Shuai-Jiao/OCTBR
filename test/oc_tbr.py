import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import pickle
from object_centric_token_based_replay import token_based_replay
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
import time

restricted_path=parent_dir+'/sample_logs/ocpn/BPI_restricted_model.pkl'
with open(restricted_path, "rb") as file:
    restrict = pickle.load(file)
flower_path=parent_dir+'/sample_logs/ocpn/BPI_flower.pkl'
with open(flower_path, "rb") as file:
    flower = pickle.load(file)
ocpn_path=parent_dir+'/sample_logs/ocpn/BPI_model.pkl'
with open(ocpn_path, "rb") as file:
    ocpn = pickle.load(file)

text_path = parent_dir+'/test/output/test1.txt'
prefix = parent_dir+'/sample_logs/jsonocel/filtered_BPI/'
log_list = [(1,2),(2,3),(3,10),(10,50)\
             ,(50,150),(150,550),(550,1550)]

with open(text_path, 'w') as file:
    file.write(f"--------New File--------\n")

tf_parameters = {'handle':True,'method':'S_component'}
for ele in log_list:
    path = prefix+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    ocel = ocel_import_factory.apply(path,parameters={"debug": False})
    cached_parameters = {'BST':False,'activity':True}
    time0= time.time() 
    result = token_based_replay(ocel,ocpn,tf_parameters,cached_parameters)
    time1= time.time()
    TBR_time = time1-time0 
    out_path_info = current_dir+f"/output/information/info_{ele[0]}to{ele[1]}_log1.pkl"
    with open(text_path, 'a') as file:
        file.write(f"-----Start {path}-----\n\
            evaluation:{result}\n\
            time:{time1-time0}")