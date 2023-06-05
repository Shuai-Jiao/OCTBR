from ocpa.objects.log.importer.csv import factory as csv_import_factory
import os
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import pandas as pd
import sys
import json
sys.path.append(".")
from preprocessing import solve_ot_syntaxerror, extract_sublog, create_sublog, store_ocel_parameter

prefix3 = './sample_logs/jsonocel/'
prefix4 = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/jsonocel/"
datalist = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
suffix2 = '_sublog.jsonocel'
prefix1 = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/jsonocel/"
ocelfolder = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
pathlist = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
storedpath = [path+'processed' for path in pathlist]
suffix1 = '.jsonocel'
prefix2 = '/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/csv/'
suffix3 = '.csv'
#create_sublog()
#store_ocel_parameter([prefix2+ele+suffix3 for ele in pathlist])
ocel_parameter = {}
for path in pathlist[:3]:
    #ocel = solve_ot_syntaxerror(prefix2+path+suffix3,prefix2+path+'processed'+suffix3)
    #ocel = csv_import_factory.apply(prefix2+path+suffix3)
    print('hi-----',path)
    with open("ocel_parameter.json","r") as file:
        parameter = json.load(file)
    ocel = ocel_import_factory.apply(prefix3+path+suffix2,parameters=parameter)
    

    #print('information ',path,'numeber of process: ',len(ocel.process_executions))
prefixcsv = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/csv/"
suffixcsv = ".csv"
pathBPI =  '/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCEM/sample_logs/csv/BPI2017-Final.csv'

#Test github_pm4py
'''df = pd.read_csv(prefixcsv+ocelfolder[0]+suffixcsv)
print('columns1--------',df.columns)
object_types = [ele.replace("ocel:type:",'').replace(":","_") for ele in list(df.columns) if 'ocel:type:' in ele]
rename = {}
for ot in [obj for obj in df.columns if 'ocel:type:' in obj]:
        rename[ot] = ot.replace("ocel:type:",'').replace(":","_")      
df.rename(columns=rename,inplace=True)
df.to_csv(prefixcsv+ocelfolder[0]+'processed'+suffixcsv)
print('columns2--------',df.columns)
attrmap = {"obj_names":object_types,
                        "val_names":[],
                        "act_name":'ocel:activity',
                        "time_name":'ocel:timestamp',
                        "sep":","}
ocel = csv_import_factory.apply(file_path = prefixcsv+ocelfolder[0]+'processed'+suffixcsv, parameters = attrmap)
ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/"+ocelfolder[0]+'.png')
'''
#Check the parameters of o2c
#The dataframe of BPI has such attributes! but why o2c doesn't have???
#For o2c the format is successfully imported! but the object not!
#The reason is that! in ocpa's df_to_ocel, it uses getattr(row,obj)\
#which doesn't work when obj is an illegal name for dot calling function\
#e.g. column symboe ocel:type:xx
#So we have to replace the illegal names of the columns first!!!
'''o2c = prefixcsv+pathlist[1]+suffixcsv
o2cprocessed = prefixcsv+pathlist[2]+suffixcsv
df = pd.read_csv(o2c)
o2crename = {}
for ot in [obj for obj in df.columns if 'ocel:type:' in obj]:
    o2crename[ot] = ot.replace("ocel:type:",'')
df.rename(columns=o2crename,inplace=True)
#print(o2crename,df.columns)
df.to_csv(prefixcsv+'o2cprocessed.csv')
object_types2 = ['EINKBELEG', 'MATERIAL', 'INDIP_REQ',\
                'CHARGE', 'ITEM_PROPOSAL',\
                'DEBIT_MEMO_DOC', 'HANDL_UNIT',\
                'VERKBELEG', 'WMS_TRANSFER', 'BELNR',\
                'INFOSATZ', 'INVOICE_CANCEL',\
                'DEBIT_MEMO_REQ', 'ORD_WO_CHARGE',\
                'INVOICE_PRO_FORMA', 'RETURNS_DOC',\
                'RETURNS_DELIVERY', 'CREDIT_MEMO_REQ',\
                'CREDIT_MEMO_DOC']
attrmap2 = {"obj_names":object_types2,
                        "val_names":[],
                        "act_name":'ocel:activity',
                        "time_name":'ocel:timestamp',
                        "sep":","}

#Testing for p2p
p2p = prefixcsv+pathlist[3]+suffixcsv
p2pprocessed = prefixcsv+pathlist[4]+suffixcsv
df = pd.read_csv(p2p)
print(df.columns)
p2prename = {}
for ot in [obj for obj in df.columns if 'ocel:type:' in obj]:
    p2prename[ot] = ot.replace("ocel:type:",'')
df.rename(columns=p2prename,inplace=True)
print(p2prename,df.columns)
df.to_csv(prefixcsv+'p2pprocessed.csv')
object_typesp2p = [ele.replace("ocel:type:",'') for ele in list(df.columns) if 'ocel:type:' in ele]
attrmapp2p = {"obj_names":object_typesp2p,
                        "val_names":[],
                        "act_name":'ocel:activity',
                        "time_name":'ocel:timestamp',
                        "sep":","}
'''
#Create a ocel that fixed the object type syntax error\
#,stores the processed ocel in a new path and return the ocel.
'''def solve_ot_syntaxerror(path,storedpath):
    df = pd.read_csv(path)
    object_types = [ele.replace("ocel:type:",'').replace(":","_") for ele in list(df.columns) if 'ocel:type:' in ele]
    rename = {}
    for ot in [obj for obj in df.columns if 'ocel:type:' in obj]:
        rename[ot] = ot.replace("ocel:type:",'').replace(":","_") 
    df.rename(columns=rename,inplace=True)
    df.to_csv(storedpath)
    attrmap = {"obj_names":object_types,
                            "val_names":[],
                            "act_name":'ocel:activity',
                            "time_name":'ocel:timestamp',
                            "sep":","}
    ocel = csv_import_factory.apply(file_path = storedpath,parameters = attrmap)
    return ocel'''

'''for index, row in enumerate(df.itertuples(), 1):
    print(df.columns,dir(row))
    print('column', df['ocel:type:DEBIT_MEMO_DOC'][:5])
    print(df.at[0,'event_timestamp'])
    getattr(row, 'event_timestamp')
    break'''
#print(df.columns,dir(df))

#The valid test for importing 5 OCELs
'''for i,path in enumerate(pathlist[1:2]):
    ocel = solve_ot_syntaxerror(prefixcsv+path+suffixcsv,prefixcsv+storedpath[i]+suffixcsv)
    ocel = extract_sublog(ocel)
    ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
    ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/"+storedpath[i]+'.png')
'''

#ocel = csv_import_factory.apply(file_path = p2pprocessed,parameters = attrmapp2p)
#ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
#ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/"+pathlist[4]+'.png')
'''path1 = 'github_pm4py.jsonocel'
for path in pathlist:
    completepath = prefix1+path+suffix1
    ocel = ocel_import_factory.apply(completepath)
    ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
    ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/"+path+'.png')'''


'''object_typesBPI = ["application", "offer"]
attrmapBPI = {"obj_names":object_typesBPI,
            "val_names":[],
            "act_name":"event_activity",
            "time_name":"event_timestamp",
            "sep":","}
ELocpa = csv_import_factory.apply(file_path = pathBPI, parameters = attrmapBPI)'''