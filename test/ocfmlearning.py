import sys
sys.path.append(".")
from footprint_based_method import OCEL2OCFM, OCPN2OCFM, Learningweight, EvalOCFM
from preprocessing import solve_ot_syntaxerror, create_training_set
from translation import PNtranslate_OCPA2PM4PY
from model import decomposeOCPN
from ocpa.objects.log.importer.csv import factory as csv_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
import pm4py

pathlist = ['github_pm4py','o2c','p2p','recruiting','running-example','transfer_order','windows_events']
prefixcsv = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/csv/"
suffixcsv = ".csv"
path = prefixcsv+pathlist[2]+suffixcsv
ocel =  pm4py.read_ocel(path)
#print(ocel.events.columns,'---',ocel.objects.columns,'---',ocel.relations.columns)
#print(ocel.events[:2],'---',ocel.objects[:2],'---',ocel.relations[:2])
#print('---',ocel.objects['ocel:type'].unique())

#ocelocpa = csv_import_factory(solve_ot_syntaxerror(path,prefixcsv+pathlist[2]+'processed'+suffixcsv))
#model = pm4py.discover_oc_petri_net(ocel)
#pm4py.view_ocpn(model, format="png")
ocelocpa = solve_ot_syntaxerror(path,prefixcsv+pathlist[2]+'processed'+suffixcsv)
ocpnocpa = ocpn_discovery_factory.apply(ocelocpa, parameters={"debug": False})
ocpnpm4py = PNtranslate_OCPA2PM4PY(ocpnocpa)
#print(EvalOCFM(OCEL2OCFM(ocel),OCPN2OCFM(decomposeOCPN(ocpnpm4py))))
print('start learning----ß')
#print('variants in ocel:----',ocelocpa.process_executions,len(ocelocpa.process_executions))
traininglist = create_training_set(ocelocpa)
'''for ocel in traininglist:
    print('number of variants:',len(ocel.process_executions),'\n------',ocel.process_executions)'''
Learningweight(traininglist,list(ocelocpa.obj.activities))


