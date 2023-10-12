import pm4py
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
import copy
from multiset import *
from ocpa.objects.oc_petri_net.obj import ObjectCentricPetriNet
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.objects.log.ocel import OCEL
from ocpa.objects.log.variants.table import Table
from ocpa.objects.log.variants.graph import EventGraph
import ocpa.objects.log.converter.versions.csv_to_ocel as obj_converter
import ocpa.objects.log.variants.util.table as table_utils
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.visualization.oc_petri_net import factory as ocpn_vis_factory

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

# You have to define the dependencies between places, transitions, and arcs\
# otherwise, the algorithm could not work. 
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
    
    for ot in objecttype:
        im,fm = Marking(),Marking()
        net = PetriNet(ot)
        places[ot] = PetriNet.Place(ot)
        net.places.add(places[ot])
        im[places[ot]] = 1
        #No place are marked as final places in Niklas\
        #But if there is no final places, the token-based\
        #method will have too many remaining tokens at the end!!!
        #otherwise the fitness of the flower model will be 75% instead of 100%
        fm[places[ot]] = 1
        
        for trans in activitytype.keys():
            for ot2 in activitytype[trans]: 
                if ot2 == ot:
                    transitions[trans] = PetriNet.Transition(trans,trans)
                    net.transitions.add(transitions[trans])
                    #If we used pm4py method to add an arc, only arc will be created\
                    #but the dependencies with the corr. places and transitions are\
                    #still missing! e.g., pl.in_arcs = set() for all places!
                    petri_utils.add_arc_from_to(places[ot],transitions[trans],net)
                    petri_utils.add_arc_from_to(transitions[trans],places[ot],net)
        #Reconstruct the dependencies
    
        for pl in net.places:
            in_arcs = set()
            out_arcs = set()
            for arc in net.arcs:
                if arc.source == pl:
                    out_arcs.add(arc)
                if arc.target == pl:
                    in_arcs.add(arc)
            pl._Place__in_arcs = in_arcs
            pl._Place__out_arcs = out_arcs
        for tr in net.transitions:
            in_arcs = set()
            out_arcs = set()
            for arc in net.arcs:
                if arc.source == tr:
                    out_arcs.add(arc)
                if arc.target == tr:
                    in_arcs.add(arc)
            tr._Transition__in_arcs = in_arcs
            tr._Transition__out_arcs = out_arcs

        ocpn['petri_nets'][ot] = [net,im,fm]
    return ocpn

def DiscardedRestrictedmodel(ocel):
    print(type(ocel.process_execution_mappings[0]))
    return ocpn_discovery_factory.apply(ocel.process_execution_mappings[0], parameters={"debug": False})

#ocel in OCPA!
def Restrictedmodel(ocel):
    #find out the shortest length
    shortestvar = ocel.process_executions[0]
    for var in ocel.process_executions:
         if len(var) < len(shortestvar):
             shortestvar = var
    #filter the df according to the shortestvar
    filteredlog = ocel.log.log[ocel.log.log['event_id'].isin(list(shortestvar))]
    #convert to ocel format
    log = Table(filteredlog, parameters = ocel.parameters)
    obj = obj_converter.apply(filteredlog)
    graph = EventGraph(table_utils.eog_from_log(log))
    result = OCEL(log, obj, graph, ocel.parameters)
    #"debug" has to be false, otherwise the print will occur
    restrictedmodel = ocpn_discovery_factory.apply(result,parameters={"debug": False})
    ocpn_vis_factory.save(ocpn_vis_factory.apply(restrictedmodel), "./test/restrict.png")
    return restrictedmodel

def Discarded_Restrictedmodel(inputmodel,ocel):
    model = copy.deepcopy(inputmodel)
    for ot in model['object_types']:
        #flat_log is a type of pandas frame, we have to convert it to EL format
        flat_log = pm4py.ocel_flattening(ocel, ot)
        print('type(flat_log)',type(flat_log))
        #pm4py.get_variants(flat_log) returns wrong variants!!!\
        #which leads to error later!!!!
        variants = pm4py.get_variants(flat_log)
        #print('variants-------',variants)
        '''s = set()
        for case in pm4py.convert_to_event_log(flat_log):
            c = []
            for event in case:
                c.append(event["concept:name"])
            s.add(str(c))'''
        print('variants2-----',Lowestvariant(pm4py.convert_to_event_log(flat_log)))
        #print(Lowestvariant(variants))
        #onetracelog = pm4py.filter_variants(flat_log,[Lowestvariant(pm4py.convert_to_event_log(flat_log))])
        
        onetracelog = pm4py.filter_variants(flat_log,variants.keys())
        print('onetracelog',onetracelog)
        #onetracelog = pm4py.filter_variants_top_k(flat_log,len(variants))
        #print(variants)
        #onetracelog = flat_log.loc[flat_log['case:concept:name'] == flat_log['case:concept:name'][0]]
        #event_log = pm4py.convert_to_event_log(onetracelog)
        net, im, fm = pm4py.discover_petri_net_inductive(pm4py.convert_to_event_log(onetracelog))
        model['petri_nets'][ot] = (net,im,fm)
        pm4py.save_vis_petri_net(net,im,fm,"./test/restrict.png")
    return model

def Lowestvariant(log):
    frequency = dict()
    for case in log:
        var = '"'
        for event in case:
            var += event["concept:name"]+','
        if var[:-1]+'"' not in frequency:
            frequency[var[:-1]+'"'] = 1
        else:
            frequency[var[:-1]+'"'] += 1
    min = float('inf')
    for k in frequency.keys():
        if frequency[k] < min:
            min = frequency[k]
            lowestvariant = k
    #print('lowestvariant',lowestvariant)
    return lowestvariant

#Method done by Niklas
def create_flower_model(ocpn,ots):
    arcs = []
    transitions = []
    places = []
    [places.append(ObjectCentricPetriNet.Place(name=c+"1",object_type=c,initial=True)) for c in ots]
    #[places.append(ObjectCentricPetriNet.Place(name=c+"final",object_type=c,final=True)) for c in ots]
    for t in [x for x in ocpn.transitions if not x.silent]:
        t_new = ObjectCentricPetriNet.Transition(name=t.name)
        transitions.append(t_new)
        for ot in ots:
            if ot in [a.source.object_type for a in t.in_arcs]:
                var = any([a.variable for a in t.in_arcs if a.source.object_type == ot ])
                source_place = [p for p in places if p.initial and p.object_type == ot][0]
                in_a = ObjectCentricPetriNet.Arc(source_place, t_new, variable = var)
                out_a = ObjectCentricPetriNet.Arc(t_new, source_place, variable = var)
                arcs.append(in_a)
                arcs.append(out_a)
                t_new.in_arcs.add(in_a)
                t_new.out_arcs.add(out_a)
    flower_ocpn = ObjectCentricPetriNet(places = places, transitions = transitions, arcs = arcs)
    return flower_ocpn