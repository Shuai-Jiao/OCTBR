from ocpa.objects.log.importer.csv import factory as csv_import_factory
import pm4py
from pm4py.objects.ocel.util import extended_table
import pandas as pd
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.csv_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
from preprocessing import PreprocessCSV

'''prefix = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCEM/sample_logs/"
prefixcsv = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/csv/"
path = "./sample_logs/csv/BPI2017-Final.csv"
path2 = prefixcsv+"running-example.csv"
a = PreprocessCSV(path,'ELocpa')
b = PreprocessCSV(path,'ELpm4py')
print(type(a),type(b))
#csv_import_factory.apply(path2)
ocel2 = pm4py.read_ocel(path2)
ocpn2 = pm4py.discover_oc_petri_net(ocel2)'''