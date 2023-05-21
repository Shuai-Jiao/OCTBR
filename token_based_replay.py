import pm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from multiset import *
from typing import List, Dict, Set

#ONLY accept pm4py format!
def OC_Conformance(ocpn,ocel,method='token-based',getprecision=False, weight = "average"):
    pndict, eldict, pnweight, elweight, fitdict, precdict = {}, {}, {}, {}, {}, {}
    pnfactor, elfactor = 0, 0
    for ot in ocpn['object_types']:
        pndict[ot] = ocpn['petri_nets'][ot]
        eldict[ot] = pm4py.ocel_flattening(ocel, ot)        
        #number of arcs
        pnfactor += len(pndict[ot][0].arcs)
        elfactor += len(eldict[ot])
            
    for ot in ocpn['object_types']:
        if weight == 'average':
            pnweight[ot] = 1/len(ocpn['object_types'])
            elweight[ot] = 1/len(ocpn['object_types'])
        elif weight == 'ratio':
            pnweight[ot] = len(pndict[ot][0].arcs)/pnfactor
            elweight[ot] = len(eldict[ot])/elfactor
        else:
            raise ValueError("Please use either 'average' or 'ratio' weighting")
    for ot in ocpn['object_types']:
        if method == 'token-based':
            fitdict[ot] = pm4py.fitness_token_based_replay(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])['log_fitness']
            if getprecision:
                precdict[ot] = pm4py.precision_token_based_replay(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])
        elif method == 'alignment':
            fitdict[ot] = pm4py.fitness_alignments(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])['log_fitness']
            if getprecision:
                precdict[ot] = pm4py.precision_alignments(eldict[ot], pndict[ot][0], pndict[ot][1], pndict[ot][2])
        else:
            raise ValueError('Only token-based and alignment methods are available')
    #print([(ot,fitdict[ot]) for ot in ocpn['object_types']])
    fitness = sum([fitdict[ot]*elweight[ot] for ot in ocpn['object_types']])
    if getprecision:
        precision = sum([precdict[ot]*pnweight[ot] for ot in ocpn['object_types']])
    if getprecision:
        return fitness, precision
    else:
        return fitness

#Based on OCPA    
def OCtokenbasedreplay(ocpn,ocel,handle_silence=True):
    #start with the initial
    if type(ocpn) is not objocpa.ObjectCentricPetriNet:
        raise ValueError("The ocpn format is not well-defined in ocpa")
    eventdict = ocel.obj.raw.events
    acttrans = []
    p,m,c,r = 0,0,0,0
    #the tokens(objects) in the corresponding place
    #Multiset stores the set of string of the object ID
    marking: Dict[objocpa.Place,Multiset]
    marking = {}
    for eventID in eventdict:
        event = eventdict[eventID]
        tr = ocpn.find_transition(event.act)
        #tr could be None! if there is no such transition in the petri net
        if tr is None:
            continue
        #Check whether for the current marking, any silence is actived
        #possiblemarking : Set[Dict[objocpa.Place,Multiset]]
        # A list of pair of the place which connected by the silence
        possibleplace = {}
        #The possible successor of the silence 
        #possiblemarking = set()

        #Find out all the possible marking executed after silence
        #Build up possible places
        for pl1 in marking.keys():
            
            if len(marking[pl1])>0:
                for pl2 in Findsilencesuccessor(pl1):
                    #Find out the possible object pair connected by the silence
                    for obj in marking[pl1]:
                        if Findobject(ocel,obj).type == pl2.object_type:
                            Initializemarking(possibleplace,pl2)
                            possibleplace[pl2].add(obj)
                            #possiblemarking.add(possibleplace)
            #print('Silence successor',pl1,Findsilencesuccessor(pl1))
                             
        #print('Possibleplace',possibleplace.keys())
        for obj in event.omap:
            #Consider precondition
            missing = True
            objecttype = Findobject(ocel,obj).type
            for arc in tr.in_arcs:
                #Check whether the marking is initialized
                Initializemarking(marking,arc.source)
                silencepredecessor = Findsilencepredecessor(obj,objecttype,arc.source,marking)
                #first determine whether the start place for the corr. type is
                if arc.source.initial and arc.source.object_type == objecttype:
                    missing = False
                    p += 1
                    c += 1
                #Initial places are not considered in the possible silence predecessors!!!\
                #So we have to discuss it seperately
                elif (not silencepredecessor is None) and silencepredecessor.initial:
                    p += 1
                    c += 1
                    missing = False
                #discuss the case the token exist for firing
                elif obj in marking[arc.source]:
                    #fire all possible token
                    #marking_copy = copy.deepcopy(marking[arc.source])
                    marking[arc.source].remove(obj)
                    missing = False
                    c += 1
                #Check whether any possible marking triggered by silence meet the condition
                elif arc.source in possibleplace.keys():
                    #print(marking[Findsilencepredecessor(obj,arc.source,marking)], obj,'---',Findsilencepredecessor(obj,arc.source,marking),arc.source.name)
                    #print(Findsilencepredecessor(obj,arc.source,marking))
                    #Consider the case that the predecessor is an initial place
                    if silencepredecessor.initial:
                        p += 1
                        c += 1
                        missing = False
                    elif obj in possibleplace[arc.source]:
                        marking[silencepredecessor].remove(obj)
                        #marking[arc.source].add(obj)
                        possibleplace[arc.source].remove(obj)
                        c += 1
                        missing = False

            if missing:
                m += 1
                c += 1
            #Consider effect
            for arc in tr.out_arcs:
                #use the obj's name to find the obj
                #instance = Findobject(ocel,obj)
                #It has to be set for the two if-statement
                
                if arc.target.object_type == objecttype:
                    Initializemarking(marking,arc.target)
                    marking[arc.target].add(obj)
                    p += 1
                #consider the end place
                if arc.target.final and arc.target.object_type == objecttype:
                    #print(arc.target.object_type,obj)
                    #Initializemarking(marking,arc.target)
                    if obj in marking[arc.target]:
                        marking[arc.target].remove(obj)
                    c += 1
    for k in marking.keys():
            r += len(marking[k])
            if len(marking[k]) >= 1:
                print(k, marking[k])
    print('pcmr:',p,c,m,r,p+m,c+r)
    return 1/2*(1-m/c)+1/2*(1-r/p)

