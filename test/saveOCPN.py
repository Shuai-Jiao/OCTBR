from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
import pickle
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory


prefix2 = parent_dir+'/sample_logs/OCPN/'
prefix1 = parent_dir+'/sample_logs/jsonocel/FilteredBPI/'
log_list = [(3,10),(50,150),(550,1550),(5000,15000)]

for ele in log_list:
    ocel_path = prefix1+f"BPI{ele[0]}to{ele[1]}executionprocess.jsonocel"
    
    ocel = ocel_import_factory.apply(ocel_path)
    out_path = prefix2+f"BPI{ele[0]}to{ele[1]}model.pkl"
    ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
    with open(out_path, 'wb') as file:
        # Use pickle.dump() to serialize and save the data to the file
        pickle.dump(ocpn, file)