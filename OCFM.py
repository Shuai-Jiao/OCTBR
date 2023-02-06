
import matplotlib
import pm4py
import os
import tempfile
from pm4py.visualization.common import gview
from graphviz import Source
from pm4py.util import exec_utils
import matplotlib.pyplot as plt
import numpy as np
import math
import itertools
from pm4py.visualization.footprints import visualizer as fp_visualizer
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery
from pm4py.objects.petri_net import obj as objpm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
from pm4py.objects.petri_net.utils import petri_utils

def OCEL2OCFM(ocel):
    otlist = pm4py.ocel_get_object_types(ocel)
    flatocfmlist = {}
    for ot in otlist:
        flatlog = pm4py.ocel_flattening(ocel, ot)
        flatocfm = footprints_discovery.apply(flatlog, variant=footprints_discovery.Variants.ENTIRE_EVENT_LOG)
        flatocfmlist[ot] = flatocfm
    return flatocfmlist


def GetOCPN(ocpn):
    integ = {'places':[],'transitions':[],'arcs':[]}
    for ot in ocpn['object_types']:
        integ['places'] += ocpn['petri_nets'][ot][0]['places']
        integ['transitions'] += ocpn['petri_nets'][ot]['transitions']
        integ['arcs'] += ocpn['petri_nets'][ot]['arcs']
        #integ['places'] += ocpn['petri_nets'][ot]['places']
    return integ


def decomposeOCPN(model):
    modellist = {}
    for key in model['petri_nets'].keys():
        net = model['petri_nets'][key][0]
        im = model['petri_nets'][key][1]
        fm = model['petri_nets'][key][2]
        demodel = (net,im,fm)
        modellist[key] = demodel
    return modellist


def OCPN2OCFM(ocpnlist):
    ocfmlist = {}
    for ot, ocpn in ocpnlist.items():
        ocfm = footprints_discovery.apply(ocpn[0], ocpn[1], ocpn[2])   
        ocfmlist[ot] = ocfm
    return ocfmlist


def MergeOCFM(ocfmlist,variablity = False):
    UNKNOWN_SYMBOL = "&#63;"
    XOR_SYMBOL = "&#35;"
    PREV_SYMBOL = "&#60;"
    SEQUENCE_SYMBOL = "&#62;"
    PARALLEL_SYMBOL = "||"
    
    activities = []
    for ot,ocfm in ocfmlist.items():
        #print(ocfm)
        activities = sorted(list(set(activities)|set(ocfm['activities'])))
    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    
    integratedtable = ["digraph {\n", "tbl [\n", "shape=plaintext\n", "label=<\n"]
    integratedtable.append("<table border='0' cellborder='1' color='blue' cellspacing='0'>\n")
    integratedtable.append("<tr><td></td>")
    for act in activities:
        integratedtable.append("<td><b>"+act+"</b></td>")
    integratedtable.append("</tr>\n")
    for a1 in activities:
        integratedtable.append("<tr><td><b>"+a1+"</b></td>")
        for a2 in activities:
            symb_1 = "?"
            symb_2 = "?"
            relation = "{"
            conflict = True
            for ot, ocfm in ocfmlist.items():
                '''if a1 in activities and a2 in activities:
                    symb_1 = XOR_SYMBOL'''
                if (a1, a2) in ocfm["parallel"]:
                    symb_1 = PARALLEL_SYMBOL
                    conflict = False
                elif (a1, a2) in ocfm["sequence"]:
                    symb_1 = SEQUENCE_SYMBOL
                    conflict = False
                elif (a2, a1) in ocfm["sequence"]:
                    symb_1 = PREV_SYMBOL
                    conflict = False
                symb = symb_1+"<sup>"+ot+"</sup>"
                relation += (symb+',')
            if conflict == True:
                relation = XOR_SYMBOL
            else:
                relation = relation[:-1]+'}'
            integratedtable.append("<td><font color=\"black\">"+ relation +"</font></td>")
        integratedtable.append("</tr>\n")
    integratedtable.append("</table>\n")
    integratedtable.append(">];\n")
    integratedtable.append("}\n")

    integratedtable = "".join(integratedtable)
    
    image_format = exec_utils.get_param_value("format", None, "png")
    gviz = Source(integratedtable, filename=filename.name)
    gviz.format = image_format

    return gviz

def EvalOCFM(logocfm,modelocfm): #ocfm1 and ocfm2 are both lists
    nonconflicttotal, conform, _ = CompareOCFM(logocfm,modelocfm)
    precision = conform/nonconflicttotal
    nonconflicttotal, conform, seqratio = CompareOCFM(modelocfm,logocfm)
    fitness = conform/nonconflicttotal
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
                    
        nonconflicttotal += (len(ocfm1['sequence'])+len(ocfm1['parallel']))           
        seq += len(ocfm1['sequence'])    
        
    return nonconflicttotal, conform, seq/(nonconflicttotal+len(conflictele))

def EvalbyOCFM(ocel,parameters=None):
    if parameters == None:
        ocpn = pm4py.discover_oc_petri_net(ocel)
        ocpnlist = decomposeOCPN(ocpn)
        ocfm1 = OCPN2OCFM(ocpnlist)
        ocfm2 = OCEL2OCFM(ocel)
        print(EvalOCFM(ocfm1,ocfm2))
    else:
        raise ValueError("Parameter configuration is not done so far")


