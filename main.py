import matplotlib
import pm4py
import os
import tempfile
from pm4py.visualization.common import gview
from graphviz import Source
from pm4py.util import exec_utils
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import math
import itertools
from pm4py.visualization.footprints import visualizer as fp_visualizer
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery
import datetime
import pandas as pd
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.visualization.common import gview
from pm4py.objects.petri_net import obj as objpm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory


def ParsingCSV(csvpath, parameters=None):
    csvlog = pd.read_csv(csvpath,sep=';')
    for ot in parameters['object_type']:
        csvlog[ot] = csvlog[ot].map(lambda x: str([y.strip() for y in x.split(',')]) if isinstance(x,str) else str([]))
        
    csvlog["event_id"] = list(range(0,len(csvlog)))
    csvlog.index = list(range(0,len(csvlog)))
    csvlog["event_id"] = csvlog["event_id"].astype(float).astype(int)
    csvlog = csvlog.rename(columns={"event_id": 'ocel:eid', parameters['time_name']:'ocel:timestamp',\
    parameters['act_name']:'ocel:activity'})
    for ot in parameters['object_type']:
        csvlog = csvlog.rename(columns={ot:str('ocel:type:'+ot)})
    '''Warnining: the previous timestamp should be determined whether an integer is'''
    csvlog['ocel:timestamp'] = [str(datetime.datetime.fromtimestamp(x))\
                                for x in csvlog['ocel:timestamp']]
    return csvlog

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
                else:
                    continue
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
    fitness = conform/nonconflicttotal
    nonconflicttotal, conform, seqratio = CompareOCFM(modelocfm,logocfm)
    precision = conform/nonconflicttotal
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

def Flowermodel(model):
    ocpn = model
    activitytype = {}
    for act in model['activities']:
        activitytype[act]=[]
        for ot in model['object_types']:
            for ele in list(model['petri_nets'][ot][0].transitions):
                if act==ele.label:
                    activitytype[act].append(ot)
    objecttype = model['object_types']
    
    places = {}
    transitions = {}
    im,fm = Marking(),Marking()
    for ot in objecttype:
        net = PetriNet(ot)
        places[ot] = PetriNet.Place(ot)
        net.places.add(places[ot])
        im[places[ot]] = 1
        fm[places[ot]] = 1
        
        for trans in activitytype.keys():
            for ot2 in activitytype[trans]: 
                if ot2 == ot:
                    transitions[trans] = PetriNet.Transition(trans,trans)
                    net.transitions.add(transitions[trans])
                    petri_utils.add_arc_from_to(places[ot],transitions[trans],net)
                    petri_utils.add_arc_from_to(transitions[trans],places[ot],net)    
        ocpn['petri_nets'][ot] = [net,im,fm]
    return ocpn

def Restrictedmodel(model,ocel):
    for ot in model['object_types']:
        flat_log = pm4py.ocel_flattening(ocel, ot)
        onetracelog = flat_log.loc[flat_log['case:concept:name'] == flat_log['case:concept:name'][0]]
        event_log = pm4py.convert_to_event_log(onetracelog)
        net, im, fm = pm4py.discover_petri_net_inductive(event_log)
        model['petri_nets'][ot] = (net,im,fm)
    return model

