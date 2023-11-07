import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
from ocpa.objects.log.importer.csv import factory as csv_import_factory

import json

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
with open(parent_dir+'/sample_logs/ocel_BPI2017.json', 'w') as file:
    json.dump(ocel, file)