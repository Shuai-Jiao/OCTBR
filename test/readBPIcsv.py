from ocpa.objects.log.importer.csv import factory as csv_import_factory
import pm4py
from pm4py.objects.ocel.util import extended_table
import pandas as pd
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.df_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils
import sys
sys.path.append(".")
from preprocessing import PreprocessCSV

path = "./sample_logs/csv/BPI2017-Final.csv"
a = PreprocessCSV(path,'ELocpa')
b = PreprocessCSV(path,'ELpm4py')
print(type(a),type(b))