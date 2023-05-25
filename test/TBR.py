import sys
sys.path.append(".")
from model import Flowermodel, create_flower_model, Restrictedmodel
from preprocessing import PreprocessCSV
import pm4py
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA
from token_based_replay import OC_Conformance, OCtokenbasedreplay
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory


path = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCEM/sample_logs/jsonocel/order_process.jsonocel"
ocel = ocel_import_factory.apply(path)
ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/orderprocessPN.png")
print(OCtokenbasedreplay(ocpn,ocel))
#print(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn)))

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