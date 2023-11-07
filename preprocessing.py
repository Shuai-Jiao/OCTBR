import pm4py
import datetime
import pandas as pd
from multiset import *
from pm4py.objects.ocel.util import extended_table
import pandas as pd
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.csv_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils
from ocpa.objects.log.importer.csv import factory as csv_import_factory
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
from ocpa.objects.log.importer.ocel.versions.import_ocel_json import import_jsonocel
import ocpa.objects.log.converter.factory as convert_factory
import ocpa.objects.log.converter.versions.csv_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils
import random
import math
from itertools import chain
from collections import Counter
from ocpa.objects.log.exporter.ocel.factory import apply as ocpaexporter
import json

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

# preprocess the csv (e.g., attributes mapping, drop duplication) and convert to the expected output format
# currently only for BPI preprocessing
def PreprocessCSV(path,format = 'ELocpa'):
    name = path.split('/')[-1]
    if name == 'BPI2017-Final.csv':
        if format == 'ELocpa':
            object_types = ["application", "offer"]
            attrmap1 = {"obj_names":object_types,
                        "val_names":[],
                        "act_name":"event_activity",
                        "time_name":"event_timestamp",
                        "sep":","}
            ELocpa = csv_import_factory.apply(file_path = path, parameters = attrmap1)
            #The under command ONLY remove ALL of the CERTAIN attributes!!!
            #ELocpa[name].log.log.drop('event_start_timestamp', axis=1)
            #If we don't remove the duplicate attrbute in the dataframe, bugs will\
            #occur when we try to explode (flatten) the object ("event_object").
            #Now it doesn't need! because we already optimized the algo of OCTBR, which\
            #doesn't need to traversal all the objects now!
            '''removeduplicate = ELocpa.log.log.loc[:,~ELocpa.log.log.columns.duplicated()]
            noduplog = Table(removeduplicate, parameters = ELocpa.parameters)
            nodupobj = obj_converter.apply(removeduplicate)
            nodupgraph = EventGraph(table_utils.eog_from_log(noduplog))
            ELocpa = OCEL(noduplog, nodupobj, nodupgraph, ELocpa.parameters)'''
            return ELocpa
            #print('---',ELocpa[name].log.log.columns)
        elif format == 'ELpm4py':
            attrmap2 = {'event_activity':'ocel:activity', 'event_timestamp':'ocel:timestamp', 'event_id':'ocel:eid'\
                            ,'order':'ocel:type:order','application':'ocel:type:application'}            
            table = pd.read_csv(path)
            table = table.rename(columns=attrmap2)
            ELpm4py = extended_table.get_ocel_from_extended_table(table,None,parameters={})
            return ELpm4py
    else:
        if format == 'ELocpa':
            return csv_import_factory.apply(path)
        elif format == 'ELpm4py':
            return pm4py.read_ocel(path)

#Solve the syntax error of the object types of 'github_pm4py','o2c','p2p','recruiting','running-example',\
#and 'transfer_order'.
#github_pm4py has ':' in between the attribute name!!! which have to be replaced.
#prefixcsv = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/csv/"
#suffixcsv = ".csv"
#storedpath = [path+'processed' for path in pathlist]
# recieve a csv file, preprocess it, and then convert the post csv (in stored path) to ocel
def solve_ot_syntaxerror(csv_path,stored_csv_path=None):
    if stored_csv_path == None:
        stored_csv_path = '/'.join(csv_path.split('/')[:-1])+'/'+csv_path.split('/')[-1].split('.')[-2]+'processed.csv'
    df = pd.read_csv(csv_path)
    object_types = [ele.replace("ocel:type:",'').replace(":","_") for ele in list(df.columns) if 'ocel:type:' in ele]
    rename = {}
    for ot in [obj for obj in df.columns if 'ocel:type:' in obj]:
        rename[ot] = ot.replace("ocel:type:",'').replace(":","_") 
    df.rename(columns=rename,inplace=True)
    df.to_csv(stored_csv_path)
    attrmap = {"obj_names":object_types,
                            "val_names":[],
                            "act_name":'ocel:activity',
                            "time_name":'ocel:timestamp',
                            "sep":","}
    ocel = csv_import_factory.apply(file_path = stored_csv_path,parameters = attrmap)
    return ocel

