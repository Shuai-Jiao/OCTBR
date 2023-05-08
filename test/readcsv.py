from ocpa.objects.log.importer.csv import factory as csv_import_factory
import pm4py
from pm4py.objects.ocel.util import extended_table
import pandas as pd
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.df_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils

filename = "./sample_logs/csv/BPI2017-Final.csv"
object_types = ["application", "offer"]
parameters = {"obj_names":object_types,
              "val_names":[],
              "act_name":"event_activity",
              "time_name":"event_timestamp",
              "sep":","}
ocel = csv_import_factory.apply(file_path= filename,parameters = parameters)
#ocel2 = pm4py.read_ocel(file_path = filename, parameters = parameters)
parameters2 = {'event_activity':'ocel:activity', 'event_timestamp':'ocel:timestamp', 'event_id':'ocel:eid'\
               ,'order':'ocel:type:order','application':'ocel:type:application'}

a1 = ocel.log.log.drop('event_start_timestamp', axis=1)
# a doesn't have duplicate anymore, but ocel.log.log still has!! because\
# it is not setable (defined in its property decorator)
a = ocel.log.log.loc[:,~ocel.log.log.columns.duplicated()]
log = Table(a, parameters = ocel.parameters)
obj = obj_converter.apply(a)
graph = EventGraph(table_utils.eog_from_log(log))
ocel2 = OCEL(log, obj, graph, ocel.parameters)
print(ocel.log.log.columns,'---',a.columns,'-----',ocel2.log.log.columns)
'''table2 = pd.read_csv("./sample_logs/csv/ocelexample.csv")
#print(table2.columns)
table = table.rename(columns=parameters2)
#print(table['ocel:timestamp'])
extended_table.get_ocel_from_extended_table(table,None,parameters={})
print(ocel.log.log.columns)'''

"""
Index(['event_None', 'event_Unnamed: 0', 'event_id', 'application',
       'event_activity', 'event_start_timestamp', 'event_timestamp',
       'event_LoanGoal', 'event_ApplicationType', 'event_RequestedAmount',
       'event_Action', 'event_FirstWithdrawalAmount', 'event_Accepted',
       'event_NumberOfTerms', 'offer', 'event_org:resource',
       'event_MonthlyCost', 'event_EventOrigin', 'event_EventID',
       'event_Selected', 'event_CreditScore', 'event_OfferedAmount',
       'event_CaseID'],
      dtype='object')"""
'''None of [Index(['ocel:activity', 'ocel:timestamp', 'ocel:eid'], dtype='object')] are in the [columns]'''
"""Example of the dataframe column in pm4py: Index(['Unnamed: 0', 'ocel:activity', 'ocel:timestamp', 'ocel:type:order',
       'ocel:type:item', 'ocel:type:delivery', 'ocel:eid'],
      dtype='object')"""
"""The EL colums of BPI"""