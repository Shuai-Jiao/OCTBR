import sys
sys.path.append(".")
from model import Flowermodel, create_flower_model, Restrictedmodel
import pm4py
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from token_based_replay import OC_Conformance, OCtokenbasedreplay



path = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCFM/sample_logs/jsonocel/order_process.jsonocel"
ocel = ocel_import_factory.apply(path)
ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
#print(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn)))

#TBR for flowermodel
'''print(OC_Conformance(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn)),pm4py.read_ocel(path)))
print(OCtokenbasedreplay(PNtranslate_PM4PY2OCPA(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn))),ocel))'''

#TBR for origin model
'''print(OC_Conformance(PNtranslate_OCPA2PM4PY(ocpn),pm4py.read_ocel(path)))
print(OCtokenbasedreplay(ocpn,ocel))'''
#print(OCtokenbasedreplay(create_flower_model(ocpn,ocpn.object_types),ocel))

#TBR for restricted model
print(OC_Conformance(Restrictedmodel(PNtranslate_OCPA2PM4PY(ocpn),pm4py.read_ocel(path)),pm4py.read_ocel(path)))
print(OCtokenbasedreplay(PNtranslate_PM4PY2OCPA(Restrictedmodel(PNtranslate_OCPA2PM4PY(ocpn),pm4py.read_ocel(path))),ocel))