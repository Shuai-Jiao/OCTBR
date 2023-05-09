import pm4py
import datetime
import pandas as pd
from multiset import *
from pm4py.objects.ocel.util import extended_table
import pandas as pd
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.df_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils
from ocpa.objects.log.importer.csv import factory as csv_import_factory

def ParsingCSV(csvpath, parameters=None):
    csvlog = pd.read_csv(csvpath,sep=';')
    for ot in parameters['object_type']:
        csvlog[ot] = csvlog[ot].map(lambda x: str([y.strip() for y in x.split(',')]) if isinstance(x,str) else str([]))
        
    csvlog["event_id"] = list(range(0,len(csvlog)))
    csvlog.index = list(range(0,len(csvlog)))
    csvlog["event_id"] = csvlog["event_id"].astype(float).astype(int)
    csvlog = csvlog.rename(columns={"event_id": 'ocel:eid', parameters['time_name']:'ocel:timestamp',\
    parameters['act_name']:'ocel:activity'})
    for ot in parameters['object_type']:
        csvlog = csvlog.rename(columns={ot:str('ocel:type:'+ot)})
    '''Warnining: the previous timestamp should be determined whether an integer is'''
    csvlog['ocel:timestamp'] = [str(datetime.datetime.fromtimestamp(x))\
                                for x in csvlog['ocel:timestamp']]
    return csvlog

#preprocess the csv (e.g., attributes mapping, drop duplication) and convert to the expected output format
def PreprocessCSV(path,format = 'ELocpa'):
    name = path.split('/')[-1]
    if name == 'BPI2017-Final.csv':
        object_types = ["application", "offer"]
        attrmap1 = {"obj_names":object_types,
                    "val_names":[],
                    "act_name":"event_activity",
                    "time_name":"event_timestamp",
                    "sep":","}
        attrmap2 = {'event_activity':'ocel:activity', 'event_timestamp':'ocel:timestamp', 'event_id':'ocel:eid'\
                        ,'order':'ocel:type:order','application':'ocel:type:application'}
        ELocpa = csv_import_factory.apply(file_path = path, parameters = attrmap1)
        #The under command ONLY remove ALL of the CERTAIN attributes!!!
        #ELocpa[name].log.log.drop('event_start_timestamp', axis=1)
        #If we don't remove the duplicate attrbute in the dataframe, bugs will\
        #occur when we try to explode (flatten) the object ("event_object").
        removeduplicate = ELocpa.log.log.loc[:,~ELocpa.log.log.columns.duplicated()]
        noduplog = Table(removeduplicate, parameters = ELocpa.parameters)
        nodupobj = obj_converter.apply(removeduplicate)
        nodupgraph = EventGraph(table_utils.eog_from_log(noduplog))
        ELocpa = OCEL(noduplog, nodupobj, nodupgraph, ELocpa.parameters)
        #print('---',ELocpa[name].log.log.columns)
        table = pd.read_csv(path)
        table = table.rename(columns=attrmap2)
        ELpm4py = extended_table.get_ocel_from_extended_table(table,None,parameters={})
    else:
        ELocpa = csv_import_factory.apply(path)
        ELpm4py = pm4py.read_ocel(path)

    if format == 'ELocpa':
        return ELocpa
    elif format == 'ELpm4py':
        return ELpm4py