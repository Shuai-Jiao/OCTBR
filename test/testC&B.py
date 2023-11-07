import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
#simply sys.path.append(".") doesn't always work!!! not work in cluster.
from ocpa.objects.log.importer.csv import factory as csv_import_factory
#sys.path.append(".")
#import pm4py.objects
#print('import ~~~pm4py.objects')
#import pm4py.objects.petri_net
#print('import ~~~pm4py.objects.petri_net')
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

BPI = parent_dir+'/sample_logs/csv/BPI2017-Final.csv'
print(f'The path is {BPI}')
#suffix2 = ".jsonocel"
object_types = ["application", "offer"]
parameters = {"obj_names":object_types,
              "val_names":[],
              "act_name":"event_activity",
              "time_name":"event_timestamp",
              "sep":","}
ocel = csv_import_factory.apply(file_path= BPI,parameters = parameters)
ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False}) 
#ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/orderprocessPN.png")]
time1 = time.time()
print('ground truth(p,f):-------',quality_measure_factory.apply(ocel, ocpn))
time2 = time.time()
print('running time for context&binding',time2-time1)