def PNtranslate_OCPA2PM4PY(pnocpa):
    
    #construct key 'petri_nets'
    pnpm4py = {}
    pnpm4py['object_types']=set()
    pnpm4py['activities']=set()
    pnpm4py['petri_nets']={}
    
    #extract all the type to create the key first!!
    pnpm4py['object_types'] = set()
    for pl in pnocpa.places:
        pnpm4py['object_types'].add(pl.object_type)
    for ot in list(pnpm4py['object_types']):
        pnpm4py['petri_nets'][ot] = []
        #here you cannot use [_,_,_] because all the _ refer to the last cashed values!
        pnpm4py['petri_nets'][ot].append(objpm4py.PetriNet())
        
    '''here we assumed the initial marking only contain one token'''
    s = {}
    t = {}
    for pl in pnocpa.places:
        #place = objpm4py.PetriNet.Place(pl.name,pl.in_arcs,pl.out_arcs)
        if pl.initial:
            place = objpm4py.PetriNet.Place('source')
            
        elif pl.final:
            place = objpm4py.PetriNet.Place('sink')
            
        else:
            place = objpm4py.PetriNet.Place(pl.name)
        pnpm4py['petri_nets'][pl.object_type][0].places.add(place)
    #for ot in list(pnpm4py['object_types']):
        
    #find how arcs defined, use this relation to specify the type
    for tr in pnocpa.transitions:
        #print(tr.label)
        trantype = set()
        if not tr.silent:
            pnpm4py['activities'].add(tr.name)
        for ar in pnocpa.arcs:
            if ar.source == tr:
                trantype.add(ar.target.object_type)
            if ar.target == tr:
                trantype.add(ar.source.object_type)
        if tr.silent:
            label = None
        else:
            label = tr.name
        for ot in list(trantype):
            #'label' is the same as 'name' here, otherwise the label will be empty and the net will not be labelled.
            transition = objpm4py.PetriNet.Transition(tr.name,label)
            pnpm4py['petri_nets'][ot][0].transitions.add(transition)
    for ar in pnocpa.arcs:
        
        if type(ar.source)==objocpa.ObjectCentricPetriNet.Place:
            ot = ar.source.object_type
            issourceplace = True
        else:
            ot = ar.target.object_type
            issourceplace = False
        #find out the respective source and target       
        source = Returncorrespondence(ar.source,pnpm4py['petri_nets'][ot][0])
        target = Returncorrespondence(ar.target,pnpm4py['petri_nets'][ot][0])
        petri_utils.add_arc_from_to(source, target, pnpm4py['petri_nets'][ot][0])
        print(target,target.out_arcs,'target out')
    #because the error reports missing key value: activities
    #print(pnpm4py['activities'])
    for ot in list(pnpm4py['object_types']):       
        for pl in pnpm4py['petri_nets'][ot][0].places:
            if pl.name == 'source':
                s[ot] = objpm4py.Marking()            
                s[ot][pl] = 1
                print(pl.out_arcs,pl.in_arcs)
            if pl.name == 'sink':
                t[ot] = objpm4py.Marking()     
                t[ot][pl] = 1
                print(pl.out_arcs,pl.in_arcs)
        
        pnpm4py['petri_nets'][ot].extend([s[ot],t[ot]])
        pnpm4py['petri_nets'][ot]=tuple(pnpm4py['petri_nets'][ot])
        
    
    #keyerror for 'double_arcs_on_activity'
    pnpm4py['double_arcs_on_activity']={}
    for ot in pnpm4py['object_types']:
        pnpm4py['double_arcs_on_activity'][ot]={}
        for act in pnpm4py['activities']:
             pnpm4py['double_arcs_on_activity'][ot][act] = Activityvariability(act,pnocpa)
       
    return pnpm4py

#arg: pm4py net, return: pm4py place/transition
def Returncorrespondence(ele,net):
    if type(ele) == objocpa.ObjectCentricPetriNet.Place:
        if ele.initial:
            for pl in net.places:
                if pl.name == 'source':
                    return pl
        elif ele.final:
            for pl in net.places:
                if pl.name == 'sink':
                    return pl
        else:
            for pl in net.places:
                if pl.name == ele.name:
                    return pl
    elif type(ele) == objocpa.ObjectCentricPetriNet.Transition:
        for tr in net.transitions:
            if tr.name == ele.name:
                return tr
            
def Activityvariability(act,net):
    for arc in net.arcs:
        if (arc.source.name == act or arc.target.name == act) and arc.variable == True:
            return True
    return False



if __name__ == "__main__":
    path = './OCEL/running-example.jsonocel'
    ocel = pm4py.read_ocel(path)
    ocpn = pm4py.discover_oc_petri_net(ocel)
    ocpnlist = decomposeOCPN(ocpn)
    ocfmmodel = OCPN2OCFM(ocpnlist)
    ocfmlog = OCEL2OCFM(ocel)
    result = EvalOCFM(ocfmlog,ocfmmodel)
    print('The fitness is: ',result[0],'\nThe precision is: ',result[1],'\nThe simplicity is: ',result[2])

  