# get an OCPA ocel
# return a set of packed ocels
# ? solve crossing problem if too few data
# Like p2p ocel, it has 12538 process executions! And even 100 process executions\
# would be too difficult for context_and_binding to learn!!! So we set fraction to 0.01 by default
# **Increase the iteration to decrease the size of the generated ocel for training
# **Decrease the fraction to increase the requirement of the generated ocel for filtering
def create_training_set(ocel,fraction=None,iteration=None):
    var = ocel.process_executions 
    # remove duplicates
    var = list(var)
    #remove the worthless process (either too short or too long)
    # too short: no footprint will be detected, and the conform value is 0\
    # which contributes nothing to the gradient descent. why p2p has 12223 processes\
    # with length 1 ????
    # too long: too expensive for using context and binding.
    # there are processes with length over than 4800??? wtf?
    filter_var = [ele for ele in var if len(ele)>3 and len(ele)<len(ocel.obj.activities)]
    # discuss the default cases:
    if fraction is None:
        # ensure at least 10 could be used for training
        fraction = max(0.25*len(filter_var)/len(var),10/len(var))    
    #determine whether enough data exist
    if len(filter_var) < fraction*len(var):
        raise ValueError("Not enough variants for training")
    trainingID = random.sample(filter_var,math.ceil(len(var)*fraction))
    # by default 3 processes in a training log
    if iteration is None:
        iteration = len(trainingID)//3
    if len(filter_var)/iteration < 1:
        raise ValueError("Not enough process for iteration")
    # seperate the log
    num = len(trainingID)//iteration
    print('check the size of process----',len(var),Counter([len(ele) for ele in filter_var]),'\nlength of \
          filtered variant:',len(filter_var),fraction*len(var),'number of activities---',len(ocel.obj.activities))
    # extract the log 
    traininglist = []
    for i in range(iteration):
        #logset = []
        offset = i*num
        #index = i*num+j
        processes = [trainingID[offset+i] for i in range(num)]
        aggregateprocess = list(chain(*processes))
        print('The type of is:',type(aggregateprocess),type(aggregateprocess[0]))
        print('length of the process~~~',[len(ele) for ele in processes])
        filteredlog = ocel.log.log[ocel.log.log['event_id'].isin(aggregateprocess)]
        # convert to ocel format
        # the generated ocel could be too tricky for context&binding, if it contains\
        # over 20 events...(considering too many objects!). So we have to limit the\
        # size of the generated ocel. 
        # BUT, if we only pack one process in an ocel, the model will be overfitting!!!\
        # which contributes nothing to learning.
        #logset.append(OCEL(log, obj, graph, ocel.parameters))
        traininglist.append(pandas_to_ocel(filteredlog,ocel.parameters))
    # pack in the rest process     
    restnum = len(trainingID)%iteration
    if restnum > 0:
        #trainingID = trainingID[-restnum:]
        #logset = []
        offset = num*iteration
        processes = [trainingID[offset+i] for i in range(restnum)]
        aggregateprocess = list(chain(*processes))
        filteredlog = ocel.log.log[ocel.log.log['event_id'].isin(aggregateprocess)]
        #convert to ocel format
        #logset.append(OCEL(log, obj, graph, ocel.parameters))
        traininglist.append(pandas_to_ocel(filteredlog,ocel.parameters))

    return traininglist

# get a smaller ocel for testing, otherwise the result won't come even in 2h
# we have to avoid: the removing objects also 
def extract_sublog(ocel,storepath=None):
    var = ocel.process_executions
    # Too long would be too expensive for testing
    print('the number of processes and the total number of events',len(var),sum([len(ele) for ele in var]))
    # To avoid empty/too short event log after pruning!
    if len(var) < 1000:
        filter_var = var
    else:
        filter_var = [ele for ele in var if len(ele)>3 and len(ele)<len(ocel.obj.activities)]    
    if len(filter_var)<1000:
        #raise ValueError('The number of processes is less than 1000')
        print(storepath.split('/')[-1],': the number of processes is less than 1000')
        subprocesses = filter_var
    else:
        subprocesses = random.sample(filter_var,1000)
    print('the number of filtered processes and the total number of events',len(subprocesses),sum([len(ele) for ele in subprocesses]))
    sublog = ocel.log.log[ocel.log.log['event_id'].isin(list(chain(*subprocesses)))]
    #logset.append(OCEL(log, obj, graph, ocel.parameters))
    if not storepath is None:
        ocpaexporter(pandas_to_ocel(sublog,ocel.parameters),storepath)
    print('parameters in extract_sublog:',ocel.parameters)
    return pandas_to_ocel(sublog,ocel.parameters)

def pandas_to_ocel(df,parameter):
    print("parameter in pandas_to_ocel:",parameter)
    log = Table(df, parameters = parameter)
    obj = obj_converter.apply(df,parameters = parameter)
    print('obj type:',type(obj))
    graph = EventGraph(table_utils.eog_from_log(log))
    #logset.append(OCEL(log, obj, graph, ocel.parameters))
    #print('number of events~~~',len(obj.raw.events))
    return OCEL(log, obj, graph, parameter)

#Create the corresponding sublogs of the given log for testing
def create_sublog(ocellist=None):
    if ocellist is None:
        prefix1 = '/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/csv/'
        prefix2 = './sample_logs/csv/'
        suffix = '.csv'
        ocellist = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
        for path in ocellist:
            ocel = solve_ot_syntaxerror(prefix1+path+suffix,prefix1+path+'processed'+suffix)
            extract_sublog(ocel,'./sample_logs/jsonocel/'+path+'_sublog.jsonocel')

