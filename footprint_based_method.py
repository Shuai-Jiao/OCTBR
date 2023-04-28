import pm4py
from pm4py.visualization.common import gview
import numpy as np
import itertools
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery
from pm4py.visualization.common import gview
from multiset import *

def OCEL2OCFM(ocel):
    otlist = pm4py.ocel_get_object_types(ocel)
    flatocfmlist = {}
    for ot in otlist:
        flatlog = pm4py.ocel_flattening(ocel, ot)
        flatocfm = footprints_discovery.apply(flatlog, variant=footprints_discovery.Variants.ENTIRE_EVENT_LOG)
        flatocfmlist[ot] = flatocfm
    return flatocfmlist

def OCPN2OCFM(ocpnlist):
    ocfmlist = {}
    for ot, ocpn in ocpnlist.items():
        ocfm = footprints_discovery.apply(ocpn[0], ocpn[1], ocpn[2],variant=footprints_discovery.Variants.PETRI_REACH_GRAPH)
        ocfmlist[ot] = ocfm
    return ocfmlist

def EvalOCFM(logocfm,modelocfm): #ocfm1 and ocfm2 are both lists
    nonconflicttotal, conform, _ = CompareOCFM(logocfm,modelocfm)
    # nonconflicttotal+1 to ensure nonconflicttotal is not 0
    fitness = conform/(nonconflicttotal+1)
    nonconflicttotal, conform, seqratio = CompareOCFM(modelocfm,logocfm)
    precision = conform/(nonconflicttotal+1)
    simplicity = 1-1/(1 + np.exp(-10*seqratio+7)) #offset to 7
    return fitness, precision, simplicity 
        
        
def CompareOCFM(conformed,conforming): # parameters are ocfm
    nonconflicttotal = 0
    conform = 0
    seq = 0
    activities = []
    
    for ot,ocfm in conformed.items():
        activities = sorted(list(set(activities)|set(ocfm['activities'])))
    allele = list(itertools.product(activities,activities))
    #total = len(list(conformed['activities'])**2
    conflictele = allele
                
    for ot1,ocfm1 in conformed.items():
        for pair1 in ocfm1['sequence']:
            for pair2 in conforming[ot1]['sequence']|conforming[ot1]['parallel']:
                if pair1 == pair2:
                    conform += 1
            conflictele = list(set(conflictele)-set([pair1]))
        
        for pair1 in ocfm1['parallel']:
            for pair2 in conforming[ot1]['parallel']:
                if pair1 == pair2:
                    conform += 1
            
            for pair2 in conforming[ot1]['sequence']:
                if pair1[0] == pair1[1]:
                    if pair1 == pair2:
                        conform += 1
                else:
                    if pair1 == pair2:
                        conform += 0.5
            conflictele = list(set(conflictele)-set([pair1]))
                    
        nonconflicttotal += (len(ocfm1['sequence'])+len(ocfm1['parallel']))           
        seq += len(ocfm1['sequence'])    
        
    return nonconflicttotal, conform, seq/(nonconflicttotal+len(conflictele))

def EvalbyOCFM(ocel,parameters=None):
    '''Suspended work'''
    if parameters == None:
        ocpn = pm4py.discover_oc_petri_net(ocel)
        ocpnlist = decomposeOCPN(ocpn)
        ocfm1 = OCPN2OCFM(ocpnlist)
        ocfm2 = OCEL2OCFM(ocel)
        print(EvalOCFM(ocfm1,ocfm2))
    else:
        raise ValueError("Parameter configuration is not done so far")


def Evaluation(ocel,ocpn):
    ocpnlist = decomposeOCPN(ocpn)
    ocfmmodel = OCPN2OCFM(ocpnlist)
    ocfmlog = OCEL2OCFM(ocel)
    gviz1=MergeOCFM(ocfmmodel)
    gviz2=MergeOCFM(ocfmlog)
    gview.view(gviz1)
    gview.view(gviz2)
    result = EvalOCFM(ocfmlog,ocfmmodel)
    return result