#Find out the predecessing place that contains token and linked by silence
#ot is the object type of the object! not the object type of the place
def Findsilencepredecessor(obj,ot,place,marking):
    for ia1 in place.in_arcs:
        if ia1.source.silent:
            for ia2 in ia1.source.in_arcs:
                #The object should be in the predecessor! Because there could be\
                #multiple predecessors, we have to find the one contain the object!
                if ia2.source in marking.keys() and obj in marking[ia2.source]:
                    return ia2.source
                #Consider the case that the predecessor is initial marking. This is\
                #a special case because no objects are initialized at there!
                elif ia2.source.initial and ia2.source.object_type == ot:
                    return ia2.source
                #Find the first satisfiable predecessor to make the algo deterministic
                elif not Findsilencepredecessor(obj,ot,ia2.source,marking) is None:
                    return Findsilencepredecessor(obj,ot,ia2.source,marking)
                    
    
def Findsilencesuccessor(place):
    #pl = place
    #while any([oa.target.silent for oa in pl.out_arcs]):
    posssucc = []
    for oa1 in place.out_arcs:
        if oa1.target.silent:
            for oa2 in oa1.target.out_arcs:
                #pairofplace.append((pl1,oa2.target))
                posssucc.append(oa2.target)
                #print('oa2.target---',place.name,oa2.target,Findsilencesuccessor(oa2.target))
                posssucc = posssucc + Findsilencesuccessor(oa2.target)
    return posssucc


def findnextnotsilent(ocpn,silence):
    nextnonsilence = []
    for ele0 in silence.out_arcs:
        for ele1 in ele0.target.out_arcs:
            if ele1.target.silent == False:
                nextnonsilence.append(ele1.target)
    return nextnonsilence

def Findobject(ocel,obj:str):
    for o in ocel.obj.raw.objects:
        if ocel.obj.raw.objects[o].id == obj:
            return ocel.obj.raw.objects[o]
    raise ValueError("Object ID doesn't exist")
def Initializemarking(marking,key):
    if not key in marking.keys():
        #print(key)
        #we have to define it as a multiset! Because the same object could occur multiple times!!! 
        #Otherwise p+m != c+r
        marking[key] = Multiset()