# store the import parameter of the given ocel in a json file (used in importing next time)
def store_ocel_parameter(pathlist=None):
    if pathlist is None:
        prefix = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/jsonocel/"
        suffix = "_sublog.jsonocel"
        pathlist = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
        pathlist = [prefix+ele+suffix for ele in pathlist]
    with open('ocel_parameter.json','r') as file:
        ocel_parameter = json.load(file)
    for path in pathlist:
        name = path.split('/')[-1].split('.')[-2]
        ocelstandard = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
        if name in ocelstandard:
            ocel = solve_ot_syntaxerror(path)
            ocel_parameter[name] = ocel.parameters
        if '_sublog' in path:
            obj = import_jsonocel(path)
            df, _ = convert_factory.apply(obj, variant='json_to_csv')
            object_type = list(set(obj.meta.obj_types)&set(df.columns.values))
            ocel_parameter[name] = {"obj_names":object_type}
    with open('ocel_parameter.json','w') as file:
        json.dump(ocel_parameter,file)

# since the sublog misses the object type, we use the object type stored in json to parse it
def parse_sublog(path):
    name = path.split('/')[-1].split('.')[-2]
    if '_sublog' in name:
        with open("ocel_parameter.json","r") as file:
            ocel_parameter = json.load(file)
        if name in ocel_parameter.keys():
            parameter = ocel_parameter[name]
        else:
            parameter = None
        ocel = ocel_import_factory.apply(path,parameters=parameter)
    else:
        raise ValueError('Not with sublog suffix')
    return ocel

def filter_process_execution(ocel,process_execution_list):
    concatenation = []
    for process_execution in process_execution_list:
        concatenation.extend(process_execution)
    filteredlog = ocel.log.log[ocel.log.log['event_id'].isin(concatenation)]
    return pandas_to_ocel(filteredlog,ocel.parameters)

def pandas_to_ocel(df,parameter):
    log = Table(df, parameters = parameter)
    obj = obj_converter.apply(df,parameters = parameter)
    graph = EventGraph(table_utils.eog_from_log(log))
    #logset.append(OCEL(log, obj, graph, ocel.parameters))
    #print('number of events~~~',len(obj.raw.events))
    return OCEL(log, obj, graph, parameter)

def get_log_attribute(ocel):
    result = {}
    activities_sequence = []
    involvingobjects = ocel.process_execution_objects
    solvingobjects = [x for ele in involvingobjects for x in ele]
    objectlist = list(set([x for ele in involvingobjects for x in ele]))
    process_execution = ocel.process_executions
    for execution in process_execution:
        processlist = []
        for event in execution:
            processlist.append(ocel.get_value(event,ocel.parameters['act_name']))
        activities_sequence.append(processlist)
        
    result['activities sequence']=activities_sequence
    result['object list']=objectlist
    result['solvingobjects']=solvingobjects
    result['variants']=ocel.variants
    result['variant frequency']=ocel.variant_frequencies
    result['variant graphs']=ocel.variant_graphs
    result['variant dict']=ocel.variants_dict
    return result

def filter_process_execution(ocel,start=None,end=None,store=False,storepath=None):
    process_execution = ocel.process_executions

    if start == None:
        start = 0
    if end == None :
        end = len(process_execution)-1
    if start<0 or end>len(process_execution)-1:
        return ValueError('the start or the end index exceeds the range')
    
    process_execution_list = process_execution[start:end]
    concatenation = []
    for process_execution in process_execution_list:
        concatenation.extend(process_execution)
    filteredlog = ocel.log.log[ocel.log.log['event_id'].isin(concatenation)]
    filteredocel = pandas_to_ocel(filteredlog,ocel.parameters)
    if store:
        ocpaexporter(filteredocel,storepath)
    return filteredocel

def get_log_information(ocel):
    result = {}
    activities_sequence = []
    involvingobjects = ocel.process_execution_objects
    solvingobjects = [x for ele in involvingobjects for x in ele]
    objectlist = list(set([x for ele in involvingobjects for x in ele]))
    process_execution = ocel.process_executions
    for execution in process_execution:
        processlist = []
        for event in execution:
            processlist.append(ocel.get_value(event,ocel.parameters['act_name']))
        activities_sequence.append(processlist)
    objectsnumber = sum([len(event.omap) for event in ocel.obj.raw.events.values()])
    
    result['number of events']=sum([len(ele) for ele in process_execution])
    result['number of (solving) objects']=objectsnumber
    result['activities sequence']=activities_sequence
    result['object list']=objectlist
    result['solvingobjects']=solvingobjects
    result['variants']=ocel.variants
    result['variant frequency']=ocel.variant_frequencies
    result['variant graphs']=ocel.variant_graphs
    result['variant dict']=ocel.variants_dict
    return result

def get_model_information(ocpn):
    result = {}
    result['number of places']=len(ocpn.places)
    result['number of transitions']=len(ocpn.transitions)
    result['number of silent transitions']=len([tran for tran in ocpn.transitions if tran.silent])
    result['number of arcs']=len(ocpn.arcs)
    return result