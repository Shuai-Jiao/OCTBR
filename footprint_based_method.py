import pm4py
from pm4py.visualization.common import gview
import numpy as np
import itertools
import copy
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery
from pm4py.visualization.common import gview
from multiset import *
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
from ocpa.objects.log.importer.csv import factory as csv_import_factory
import sympy as sp
from preprocessing import create_training_set
from model import decomposeOCPN
from translation import ELtranslate_OCPA2PM4PY, PNtranslate_OCPA2PM4PY

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
        # mistake? here used to be nonconflicttotal = sum([weight[act] for act in ocfm1['sequence']])+sum([weight[act] for act in ocfm1['parallel']])
        nonconflicttotal += sum([weight[act] for act in ocfm1['sequence']])+sum([weight[act] for act in ocfm1['parallel']])         
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

# the learningweight should receive a training data and return the weight of each relation
# input activity to avoid non-occurred relation
# Use the numerical instead of symbolic differentiation (sympy)!!! First, it is inefficient. Second,\
# not that useful for gradient descent!
def Learningweight(ocel_list,activities,epoch=1,rate=0.2,weightdelta=0.001,learning='learn_weight'):
    from visualization import MergeOCFM
    # Initialize symbolic variables for sympy calculation
    fitnessweight = {}
    precisionweight = {}
    fitnesserrorderivative = {}
    precisionerrorderivative = {}
    # To ensure the order of the relation
    activities = sorted(activities)
    relation_pair = list(itertools.product(activities,activities))
    for i,w in enumerate(relation_pair):
        #print('create variables------')
        #the weights should not be symetric
        fitnessweight[w] = 1
        precisionweight[w] = 1
    for ocel in ocel_list:
        ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": False})
        print('start context and binding:-----',type(ocel),type(ocpn))
        tarprec, tarfit = quality_measure_factory.apply(ocel, ocpn)
        print('finish context and binding:-----')
        #BUT the ocel is in ocpa! not in pm4py!
        logocfm = OCEL2OCFM(ELtranslate_OCPA2PM4PY(ocel,'./sample_logs/jsonocel/intermediate.jsonocel'))
        modelocfm = OCPN2OCFM(decomposeOCPN(PNtranslate_OCPA2PM4PY(ocpn)))
        '''gviz1=MergeOCFM(logocfm)
        gviz2=MergeOCFM(modelocfm)
        gview.view(gviz1)
        gview.view(gviz2)'''
        # now the issue is that conform is 0
        nonconflicttotal, conform, _ = CompareOCFM(logocfm,modelocfm,fitnessweight)
        predfit = conform/(nonconflicttotal)
        #print('Loss fct-----')
        fiterror = Lossfunction(predfit,tarfit) 
        nonconflicttotal, conform, _ = CompareOCFM(modelocfm,logocfm,precisionweight)
        predprec = conform/(nonconflicttotal)
        precerror = Lossfunction(predprec,tarprec) 
        #print('perform differentiation-----')
        #print('compare quality---',tarfit,tarprec,predfit,predprec)
        #print('error check:---',fiterror,precerror)

        # compute the derivative in terms of all the weights
        for _ in range(epoch):
            print('epoch start-----')
            for w in relation_pair:
                fitnessweightdiff = copy.deepcopy(fitnessweight)
                fitnessweightdiff[w] += weightdelta
                precisionweightdiff = copy.deepcopy(precisionweight)
                precisionweightdiff[w] += weightdelta
                nonconflicttotal, conform, _ = CompareOCFM(logocfm,modelocfm,fitnessweightdiff)
                fitdelta = conform/(nonconflicttotal)
                nonconflicttotal, conform, _ = CompareOCFM(modelocfm,logocfm,precisionweight)
                precdelta = conform/(nonconflicttotal)
                fiterrordelta = Lossfunction(fitdelta,tarfit)
                precerrordelta = Lossfunction(precdelta,tarprec)
                #print('error check:---',fiterrordelta,fiterror,precerrordelta,precerror)
                                
                fitnesserrorderivative[w] = (fiterrordelta-fiterror)/weightdelta
                precisionerrorderivative[w] = (precerrordelta-precerror)/weightdelta
                #perform gradient descent
                #update the weight (from symbolic value to symbolic expression)
                # the last term should be the partial derivative of the error function!!!
                fitnessweight[w] += rate*fitnesserrorderivative[w]
                precisionweight[w] += rate*precisionerrorderivative[w]
        #print('check weight-----',fitnessweight,precisionweight)
    return fitnessweight, precisionweight

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