'''Only places have object type in ocpa, but in pm4py all the sub-petri net are keyed by ot'''
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
            s[pl.object_type] = objpm4py.Marking()            
            s[pl.object_type][place] = 1
        elif pl.final:
            place = objpm4py.PetriNet.Place('sink')
            t[pl.object_type] = objpm4py.Marking()     
            t[pl.object_type][place] = 1
        else:
            place = objpm4py.PetriNet.Place(pl.name)
        pnpm4py['petri_nets'][pl.object_type][0].places.add(place)
            
    for ot in list(pnpm4py['object_types']):
        pnpm4py['petri_nets'][ot].extend([s[ot],t[ot]])
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
            transition = objpm4py.PetriNet.Transition(tr.name,label,tr.in_arcs,tr.out_arcs,tr.properties)
            pnpm4py['petri_nets'][ot][0].transitions.add(transition)
    for ar in pnocpa.arcs:
        if type(ar.source)==objocpa.ObjectCentricPetriNet.Place:
            ot = ar.source.object_type
        else:
            ot = ar.target.object_type
        #find out the respective source and target       
        source = Returncorrespondence(ar.source,pnpm4py['petri_nets'][ot][0])
        target = Returncorrespondence(ar.target,pnpm4py['petri_nets'][ot][0])
        arcs = objpm4py.PetriNet.Arc(source,target,ar.weight,ar.properties)
        pnpm4py['petri_nets'][ot][0].arcs.add(arcs)           
    #because the error reports missing key value: activities
    #print(pnpm4py['activities'])
    for ot in list(pnpm4py['object_types']):
        pnpm4py['petri_nets'][ot]=tuple(pnpm4py['petri_nets'][ot])
    
    #keyerror for 'double_arcs_on_activity'
    pnpm4py['double_arcs_on_activity']={}
    for ot in pnpm4py['object_types']:
        pnpm4py['double_arcs_on_activity'][ot]={}
        for act in pnpm4py['activities']:
             pnpm4py['double_arcs_on_activity'][ot][act] = Activityvariability(act,pnocpa)
       
    return pnpm4py

#arg: pm4py net, return: pm4py place/transition
#return pm4py element
def Returncorrespondence(ele,net,ot=None):
    if type(ele) == objocpa.ObjectCentricPetriNet.Place:
        #Consider the case that net is a translated ocpapn! then\
        #all the place has an extra prefix in name.
        if ot != None:
            for pl in net.places:
                if pl.name in ele.name:
                    return pl 
                
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

#return ocpa element, receive pm4py element. ot is initialized with\
#an unoccurred string, because None is not iterated.
def PNMatching(ele,ocpn,ot=None):
    #The following works
    if type(ele) == objpm4py.PetriNet.Place:
        #print('1')
        for pl in ocpn.places:
            #print(ele.name,pl.name)
            if ele.name in pl.name and ot in pl.name:
                #print('returned')
                return pl
    if type(ele) == objpm4py.PetriNet.Transition:
        #print('2',[(tr.name,tr.label) for tr in ocpn.transitions])
        for tr in ocpn.transitions:
            #already missed
            #print('!!!',tr.name,tr.label,ele.name)
            #Because we renamed the silence, so we need to check the connection\
            #to identify the transition. tr.label is always None! 
            #tr.name is 
            #print(tr.label,ele.name,'---',tr.name,ele.label)
            #the following works
        
            if any(['tau' in str(ele.name),'skip' in str(ele.name),'loop' in str(ele.name)])\
            and tr.label != None and ot != None and ele.name in tr.label and ot in tr.label:
                return tr
                
            elif tr.name == ele.label:
                #print('returned')
                return tr
    
        #print('3')
    #print(type(ele),ele.name,ele.label)
    raise ValueError("No correspondence found")
    return None

