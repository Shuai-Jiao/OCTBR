import sys
sys.path.append(".")
from model import Flowermodel, create_flower_model, Restrictedmodel,decomposeOCPN
from preprocessing import PreprocessCSV, solve_ot_syntaxerror, parse_sublog
import pm4py
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA, ELtranslate_OCPA2PM4PY
from token_based_replay import OC_Conformance, OCtokenbasedreplay
from footprint_based_method import OCEL2OCFM, OCPN2OCFM, EvalOCFM
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
import time
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

prefix1 = './sample_logs/jsonocel/'
prefix2 = "/Users/jiao.shuai.1998.12.01outlook.com/Downloads/OCEL/jsonocel/"
# running-example and windows_events have only one case, but too big! filtering is not possible
datalist = ['transfer_order','github_pm4py','o2c','p2p','recruiting','running-example','windows_events']
suffix = '_sublog.jsonocel'

for data in datalist[:-2]:
    #ocel = solve_ot_syntaxerror(prefix1+data+suffix,prefix2+storedpath[i]+suffix)
    #ocel = extract_sublog(ocel)
    print('hi------',data)
    #time0 = time.time()
    #ocel = ocel_import_factory.apply(prefix1+data+suffix)
    ocel = parse_sublog(prefix1+data+suffix)
    ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False}) 
    #ocpn = PNtranslate_OCPA2PM4PY(ocpn)
    #ocpn_vis_factory.save(ocpn_vis_factory.apply(ocpn), "./test/orderprocessPN.png")]
    time1 = time.time()
    fit1 , prec1 = OC_Conformance(PNtranslate_OCPA2PM4PY(ocpn),ELtranslate_OCPA2PM4PY(ocel),'token-based',True)
    #prec, fit = quality_measure_factory.apply(ocel,ocpn)
    '''ocpn1 = decomposeOCPN(PNtranslate_OCPA2PM4PY(ocpn))
    ocfmmodel = OCPN2OCFM(ocpn1)
    ocfmlog = OCEL2OCFM(ELtranslate_OCPA2PM4PY(ocel))
    fit,_,_ = EvalOCFM(ocfmlog,ocfmmodel)
    _,prec,_ = EvalOCFM(ocfmlog,ocfmmodel)'''
    time2 = time.time()
    fit2, prec2 = OC_Conformance(PNtranslate_OCPA2PM4PY(ocpn),ELtranslate_OCPA2PM4PY(ocel),'token-based',True,'fraction')
    time3 = time.time()
    print('average flattened TBR: time, fit, prec: ',time2-time1, fit1, prec1)
    print('fractional flattened TBR: time, fit, prec: ',time3-time2, fit2, prec2)
    #print('context&binding time fit prec:',time2-time1,fit1,prec1)
    #print('OCtokenbased-------',OCtokenbasedreplay(ocpn,ocel))
    #print('Im here~~~~~~~~~~~~~')
    
    #print('flattened TBR-------',OC_Conformance(PNtranslate_OCPA2PM4PY(ocpn),ELtranslate_OCPA2PM4PY(ocel)))
    #print(Flowermodel(PNtranslate_OCPA2PM4PY(ocpn)))
    #time3 = time.time()
    #print(data,'parsed time:',time1-time0,', OC TBR:',time2-time1,', F TBR:',time3-time2)