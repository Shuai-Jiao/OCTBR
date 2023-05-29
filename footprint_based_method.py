import pm4py
from pm4py.visualization.common import gview
import numpy as np
import itertools
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery
from pm4py.visualization.common import gview
from multiset import *
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
from ocpa.objects.log.importer.csv import factory as csv_import_factory
import sympy as sp

from model import decomposeOCPN
#from visualization import MergeOCFM

def OCEL2OCFM(ocel):
    otlist = pm4py.ocel_get_object_types(ocel)
    flatocfmlist = {}
    for ot in otlist:
        flatlog = pm4py.ocel_flattening(ocel, ot)
        flatocfm = footprints_discovery.apply(flatlog, variant=footprints_discovery.Variants.ENTIRE_EVENT_LOG)
        flatocfmlist[ot] = flatocfm
    return flatocfmlist

# Accept a decomposed ocpn as input!
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
        
# conformed and conforming are both a dictionary, keyed by ot:str, the items are\
# the list of ocfm.
# ocfm is a dictionary, keyed by relation:str, items are pair of activities. 
# weight: Dict(pair:Tuple, weight:float)       
def CompareOCFM(conformed,conforming,weight): # parameters are ocfm
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
                    conform += weight[pair1]
            conflictele = list(set(conflictele)-set([pair1]))
        
        for pair1 in ocfm1['parallel']:
            for pair2 in conforming[ot1]['parallel']:
                if pair1 == pair2:
                    conform += weight[pair1]
            
            for pair2 in conforming[ot1]['sequence']:
                #Consider for a special case that (act,act) belongs to both sequence and parallel
                if pair1[0] == pair1[1]:
                    if pair1 == pair2:
                        conform += weight[pair1]
                else:
                    #Count half of importance, when parallel conformed by sequence.
                    if pair1 == pair2:
                        conform += 0.5*weight[pair1]
            conflictele = list(set(conflictele)-set([pair1]))
                    
        nonconflicttotal = sum([weight[act] for act in ocfm1['sequence']])+sum([weight[act] for act in ocfm1['parallel']])         
        seq = sum([weight[act] for act in ocfm1['sequence']])   
        
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


def Learningweight(ocel_ocpa,logocfm,modelocfm,epoch=1,rate=0.2,learning='learn_weight'):
    ocpn = ocpn_discovery_factory.apply(ocel_ocpa, parameters={"debug": False})
    tarprec, tarfit = quality_measure_factory.apply(ocel_ocpa, ocpn)
    #Initialize symbolic variables for sympy calculation
    fitnesssymweight = {}
    precisionsymweight = {}
    fitnessweightderivative = {}
    precisionweightderivative = {}
    for ot,ocfm in logocfm.items():
        activities = sorted(list(set(activities)|set(ocfm['activities'])))
    weightkey = list(itertools.product(activities,activities))
    for i,w in enumerate(weightkey):
        print('create variables------')
        fitnesssymweight[w] = sp.symbols('w_'+str(i))
        precisionsymweight[w] = sp.symbols('w_'+str(i))
    nonconflicttotal, conform, _ = CompareOCFM(logocfm,modelocfm,fitnesssymweight)
    predfit = conform/(nonconflicttotal+1)
    print('Loss fct-----')
    difffit = Lossfunction(predfit,tarfit) 
    nonconflicttotal, conform, _ = CompareOCFM(modelocfm,logocfm,precisionsymweight)
    predprec = conform/(nonconflicttotal+1)
    diffprec = Lossfunction(predprec,tarprec) 
    print('perform differentiation-----')
    for i,w in enumerate(weightkey):
        fitnessweightderivative[w] = sp.diff(difffit,fitnesssymweight[w])
        precisionweightderivative[w] = sp.diff(diffprec,precisionsymweight[w])
    #perform gradient descent
    for _ in range(epoch):
        print('epoch start-----')
        #update the weight (from symbolic value to symbolic expression)
        for w in enumerate(weightkey):
            fitnesssymweight[w] += rate*fitnessweightderivative[w]
            precisionsymweight[w] += rate*precisionweightderivative[w]

def Lossfunction(pred,tar,variant='squared error'):
    if variant == 'squared error':
        return 1/2*(pred-tar)**2
    else:
        raise ValueError(f'{variant} is not valid')    


def Evaluation(ocel,ocpn,threshold = 0.05):   
    ocpnlist = decomposeOCPN(ocpn)
    ocfmmodel = OCPN2OCFM(ocpnlist)
    ocfmlog = OCEL2OCFM(ocel)
    for ot in pm4py.ocel_get_object_types(ocel):
        ocfmlog[ot] = pm4py.filter_variants_by_coverage_percentage(ocfmlog[ot], threshold)
    #gviz1=MergeOCFM(ocfmmodel)
    #gviz2=MergeOCFM(ocfmlog)
    #gview.view(gviz1)
    #gview.view(gviz2)
    result = EvalOCFM(ocfmlog,ocfmmodel)
    return result