def PNtranslate_PM4PY2OCPA(ocpn):
    ocpapn = objocpa.ObjectCentricPetriNet()
    for ot in ocpn['object_types']:
        #first construct places and enrich later
        for pl in ocpn['petri_nets'][ot][0].places:            
            place = objocpa.ObjectCentricPetriNet.Place(ot+pl.name,ot)
            ocpapn.places.add(place)
            #inarc = objocpa.ObjectCentricPetriNet.Arc(target=place)
            
     
    for ot in ocpn['object_types']:
        count = 0
        for tr in ocpn['petri_nets'][ot][0].transitions:         
            tau = False
            #l is used to store the value of slient name for later usage, the new
            #label will be overwritten after the visualization.
            n = tr.label
            l = None
            
            if tr.label == None:
                silent = True
                n = ot+'tau'+str(count)
                count += 1
                #not l=ot+tr.name otherwise the correspondence won't be found
                l = ot+tr.name                 
            transition = objocpa.ObjectCentricPetriNet.Transition(name=n,label=l\
                                                                 ,silent=tau)
            ocpapn.transitions.add(transition)
    #used to check whether duplicates has 
    
    #the ocpapn now contain all the required transitions
    
    arcslist=[]
    for ot in ocpn['object_types']:
        for a in ocpn['petri_nets'][ot][0].arcs:
            '''if a.source.label == "productstau1" or a.target.label == "productstau1":
                print(a.source.label,'-->',a.target.label)'''
            #
            #print('~',type(a.source),type(a.target))
            s = PNMatching(a.source,ocpapn,ot)
            t = PNMatching(a.target,ocpapn,ot)
            '''if s.name == "productstau1" or t.name == "productstau1":
                print(s.name,'-->',t.name)'''
            #print(type(t),type(s))
            #b = True
            if type(s) == objocpa.ObjectCentricPetriNet.Transition and s.label == None:
                n = s.name
                v = ocpn['double_arcs_on_activity'][ot][n]
                #b = False
            elif type(t) == objocpa.ObjectCentricPetriNet.Transition and t.label == None:
                n = t.name
                v = ocpn['double_arcs_on_activity'][ot][n]
                #b = False
            else:
                v = False
            #print(b,ot,n,ocpn['double_arcs_on_activity'][ot])
            arc = objocpa.ObjectCentricPetriNet.Arc(s,t,v)
            #print(not arc in ocpapn.arcs,arc.source.name,arc.target.name)
            #please don't directly check whether duplicate exist as follow!
            #print(arcslist)
            if not (s.name,t.name) in arcslist:
                ocpapn.arcs.add(arc)
            arcslist.append((s.name,t.name))
            
            
    #update the places and transitions
    for pl in ocpapn.places:
        inarcs = set()
        outarcs = set()
        #print(pl.name)
        for a in ocpapn.arcs:
            #print(a.source.name)
            if a.source.name == pl.name:
                #print('add inarcs')
                outarcs.add(a)
            if a.target.name == pl.name:
                #print('add outarcs')
                inarcs.add(a)
        p = Returncorrespondence(pl,ocpn['petri_nets'][pl.object_type][0],pl.object_type)
        #print(pl.name,ocpn['petri_nets'][pl.object_type][0])
        i,f = False,False
        #print('@@',type(p),ocpn['petri_nets'][pl.object_type][1][p])
        if ocpn['petri_nets'][pl.object_type][1][p]==1:
            i = True
        if ocpn['petri_nets'][pl.object_type][2][p]==1:
            f = True
        #print(type(pl),type(ocpapn.places))
        p = pl
        ocpapn.places.remove(p)
        pl = objocpa.ObjectCentricPetriNet.Place(pl.name,pl.object_type,outarcs,inarcs,i,f)
        p = pl
        ocpapn.places.add(p)
    for tr in ocpapn.transitions:
        inarcs = set()
        outarcs = set()
        for a in ocpapn.arcs:
            if a.source.name == tr.name:
                outarcs.add(a)
            if a.target.name == tr.name:
                inarcs.add(a)
        t = tr
        ocpapn.transitions.remove(t)
        tr = objocpa.ObjectCentricPetriNet.Transition(tr.name,tr.label,inarcs,outarcs,None,tr.silent)
        t = tr
        ocpapn.transitions.add(t)
    for arc in ocpapn.arcs:
        '''if arc.source.name == "productstau1" or arc.target.name == "productstau1":
            print('kalala')'''
        for pl in ocpapn.places:
            if pl.name == arc.source.name:
                s = pl
            if pl.name == arc.target.name:
                t = pl
        for tr in ocpapn.transitions:
            #print(tr.name,arc.source.name)
            if tr.name == arc.source.name:
                s = tr
            if tr.name == arc.target.name:
                t = tr
            #print(type(t),type(s),s.name,t.name,'--',arc.source.name,arc.target.name)
            #b = True
            #print(b,ot,n,ocpn['double_arcs_on_activity'][ot])
        '''if s.name == "productstau1" or t.name == "productstau1":
            print('hhhhh')'''
        a = arc
        ocpapn.arcs.remove(a)
        arc = objocpa.ObjectCentricPetriNet.Arc(s,t,arc.variable)
        a = arc
        ocpapn.arcs.add(a)
    return ocpapn

