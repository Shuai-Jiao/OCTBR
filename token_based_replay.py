import pm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from multiset import *
from typing import List, Dict, Set
import time

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
    start_time = time.time()
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
    initialplace = {}
    tokenmap = set()
    semiinitialplace = set()
    # To speed up the algo., first we first compute all the silence successors\
    # and the predecessors of each place, then we don't have to compute them\
    # all the time!
    successorcandidate = {}
    predecessorcandidate = {}
    #Build up the initial places of each ot
    for ot in ocpn.object_types:
        initialplace[ot] = set()
    for pl in ocpn.places:
        marking[pl] = Multiset()
        if pl.initial:
            initialplace[pl.object_type].add(pl)
        # we have to set the visited parameter to [] in each iteration explicitly!\
        # otherwise visited will be considered as an global variable!!!
        predecessorcandidate[pl] = find_silence_predecessor(pl,[])
        successorcandidate[pl] = Findsilencesuccessor(pl,[])
    print('silence search finished--------')
    #print('silence search finished------',predecessorcandidate,'\n----',successorcandidate)
    #print(initialplace)
    #One object could produce multiple tokens!!!
    #Find out the silence successors for the initial states in case of\
    #duplicate objects starts without initialized marking!
    for key in initialplace.keys():
        for initpl in initialplace[key]:
            #For set and list, again you forget A = A+B!!! A+B is wrong!
            semiinitialplace = semiinitialplace|set(Findsilencesuccessor(initpl))
            #print('!!',initpl,Findsilencesuccessor(initpl))
    #print('---',semiinitialplace)

    # counter is used for tracking the progress of OC TBR
    counter = 0
    replayedevents = 0
    totalevents = len(ocel.obj.raw.events)
    print('event dictionary',len(eventdict.keys()))
    for eventID in eventdict:
        counter += 1
        if counter%100 == 0:
            replayedevents += 100
            print('progress:',replayedevents,' from ',totalevents)
        event = eventdict[eventID]
        tr = ocpn.find_transition(event.act)
        #tr could be None! if there is no such transition in the petri net
        if tr is None:
            continue
        #Check whether for the current marking, any silence is actived
        #possiblemarking : Set[Dict[objocpa.Place,Multiset]]
        # A list of pair of the place which connected by the silence
        possibleplace = {}
        for pl in ocpn.places:
            possibleplace[pl] = Multiset()
        #The possible successor of the silence 
        #possiblemarking = set()

        # find out all the possible marking executed after silence
        # build up possible places
        #print(' start possible set---')
        for pl1 in marking.keys():
            silencesuccessor = successorcandidate[pl1]         
            if len(marking[pl1])>0 and len(silencesuccessor)>0:
                for pl2 in silencesuccessor:
                    #Find out the possible object pair connected by the silence
                    for obj in marking[pl1]:
                        if ocel.obj.raw.objects[obj].type == pl2.object_type:
                            #Initializemarking(possibleplace,pl2)
                            possibleplace[pl2].add(obj)
                            #possiblemarking.add(possibleplace)
            #print('Silence successor',pl1,Findsilencesuccessor(pl1))
        #print(' end possible set----')
                             
        #print('Possibleplace',possibleplace.keys())
        
        for obj in event.omap:
            #Consider precondition
            missing = True
            objecttype = ocel.obj.raw.objects[obj].type
            #If the object is the first time occur, then initialize token at start place\
            #Besides, we have to add on all possible silence successors
            if not obj in tokenmap:
                for pl1 in initialplace[objecttype]:
                    marking[pl1].add(obj)
                    for pl2 in successorcandidate[pl1]:
                        possibleplace[pl2].add(obj)
                        #print('~~~',pl2.name)
                tokenmap.add(obj)
                p += 1
            #print('----',tokenmap)
            for arc in tr.in_arcs:
                #Check whether the marking is initialized
                #Initializemarking(marking,arc.source)
                # find out the prerequired place from the predecessor candidates
                #print('predecessor candidate----',arc.source,predecessorcandidate[arc.source])
                for pl1 in predecessorcandidate[arc.source]:
                    if pl1 in marking.keys() and obj in marking[pl1]:
                        silencepredecessor = pl1
                #first determine whether the start place for the corr. type is
                '''if arc.source.initial and arc.source.object_type == objecttype:
                    missing = False
                    p += 1
                    c += 1'''
                #Initial places are not considered in the possible silence predecessors!!!\
                #So we have to discuss it seperately
                '''elif (not silencepredecessor is None) and silencepredecessor.initial:
                    p += 1
                    c += 1
                    missing = False'''
                #discuss the case the token exist for firing
                if obj in marking[arc.source]:
                    #fire all possible token
                    #marking_copy = copy.deepcopy(marking[arc.source])
                    marking[arc.source].remove(obj)
                    missing = False
                    c += 1
                #Check whether any possible marking triggered by silence meet the condition
                # possibleplace records all the possible reachable place from the current marking
                elif obj in possibleplace[arc.source]:
                    #print(marking[Findsilencepredecessor(obj,arc.source,marking)], obj,'---',Findsilencepredecessor(obj,arc.source,marking),arc.source.name)
                    #print(Findsilencepredecessor(obj,arc.source,marking))
                    #Consider the case that the predecessor is an initial place
                    marking[silencepredecessor].remove(obj)
                    #marking[arc.source].add(obj)
                    possibleplace[arc.source].remove(obj)
                    c += 1
                    missing = False
                #Consider we are now at the semi initial places, then initialize the missing token!
                elif arc.source in semiinitialplace:
                    p += 1
                    c += 1
                    missing = False

            if missing:
                m += 1
                c += 1
                #print('---',tr.name)
            #Consider effect
            for arc in tr.out_arcs:
                #use the obj's name to find the obj
                #instance = Findobject(ocel,obj)
                #It has to be set for the two if-statement
                
                if arc.target.object_type == objecttype:
                    #Initializemarking(marking,arc.target)
                    marking[arc.target].add(obj)
                    p += 1
                #consider the end place
                if arc.target.final and arc.target.object_type == objecttype:
                    #print(arc.target.object_type,obj)
                    #Initializemarking(marking,arc.target)
                    if obj in marking[arc.target]:
                        marking[arc.target].remove(obj)
                    c += 1
    # determine whether the remaining tokens can reach the end by silence
    for k in marking.keys():
            successorcandidates = Findsilencesuccessor(k,[])
            final = False
            for pl in successorcandidates:
                if pl.final:
                    final = True
                    break
            if final:
                continue
            else:
                r += len(marking[k])
                print('remaining places---',k, marking[k])

    print('pcmr:',p,c,m,r,p+m,c+r)
    if c == 0 or p == 0:
        raise ValueError('no consumed or produced tokens')
    end_time = time.time()
    print('Running time (s):',end_time-start_time)
    return 1/2*(1-m/c)+1/2*(1-r/p)

