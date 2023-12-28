import sys
sys.path.append(".")
from model import Restrictedmodel, create_flower_model
from translation import PNtranslate_PM4PY2OCPA, PNtranslate_OCPA2PM4PY
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
import pm4py
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.append(parent_dir)
 

path = parent_dir+"/sample_logs/jsonocel/order_process.jsonocel"
ocel = ocel_import_factory.apply(path)
ocel1 = pm4py.read_ocel(path)
ocpapn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
# No matter use ocpa->pm4py->ocpa or pm4py->ocpa the wrong results are the same\
# so the problem should be located at the conversion from pm4py to ocpa
#flower = Flowermodel(PNtranslate_OCPA2PM4PY(ocpapn))
restrict = Restrictedmodel(ocel)
#print(quality_measure_factory.apply(ocel, PNtranslate_PM4PY2OCPA(flower)))
#restrict = PNtranslate_OCPA2PM4PY(Restrictedmodel(ocel))
#print('-------',type(ocel.log.log))
#flower1 = create_flower_model(ocpapn,ocpapn.object_types)
print(quality_measure_factory.apply(ocel, restrict))
ocpn_vis_factory.save(ocpn_vis_factory.apply(restrict), "./test/restrict.png")
#ocpn_vis_factory.save(ocpn_vis_factory.apply(flower1), "./test/flower1.png")