def Activityvariability(act,net):
    for arc in net.arcs:
        if (arc.source.name == act or arc.target.name == act) and arc.variable == True:
            return True
    return False

#the inputs in pm4py standard
def OC_Conformance(ocpn,ocel,method='token-based'):
    pndict, eldict, pnweight, elweight, fitdict, precdict = {}, {}, {}, {}, {}, {}
    pnfactor, elfactor = 0, 0
    for ot in ocpn['object_types']:
        pndict[ot] = ocpn['petri_nets'][ot]
        eldict[ot] = pm4py.ocel_flattening(ocel, ot)        
        #number of arcs
        pnfactor += len(pndict[ot][0].arcs)
        elfactor += len(eldict[ot])
    for ot in ocpn['object_types']:
        pnweight[ot] = len(pndict[ot][0].arcs)/pnfactor
        elweight[ot] = len(eldict[ot])/elfactor
    for ot in ocpn['object_types']:
        if method == 'token-based':
            fitdict[ot] = pm4py.fitness_token_based_replay(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])['log_fitness']
            precdict[ot] = pm4py.precision_token_based_replay(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])
        elif method == 'alignment':
            fitdict[ot] = pm4py.fitness_alignments(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])['log_fitness']
            precdict[ot] = pm4py.precision_alignments(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])
        else:
            raise ValueError('Only token-based and alignment methods are available')
    fitness = sum([fitdict[ot]*elweight[ot] for ot in ocpn['object_types']])
    precision = sum([precdict[ot]*pnweight[ot] for ot in ocpn['object_types']])
    return fitness, precision