def find_silence_predecessor(place,visited=[]):
    silencepredecessor = []
    visited.append(place)
    for ia1 in place.in_arcs:
        if ia1.source.silent:           
            for ia2 in ia1.source.in_arcs:
                if ia2.source in visited:
                    #print('stop loop')
                    continue
                if place.object_type == ia2.source.object_type:
                    silencepredecessor.append(ia2.source)
                    #The object should be in the predecessor! Because there could be\
                    #multiple predecessors, we have to find the one contain the object!
                    silencepredecessor += find_silence_predecessor(ia2.source,visited)
                    #Consider the case that the predecessor is initial marking. This is\
                    #a special case because no objects are initialized at there!
                    #Find the first satisfiable predecessor to make the algo deterministic
                     
    return silencepredecessor
                
#Find out the predecessing place that contains token and linked by silence
#ot is the object type of the object! not the object type of the place
def Findsilencepredecessor(obj,ot,place,marking,visited=[]):
    visited.append(place)
    for ia1 in place.in_arcs:
        if ia1.source.silent:           
            for ia2 in ia1.source.in_arcs:
                if ia2.source in visited:
                    #print('stop loop')
                    continue
                #The object should be in the predecessor! Because there could be\
                #multiple predecessors, we have to find the one contain the object!
                silencepredecessor = Findsilencepredecessor(obj,ot,ia2.source,marking,visited)
                if ia2.source in marking.keys() and obj in marking[ia2.source]:
                    return ia2.source
                #Consider the case that the predecessor is initial marking. This is\
                #a special case because no objects are initialized at there!
                #Find the first satisfiable predecessor to make the algo deterministic
                elif not silencepredecessor is None:      
                    return silencepredecessor
                '''elif ia2.source.initial and ia2.source.object_type == ot:
                    return ia2.source'''
                    

def Findsilencesuccessor(place,visited=[]):
    # pl = place
    # while any([oa.target.silent for oa in pl.out_arcs]):
    posssucc = []
    # perhaps there is a silence loop, and the recursion won't be terminated
    visited.append(place)
    for oa1 in place.out_arcs:
        if oa1.target.silent:
            #print('a')
            for oa2 in oa1.target.out_arcs:
                # pairofplace.append((pl1,oa2.target))
                # if the place is visited, then ignore! all the recursed places\
                # will be added to the visited list.
                if oa2.target in visited:
                    #print('Loop to stop',place,oa2.target)
                    continue
                if place.object_type == oa2.target.object_type:
                    posssucc.append(oa2.target)
                    visited.append(oa2.target)
                    #print('oa2.target---',place.name,oa2.target,Findsilencesuccessor(oa2.target))
                    #This is used to consider the multiple consecutive silence!!!
                    #Confused $+$ and $extend$, speechless...
                    #print('b',oa2,oa2.target)
                    #print('b',oa2)
                    posssucc = posssucc + Findsilencesuccessor(oa2.target,visited)
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
