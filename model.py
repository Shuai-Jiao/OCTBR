import pm4py
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
import copy
from multiset import *

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

def Flowermodel(inputmodel):
    model = copy.deepcopy(inputmodel)
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

def Restrictedmodel(inputmodel,ocel):
    model = copy.deepcopy(inputmodel)
    for ot in model['object_types']:
        flat_log = pm4py.ocel_flattening(ocel, ot)
        onetracelog = flat_log.loc[flat_log['case:concept:name'] == flat_log['case:concept:name'][0]]
        event_log = pm4py.convert_to_event_log(onetracelog)
        net, im, fm = pm4py.discover_petri_net_inductive(event_log)
        model['petri_nets'][ot] = (net,im,fm)
    return model