def Drawcomparisontable(ocellist,ocpnlist,automodel=True):
    col = ['Ground truth','','Token-based replay','','Alignment','','Footprint-based method','']
    col2 = []
    for ele in range(4):
        col2.extend(['fitness','precision'])
    col = ['','']+col
    col2 = ['','']+col2

    if (not (len(ocellist) == len(ocpnlist))) and not automodel: 
        raise ValueError("OCEL list is not consistent to the OCPN list")
    row = []
    ELpm4py, ELocpa,PNocpa = {}, {},{}
    for ocel in ocellist:
        name = ocel.split('/')[-1]
        row.append(name)       
        ELocpa[name] = ocel_import_factory.apply(ocel)
        ELpm4py[name] = pm4py.read_ocel(ocel)
        if automodel:
            PNocpa[name] = ocpn_discovery_factory.apply(ELocpa[name], parameters={"debug": False})
            ocpnlist = [PNocpa[name] for name in row]
    PNpm4py = [PNtranslate_OCPA2PM4PY(pn) for pn in ocpnlist if type(pn)==objocpa.ObjectCentricPetriNet]
    value = []

    for i in range(len(row)):
        row1 = [row[i],'Origin']
        row2 = ['','Flower model']
        row3 = ['','Restricted model']
        
        flower = Flowermodel(PNpm4py[i])
        restrict = Restrictedmodel(PNpm4py[i],ELpm4py[row[i]])
        
        for j in range(4):
            if j == 0:
                fit,_ = quality_measure_factory.apply(ELocpa[row[i]], ocpnlist[i])
                _,prec = quality_measure_factory.apply(ELocpa[row[i]], ocpnlist[i])
                row1.extend([fit,prec])
                fit,_ = quality_measure_factory.apply(ELocpa[row[i]], flower)
                _,prec = quality_measure_factory.apply(ELocpa[row[i]], flower)
                row2.extend([fit,prec])
                fit,_ = quality_measure_factory.apply(ELocpa[row[i]], restrict)
                _,prec = quality_measure_factory.apply(ELocpa[row[i]], restrict)
                row3.extend([fit,prec])
                
            elif j == 1:
                fit,_ = OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'token-based',True)
                _,prec = OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'token-based',True)
                row1.extend([fit,prec])
                fit,_ = OC_Conformance(flower,ELpm4py[row[i]],'token-based',True)
                _,prec = OC_Conformance(flower,ELpm4py[row[i]],'token-based',True)
                row2.extend([fit,prec])
                fit,_ = OC_Conformance(restrict,ELpm4py[row[i]],'token-based',True)
                _,prec = OC_Conformance(restrict,ELpm4py[row[i]],'token-based',True)
                row3.extend([fit,prec])
            elif j == 2:
                try:
                    fit1,_ = OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'alignment',True)
                    _,prec1 = OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'alignment',True)
                    fit2,_ = OC_Conformance(flower,ELpm4py[row[i]],'alignment',True)
                    _,prec2 = OC_Conformance(flower,ELpm4py[row[i]],'alignment',True)
                    fit3,_ = OC_Conformance(restrict,ELpm4py[row[i]],'alignment',True)
                    _,prec3 = OC_Conformance(restrict,ELpm4py[row[i]],'alignment',True)
                    
                except:
                    fit1,fit2,fit3 = np.nan,np.nan,np.nan
                    prec1,prec2,prec3 = np.nan,np.nan,np.nan
                row1.extend([fit1,prec1])
                row2.extend([fit2,prec2])
                row3.extend([fit3,prec3])
            elif j == 3:
                for k in range(3):
                    if k == 0:
                        model = PNpm4py[i]
                        currow = row1
                    elif k == 1:
                        model = flower
                        currow = row2
                    elif k == 2:
                        model = restrict
                        currow = row3
                    ocpnlist = decomposeOCPN(model)
                    ocfmmodel = OCPN2OCFM(ocpnlist)
                    ocfmlog = OCEL2OCFM(ELpm4py[row[i]])
                    fit,_ = EvalOCFM(ocfmlog,ocfmmodel)
                    _,prec = EvalOCFM(ocfmlog,ocfmmodel)
                    currow.extend([fit,prec])
                    
        value.extend([row1,row2,row3])

    fig = plt.figure(figsize=(19,5))
    ax=fig.gca()
    ax.axis('off')
    #plt.figure(figsize=(20,8))
    #plt.table(cellText=[['']*4],colLabels=col,loc='bottom',bbox=[0,0.2,1,0.2])

    table = plt.table(cellText=[col]+[col2]+value,loc='center')
    #plt.table(cellText=[col],loc='top',bbox=[0,0.5,1,0.4])


    fig.canvas.draw()
    #merge the table below, the first will overwrite the second cell
    mergecells(table,[(0,0),(1,0)])
    mergecells(table,[(0,1),(1,1)])
    for i in range(4):
        mergecells1(table,(0,2+2*i),(0,3+2*i))
    for i in range(len(row)):
        mergecells(table,[(2+2*i,0),(2+2*i+1,0),(2+2*i+2,0)])
    #tab.scale(1,2)

def mergecells1(table, ix0, ix1):
    ix0,ix1 = np.asarray(ix0), np.asarray(ix1)
    d = ix1 - ix0
    if not (0 in d and 1 in np.abs(d)):
        raise ValueError("ix0 and ix1 should be the indices of adjacent cells. ix0: %s, ix1: %s" % (ix0, ix1))

    if d[0]==-1:
        edges = ('BRL', 'TRL')
    elif d[0]==1:
        edges = ('TRL', 'BRL')
    elif d[1]==-1:
        edges = ('BTR', 'BTL')
    else:
        edges = ('BTL', 'BTR')

    # hide the merged edges
    for ix,e in zip((ix0, ix1), edges):
        table[ix[0], ix[1]].visible_edges = e

    txts = [table[ix[0], ix[1]].get_text() for ix in (ix0, ix1)]
    tpos = [np.array(t.get_position()) for t in txts]

    # center the text of the 0th cell between the two merged cells
    trans = (tpos[1] - tpos[0])/2
    if trans[0] > 0 and txts[0].get_ha() == 'right':
        # reduce the transform distance in order to center the text
        trans[0] /= 2
    elif trans[0] < 0 and txts[0].get_ha() == 'right':
        # increase the transform distance...
        trans[0] *= 2

    #txts[0].set_transform(mpl.transforms.Affine2D().translate(*trans))

    # hide the text in the 1st cell
    txts[1].set_visible(False)

