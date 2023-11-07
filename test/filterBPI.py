import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
from ocpa.objects.log.importer.csv import factory as csv_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
import pandas as pd
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.csv_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils

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
proexec = ocel.process_executions() 
print(f"the number of process_execution:{len(proexec)}the number of events: {sum([len(ele) for ele in proexec])}")
#ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/orderprocessPN.png")]
'''time1 = time.time()
print('ground truth(p,f):-------',quality_measure_factory.apply(ocel, ocpn))
time2 = time.time()
print('running time for context&binding',time2-time1)'''

def filter_process_execution(ocel,process_execution_list):
    concatenation = []
    for process_execution in process_execution_list:
        concatenation.extend(process_execution)
    filteredlog = ocel.log.log[ocel.log.log['event_id'].isin(concatenation)]
    return pandas_to_ocel(filteredlog,ocel.parameters)

def pandas_to_ocel(df,parameter):
    log = Table(df, parameters = parameter)
    obj = obj_converter.apply(df)
    graph = EventGraph(table_utils.eog_from_log(log))
    #logset.append(OCEL(log, obj, graph, ocel.parameters))
    #print('number of events~~~',len(obj.raw.events))
    return OCEL(log, obj, graph, parameter)