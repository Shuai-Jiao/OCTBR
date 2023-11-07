import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
#simply sys.path.append(".") doesn't always work!!! not work in cluster.

#sys.path.append(".")
#import pm4py.objects
#print('import ~~~pm4py.objects')
#import pm4py.objects.petri_net
#print('import ~~~pm4py.objects.petri_net')
from model import Flowermodel, create_flower_model, Restrictedmodel
from preprocessing import PreprocessCSV, solve_ot_syntaxerror, parse_sublog

from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OC_Conformance, OCtokenbasedreplay
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

#path = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCEM/sample_logs/jsonocel/order_process.jsonocel"
prefix1 = '/sample_logs/jsonocel/'
prefix2 = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/jsonocel/"
datalist = ['transfer_order','github_pm4py','o2c','p2p','recruiting','running-example','windows_events','order_process','p2p-normal']
suffix1 = '_sublog.jsonocel'
suffix2 = ".jsonocel"

for data in datalist[-2:-1]:
    #ocel = solve_ot_syntaxerror(prefix1+data+suffix,prefix2+storedpath[i]+suffix)
    #ocel = extract_sublog(ocel)
    path = parent_dir+prefix1+data+suffix2
    
    print('hi------',path)
    
    time0 = time.time()
    #ocel = ocel_import_factory.apply(prefix1+data+suffix)
    #ocel = parse_sublog(prefix2+data+suffix2)
    ocel = ocel_import_factory.apply(path)
    print(ocel is None)
    ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False}) 
    #ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/orderprocessPN.png")]
    time1 = time.time()
    print('OCtokenbased-------',OCtokenbasedreplay(ocpn,ocel))
    print('Im here~~~~~~~~~~~~~')
    time2 = time.time()
    print('flattened TBR-------',OC_Conformance(PNtranslate_OCPA2PM4PY(ocpn),ELtranslate_OCPA2PM4PY(ocel)))
    #print(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn)))
    time3 = time.time()
    print(data,'parsed time:',time1-time0,', OC TBR:',time2-time1,', F TBR:',time3-time2)
    
    print('ground truth(p,f):-------',quality_measure_factory.apply(ocel, ocpn))
    time4 = time.time()
    print('running time for context&binding',time4-time3)
#Test BPI data
'''path1 =  "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCEM/sample_logs/csv/BPI2017-Final.csv"
ocel1 = PreprocessCSV(path1,'ELocpa')
ocpn1 = ocpn_discovery_factory.apply(ocel1, parameters={"debug": False})
ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn1), "./test/BPI2017.png")
print(OCtokenbasedreplay(ocpn1,ocel1))'''

#TBR for flowermodel
'''print(OC_Conformance(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn)),pm4py.read_ocel(path)))
print(OCtokenbasedreplay(PNtranslate_PM4PY2OCPA(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn))),ocel))'''

#TBR for origin model
#print(OC_Conformance(PNtranslate_OCPA2PM4PY(ocpn1),PreprocessCSV(path1,'ELpm4py')))
#print(OCtokenbasedreplay(ocpn,ocel))
#print(OCtokenbasedreplay(create_flower_model(ocpn,ocpn.object_types),ocel))

#TBR for restricted model
'''print(OC_Conformance(PNtranslate_OCPA2PM4PY(Restrictedmodel(ocel)),pm4py.read_ocel(path)))
print(OCtokenbasedreplay(Restrictedmodel(ocel),ocel))'''