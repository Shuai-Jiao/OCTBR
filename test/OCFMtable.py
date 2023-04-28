
import sys
sys.path.append(".")
from footprint_based_method import OCEL2OCFM, OCPN2OCFM, EvalOCFM
from model import decomposeOCPN
from translation import PNtranslate_OCPA2PM4PY
from visualization import MergeOCFM
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
from pm4py.visualization.common import gview
import pm4py

path1 = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCFM/sample_logs/jsonocel/order_process.jsonocel"
ocel1 = ocel_import_factory.apply(path1)
ocel1a = pm4py.read_ocel(path1)
ocpn1 = ocpn_discovery_factory.apply(ocel1, parameters={"debug": False})
ocpn = decomposeOCPN(PNtranslate_OCPA2PM4PY(ocpn1))
ocfmmodel = OCPN2OCFM(ocpn)
ocfmlog = OCEL2OCFM(ocel1a)
fit,_,_ = EvalOCFM(ocfmlog,ocfmmodel)
_,prec,_ = EvalOCFM(ocfmlog,ocfmmodel)
print(fit,prec)
#print(ocfmmodel)
#print(ocpn)

ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn1), "./test/oc_petri_net.png")
gviz = MergeOCFM(ocfmmodel)
gviz1 =  MergeOCFM(ocfmlog)
gview.view(gviz)
gview.view(gviz1)