#cells is a list of tuple (coordinate of the top left corner), the first cell will overwrite the remaining cells.
def mergecells(table, cells):
    cells_array = [np.asarray(c) for c in cells]
    h = np.array([cells_array[i+1][0] - cells_array[i][0] for i in range(len(cells_array) - 1)])
    v = np.array([cells_array[i+1][1] - cells_array[i][1] for i in range(len(cells_array) - 1)])

    # if it's a horizontal merge, all values for `h` are 0
    if not np.any(h):
        # sort by horizontal coord
        cells = np.array(sorted(list(cells), key=lambda v: v[1]))
        edges = ['BTL'] + ['BT' for i in range(len(cells) - 2)] + ['BTR']
    elif not np.any(v):
        cells = np.array(sorted(list(cells), key=lambda h: h[0]))
        edges = ['TRL'] + ['RL' for i in range(len(cells) - 2)] + ['BRL']
    else:
        raise ValueError("Only horizontal and vertical merges allowed")

    for cell, e in zip(cells, edges):
        table[cell[0], cell[1]].visible_edges = e
        
    txts = [table[cell[0], cell[1]].get_text() for cell in cells]
    tpos = [np.array(t.get_position()) for t in txts]

    # transpose the text of the left cell
    trans = (tpos[-1] - tpos[0])/2
    # didn't had to check for ha because I only want ha='center'
    txts[0].set_transform(mpl.transforms.Affine2D().translate(*trans))
    for txt in txts[1:]:
        txt.set_visible(False)

if __name__ == "__main__":
    path1 = '/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCFM/OCEL/jsonocel/running-example.jsonocel'
    ocel1 = pm4py.read_ocel(path1)
    path2 = '/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCFM/OCEL/example.csv'

    parameter1 = {'time_name':'event_timestamp','act_name':'event_activity','object_type':['order','item','delivery']}
    ParsingCSV(path2,parameter1).to_csv('./ocelexample.csv')
    ocel2 = pm4py.read_ocel('./ocelexample.csv')

    ocpn1 = pm4py.discover_oc_petri_net(ocel1)
    ocpn2 = pm4py.discover_oc_petri_net(ocel2)
    flower1 = Flowermodel(ocpn1)
    restricted1 = Restrictedmodel(ocpn1,ocel1)
    flower2 = Flowermodel(ocpn2)
    restricted2 = Restrictedmodel(ocpn2,ocel2)
    #pm4py.view_ocpn(ocpn1, format="png")
    #pm4py.view_ocpn(flower1, format="png")

    result1 = Evaluation(ocel1,ocpn1)
    result2 = Evaluation(ocel2,ocpn2)
    result3 = Evaluation(ocel1,flower1)
    result4 = Evaluation(ocel2,flower2)
    result5 = Evaluation(ocel1,restricted1)
    result6 = Evaluation(ocel2,restricted2)

    #list1 = [(path1,result1), (path2,result2),(path1,result3),(path2,result4)]
    list2 = [(path1,result1), (path1,result3),(path1,result5)]
    list3 = [(path2,result2), (path2,result4),(path2,result6)]

    for ele in list2+list3:
        print('The quality dimensions of',ele[0][7:],'compared to its discovered model are: ','\nThe fitness is: ',ele[1][0],'\nThe precision is: ',ele[1][1],'\nThe simplicity is: ',ele[1][2])


  