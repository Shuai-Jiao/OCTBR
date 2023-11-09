import pm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from multiset import *
from typing import List, Dict, Set
import time
import networkx as nx
from itertools import groupby
import itertools
import copy
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
        elif weight == 'fraction':
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
                    marking[arc.source].remove(obj,multiplicity=1)
                    missing = False
                    c += 1
                #Check whether any possible marking triggered by silence meet the condition
                # possibleplace records all the possible reachable place from the current marking
                elif obj in possibleplace[arc.source]:
                    #print(marking[Findsilencepredecessor(obj,arc.source,marking)], obj,'---',Findsilencepredecessor(obj,arc.source,marking),arc.source.name)
                    #print(Findsilencepredecessor(obj,arc.source,marking))
                    #Consider the case that the predecessor is an initial place
                    marking[silencepredecessor].remove(obj,multiplicity=1)
                    #marking[arc.source].add(obj)
                    possibleplace[arc.source].remove(obj,multiplicity=1)
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
                        marking[arc.target].remove(obj,multiplicity=1)
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
                #print('remaining places---',k, marking[k])

    print('pcmr:',p,c,m,r,p+m,c+r)
    if c == 0 or p == 0:
        raise ValueError('no consumed or produced tokens')
    end_time = time.time()
    print('Running time (s):',end_time-start_time)
    return 1/2*(1-m/c)+1/2*(1-r/p)

def OCtokenbasedreplay2(ocel,ocpn,handle_silence="backward replay"):
    if type(ocpn) is not objocpa.ObjectCentricPetriNet:
        raise ValueError("The ocpn format is not well-defined in ocpa")
    eventdict = ocel.obj.raw.events
    acttrans = []
    p,m,c,r = 0,0,0,0
    #the tokens(objects) in the corresponding place
    #Multiset stores the set of string of the object ID
    marking: Dict[objocpa.Place,Multiset]
    marking = {}
    initial_place = {}
    #group the ocel into process executions
    process_execution = ocel.process_executions
    process_execution_object = ocel.process_execution_objects
    event_dict = ocel.obj.raw.events
    object_dict = ocel.obj.raw.objects
    place_dict = {}
    transition_dict = {}
    for pl in ocpn.places:
        place_dict[pl.name]=pl
    for tr in ocpn.transitions:
        transition_dict[tr.name]=tr

    dg = abstract_ocpn_to_DG(ocpn)
    print(f'the DG is {nx.to_dict_of_dicts(dg)}')
    #Build up the initial places of each ot
    for ot in ocpn.object_types:
        initial_place[ot] = set()
    for pl in ocpn.places:
        #print('line263',type(pl))
        marking[pl] = Multiset()
        if pl.initial:
            initial_place[pl.object_type].add(pl)
    r_places = set()
    #print('marking:',marking.keys(),'\n',initial_place)

    #extract all the started transition
    '''initialization = {}
    non_silent_transition = [tr for tr in ocpn.transitions if not tr.silent]
    for tr in non_silent_transition:
        for arc in tr.in_arcs:
            if arc.source.initial:
                if tr in initialization.keys():
                    initialization[tr].add(arc.source)
                else:
                    initialization[tr] = set()
                    initialization[tr].add(arc.source)'''
        
    for i,unsorted_process in enumerate(process_execution):
        print(f'Progress: process id {i} from {len(process_execution)}')
        process = sort_process_execution(unsorted_process,event_dict)
        #print(f'the process execution is {[event.act for event in process]}')

        #check whether the previous marking is clean
        if sum([len(marking[pl]) for pl in ocpn.places]):
            print(f'the uncleared marking is {marking}')
            raise ValueError('the marking is not clean')
        
        #initialize the start place with the involving objects
        # it is not guaranteed that the object only occurred once!!!        
        for obj in process_execution_object[i]:
            if len(initial_place[obj[0]]) > 1:
                raise ValueError('the start place is not unique!')
            for start_place in initial_place[obj[0]]:
                #print('type',type(obj[1]))
                marking[start_place].add(obj)
                #marking[start_place].add('3')                
                p += 1
        #token_set = Multiset()
        
        #start replay all the events in a process 
        for event in process:
            #act = event.act
            obj_list = [(object_dict[event_id].type,event_id) for event_id in event.omap]
            #print(f'objlist {obj_list}')
            '''for tr in ocpn.transitions:
                if tr.name == act:
                    curr_tr = tr'''  
            #BE AWARE! Considering the case that the activity not in the model!!!!
            if event.act in transition_dict.keys():
                curr_tr = transition_dict[event.act]
            else:
                continue

            '''if curr_tr in initialization.keys():
                for start_place in initialization[curr_tr]:
                    initializing_object = Multiset([obj for obj in obj_list if obj[0]==start_place.object_type])
                    marking[start_place] = marking[start_place] + initializing_object
                            
                    token_set = token_set + initializing_object
                    p += len(initializing_object)'''
            #print(f'~~~~~the current transition name is :{curr_tr.name}')
            

            
            #debugi = 0         
            for obj in obj_list:
                #debugi += 1
                #print(f'Progress: object {debugi} from {len(obj_list)}')
                #is_missing, support_place = backward_replay()
                #I guess the marking are already modified in this method
                preset = [arc.source for arc in curr_tr.in_arcs if arc.source.object_type == obj[0]]
                postset = [arc.target for arc in curr_tr.out_arcs if arc.target.object_type == obj[0]]

                if handle_silence == 'backward_replay':                
                    p0,c0,m0,_ = backward_replay3(curr_tr,marking,obj)
                    #not necessary only miss one token
                    '''if obj not in marking[arc.source] and is_missing:
                        m += 1
                        c += 1
                    elif obj not in marking[arc.source] and not is_missing:
                        marking[support_place].remove(obj)
                        c += 1
                    else:
                        c += 1'''
                    #print(f'missing place {missing_place}')                                       
                    #print(f'missing_place: {missing_place}, pcm:{[p,c,m]}')                    
                elif handle_silence == 'shortest_path':
                    dg_copy = copy.deepcopy(dg)        
                    parameter = {'preset':preset,'transition_dict':transition_dict,'place_dict':place_dict}
                    p0,c0,m0,_ = shortest_path_backward_replay(ocpn,dg_copy,marking,obj,parameter)
                    #enumerate all the possible combination
                    

                p += p0
                c += c0
                m += m0

                #execute the current transition    
                for pl in preset:
                    #print(pl.name,obj,marking[pl])
                    #the problem is that the marking[arc,source] is empty
                    #only remove the object, which the same object type
                    marking[pl].remove(obj,multiplicity=1)
                for pl in postset:
                    marking[pl].add(obj)
                c += len(preset)
                p += len(postset)
                #print(f'transition {curr_tr} is executed successfully')
            '''for arc in curr_tr.out_arcs:
                for obj in obj_list:
                    if arc.target.object_type == obj.type:
                        marking[arc.target].add(obj)
                        p += 1'''
        
            '''for obj in marking[pl]:
                marking[pl].remove(obj)
                c += 1'''
        #at the end, check whether remaining
        final_places = [pl for pl in ocpn.places if pl.final]
        remaining_places = [pl for pl in ocpn.places-set(final_places) if len(marking[pl])>0] 
        remaining_objects = set().union(*[marking[pl] for pl in remaining_places])
        #print(f'the middle pmcr is: {p,c,m,r,p+m,c+r}')

        for obj in remaining_objects:
        #for obj in list(token_set):
            obj_final_places = [pl for pl in ocpn.places if pl.final and pl.object_type==obj[0]]
            if handle_silence == 'backward_replay':           
                                
                    #final = [f for f in final_places if f.object_type==obj[0]]
                    if len(obj_final_places)==1:
                        p1,c1,m1,_ = backward_replay3(*obj_final_places,marking,obj)
                        #r1 = len([pl for pl in ocpn.places-final_places if obj in marking[pl]])
                    else:
                        return ValueError('the final place is not unique for a certain object type!')
                    
                

                #remain_number = sum([len(marking[pl]) for pl in ocpn.places])
                #print(f'the number of remaining objects is: {remain_number}')

            elif handle_silence == 'shortest_path':
                    #print('delete this message')
                    dg_copy = copy.deepcopy(dg)
                    #path = find_shortest_executable_path(ocpn,marking,dg_copy,pair[0],pair[1],obj)
                    
                    parameter = {'preset':obj_final_places,'transition_dict':transition_dict,'place_dict':place_dict}
                    p1,c1,m1,_ = shortest_path_backward_replay(ocpn,dg_copy,marking,obj,parameter)
            p += p1
            c += c1
            if m1>0:
                raise ValueError('the end place missing is not 0!')
            #m += m0
        #r += sum([len(marking[pl]) for pl in ocpn.places-set(final_places)])

        for pl in ocpn.places-set(final_places):
            r += len(marking[pl])
            marking[pl] = Multiset()
        '''for pl in ocpn.places-set(final_places):
            if len(marking[pl])>0:
                r_places.add(pl.name)'''
        #clear all the final places            
        for pl in final_places:
            c += len(marking[pl])
            marking[pl] = Multiset()
    #print(f'the remaining places: {remaining_places}')                
    print('pcmr:',p,c,m,r,p+m,c+r)
    if c == 0 or p == 0:
        raise ValueError('no consumed or produced tokens')
    result = {'fitness':1/2*(1-m/c)+1/2*(1-r/p),'p':p,'c':c,'m':m,'r':r}
    return result

def shortest_path_backward_replay(ocpn,dg,marking,obj,parameter):
    #the preset already considered the object type
    preset = parameter['preset']
    transition_dict = parameter['transition_dict']
    place_dict = parameter['place_dict']
    #all the place miss one token
    gamma_list = [pl.name for pl in preset if not obj in marking[pl] and pl.object_type==obj[0]]
    #all the place contain one token that not needed
    lambda_list = [pl.name for pl in ocpn.places-set(preset) if obj in marking[pl]]
    search_pairs = [(x,y) for x in lambda_list for y in gamma_list]
    interrupt = True if len(gamma_list)==0 or len(lambda_list)==0 else False
    p,c,m,silent_sequence = 0,0,0,None
    marking_copied0={}
    for key,value in marking.items():
        marking_copied0[key] = value
    while not interrupt:               
        shortest_paths_list = []
        #dg should be deep copied!!!

        
        #print(f'line411 whether the marking changed: {marking==marking_copied0}')
        #item1 =  place_dict['item1']
        #order7 = place_dict['order7']
        #print(f'line413 marking item1: {marking[item1]}; marking order7: {marking[order7]}')
        #print(f'the search pair: {search_pairs}')
        for pair in search_pairs:
            dg_copy = copy.deepcopy(dg)
            #collect all the shortest path and find the shortest one
            #parameter2 = {'transition_dict':transition_dict}
           
            path = find_shortest_executable_path(marking,dg_copy,pair[0],pair[1],obj,parameter)
            if not path is None:
                shortest_paths_list.append(path)
            else:
                #else means that the DG doesn't contain the start node or the end node\
                #which means that the start or the end doesn't have silence
                interrupt = True

        if len(shortest_paths_list) == 0:
            break
            print('no executable path in all of the possible combinations')
        
        #print(f'line429 whether the marking changed: {marking==marking_copied0}')
        #print(f'line429 marking item1: {marking[item1]}; marking order7: {marking[order7]}')
        #print(f'line429 marking_copied0 item1: {marking_copied0[item1]}; marking order7: {marking_copied0[order7]}')    
        sorted_shortest_paths_list = sorted(shortest_paths_list,key=lambda path:len(path))
        shortest_path = sorted_shortest_paths_list[0]
        #print(f'the shortest path is {shortest_path}')
        silent_sequence = []
        for i in range(len(shortest_path)-1):
            #endnode1 = dg.nodes[shortest_path[i]]
            #endnode2 = dg.nodes[shortest_path[i+1]]
            #print(f'the endnodes are {shortest_path[i],shortest_path[i+1]} and the type is {type(shortest_path[i+1])}')
            tr_name = dg.get_edge_data(shortest_path[i],shortest_path[i+1]).get('label')
            silent_sequence.append(transition_dict[tr_name])
        #print(f'the silent_sequence is {silent_sequence}')
        #print(f'whether the marking changed: {marking==marking_copied0}')
        #print(f'line447 marking item1: {marking[item1]}; marking order7: {marking[order7]}')
        print(f'the SP silent sequence is {silent_sequence}')
        p,c = execute_silent_sequence(silent_sequence,marking,obj)
        gamma_list = [pl.name for pl in preset if not obj in marking[pl] and pl.object_type==obj[0]]
        #all the place contain one token that not needed
        lambda_list = [pl.name for pl in ocpn.places-set(preset) if obj in marking[pl]]
        search_pairs = [(x,y) for x in lambda_list for y in gamma_list]

        if len(gamma_list) == 0 or len(lambda_list) == 0:
            interrupt = True
    
    is_final = len(preset) == 1 and preset[0].final
    for pl in preset:
        if not obj in marking[pl] and not is_final:
            m += 1
            marking[pl].add(obj)
    
    return p,c,m,silent_sequence

def which_missing(transition,object,marking):
    missing_places = []
    for tr in transition.in_arcs:
        if object not in marking[tr.source]:
            missing_places.append(tr.source)
    return missing_places

#
def forward_replay(remaining_places,forward_cashing,r,marking,object):
    if len(remaining_places) == 0:
        return r,marking
    new_postset = []
    for pl1 in remaining_places:
        focus_list = forward_cashing[pl1]
        for pl2 in focus_list:
            if pl2.final:
                c += 1
                marking[pl2].remove


#handling the marking update and compute the missing value
#determine the executed silence, and update the marking according to it!
def backward_replay(marking,missing_places,object,sequence,visited):
    '''if len(missing_places) == 0:
        return m,marking'''
    #missing_places = which_missing(transition,object,marking)
    next_missing_places = []
    for pl1 in missing_places:
        #missing_places.remove(pl1)
        #find out the backward transition
        backward_transition = []
        for arc in pl1.in_arcs:
            if arc.source.silent:
                backward_transition.append(arc.source)
        if len(backward_transition) == 0:
            sequence.insert(0,'block')
            return sequence
        else:
            sequence.insert(0,'choice')

        for tr in backward_transition:
            for arc in tr.in_arcs:
                if object in marking[arc.source]:
                    sequence.insert(0,tr)
                else:
                    next_missing_places.add(arc.source)
            return backward_replay(marking,next_missing_places,object,sequence)



        '''focus_list = backward_replay_cashing[pl1]
        #if there is no silent preset for a place, then it can be filled
        #here we don't update the marking, just consider it has been consumed
        if len(focus_list) == 0:
            m += 1
            c += 1
            continue
        for pl2 in focus_list:
            if object in marking[pl2]:
                marking[pl2].remove(object)
                c += 1
                continue
            else:
                next_missing_places.append(pl2)
    return backward_replay(marking,next_missing_places,object,backward_replay_cashing,m)
     '''
            


#you didn't consider the case that one place can have mulitple connected silence!
def cashing(ocpn):
    # To speed up the algo., first we first compute all the silence successors\
    # and the predecessors of each place, then we don't have to compute them\
    # all the time!
    place_successor = {}
    place_predecessor = {}
    place_in_silence = {}
    place_out_silence = {}
    for pl in ocpn.places:
        place_in_silence[pl] = [arc.target for arc in pl.out_arcs if arc.target.silent]
        place_out_silence[pl] = [arc.source for arc in pl.in_arcs if arc.source.silent]

    #Build up the initial places of each ot
    for tr in ocpn.transitions:
        if tr.silent:
            preset = [arc.source for arc in tr.in_arcs]
            postset = [arc.target for arc in tr.out_arcs]
            for arc in tr.in_arcs:
                place_successor[(arc.source,tr)] = postset
            for arc in tr.out_arcs:
                place_predecessor[(arc.target,tr)] = preset
    return place_predecessor, place_successor, place_in_silence, place_out_silence


def find_silence_predecessor(place,visited=[]):
    silencepredecessor = []
    visited.append(place)
    for ia1 in place.in_arcs:
        if ia1.source.silent:           
            for ia2 in ia1.source.in_arcs:
                if ia2.source in visited:
                    #print('stop loop')
                    continue
                # the object type should be consistent!
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


def abstract_ocpn_to_DG(ocpn):
    DG = nx.DiGraph()
    node = set()
    silent_transition = [tr for tr in ocpn.transitions if tr.silent]
    for tr in silent_transition:       
        endpoint_start = [arc.source for arc in tr.in_arcs]
        endpoint_end = [arc.target for arc in tr.out_arcs]
        #group the nodes with the same object type
        grouped_start = {key: list(group) for key, group in itertools.groupby(endpoint_start, key=lambda obj: obj.object_type)}
        grouped_end = {key: list(group) for key, group in itertools.groupby(endpoint_end, key=lambda obj: obj.object_type)}
        for key1,value1 in grouped_start.items():
            for key2,value2 in grouped_end.items():
                if key2 == key1:
                    node_start = [ele.name for ele in value1]
                    node_end = [ele.name for ele in value2]
                    edges=list(itertools.product(node_start,node_end))
                    for ed in edges:
                        if ed[0] not in node:
                            node.add(ed[0])
                            DG.add_node(ed[0])
                        if ed[1] not in node:
                            node.add(ed[1])
                            DG.add_node(ed[1])
                        DG.add_edge(ed[0],ed[1],label=tr.name)

    return DG

def find_shortest_path(DG,start,end):
    if start not in list(DG.nodes) or end not in list(DG.nodes):
        '''print(f'the start or the end node is not defined; the start: {start}\
              ,the end: {end}, and the DG.nodes: {list(DG.nodes)}')'''
        return None
    #print(f'line666 the DG is {nx.to_dict_of_dicts(DG)}')
    try:
        #nx.astar_path(DG,start,end) can only return an existing path! no None return.
        return nx.astar_path(DG,start,end)
    except:
        #print(f'no path between {start} and {end}')
        return None

#consider the object type!
#You just verify without execution???
def verify(dg,marking,path,obj,parameter):
    #since marking_copy = copy.deepcopy(marking) cannot be used because of PLACE no copy defined!
    marking_copy = {}
    for key,value in marking.items():
        marking_copy[key]=copy.deepcopy(value)
    
    transition_dict = parameter['transition_dict']
    place_dict = parameter['place_dict']
    enable = True
    unenable_edge = None
    for i in range(len(path[:-1])):
        for u, v, data in dg.edges(data=True):
            if u == path[i] and v == path[i+1]:
                tr_name = data.get("label")
                break
        curr_tr = transition_dict[tr_name]
        preset = [arc.source for arc in curr_tr.in_arcs if arc.source.object_type==obj[0]]
        postset = [arc.target for arc in curr_tr.out_arcs if arc.target.object_type==obj[0]]
        if any([obj not in marking_copy[pl] for pl in preset]):
            #print(f'line718 obj is {obj}, marking is {[marking_copy[arc.source] for arc in curr_tr.in_arcs if arc.source.object_type==obj[0]]}')  
            '''print(f'line718 the unverified path {path}, the unverified tr: {curr_tr.name}\
                  the marking of the unverified place {marking[place_dict[path[i]]]}')'''         
            enable = False
            unenable_edge = (path[i],path[i+1])
            return enable, unenable_edge
        else:
            for pl in preset:
                marking_copy[pl].remove(obj,multiplicity=1)
            for pl in postset:
                marking_copy[pl].add(obj)
    #print(f'the verified path is {path} with object {obj}')
    return enable, unenable_edge

#Be aware of deepcopy DG
def find_shortest_executable_path(marking,dg,start,end,obj,parameter):
    place_dict = parameter['place_dict']
    path = find_shortest_path(dg,start,end)
    if path == None:
        return None
    verification, delete_edge = verify(dg,marking,path,obj,parameter)
    
    if verification:
        return path
    else:
        #print(f'the unverified path is {path}')
        '''print(f'the verification: {verification}; obj is {obj}; deleted: {delete_edge}\
          the marking of deleted point: {marking[place_dict[delete_edge[0]]]}')'''
        #raise ValueError('a path cannot be verified')
        dg.remove_edge(*delete_edge)
        return find_shortest_executable_path(marking,dg,start,end,obj,parameter)

# define a higher level data structure
class BackwardGraph(object):
    def __init__(self):
        self.nodes = set()
        self.operators = set()
        self.root = None
        #self.endnodes = set()
    class Node(object):
        def __init__(self,state,transition=None,label=None, end=False):
            self.state = state
            self.transition = transition
            self.label = transition.name if not transition is None else label
            #in is a set, out is unique
            self.inn = set()
            self.out = None
            self.color = 'yellow'
            self.path = []
            self.end = end
    class Operator(object):
        def __init__(self,type,transition=None,label=None):
            self.type = type
            self.inn = set()
            #the label None is just used for attribtue consistency when handling
            self.transition = transition
            self.label = transition.name if not transition is None else label
            self.out = None
            self.path = []
            self.color = 'yellow'
    #above is children, inn is children
    def connect_components(self,above,below):
        above.out = below
        below.inn.add(above)
        above.end = True
        below.end = False
        #print(f'line673 above.label is {above.label}, above.path is {above.path}, above.type: {type(above)}\n \
              #below.label is {below.label}, below.path is {below.path}, below type: {type(below)}')
        #above.path = below.path + [above.label]
        #print('type of above.path',[type(ele) for ele in below.path])
        #deepcopy cannot copy None, and insert() returns None
        above.path = copy.deepcopy(below.path)
        if type(above) == BackwardGraph.Node:
            #print('hi=======')
            # insert() doesn't return value?????
            #above.path = below_path_copy.insert(0,above.label)
            #print(f'above label: {above.label}')
            above.path.insert(0,above.label)
        #print(f'After, below path:{below.path}, above path"{above.path}')

    @property
    def extension_nodes(self):
        return [n for n in self.nodes if n.end and n.color=='yellow']
    
    @property
    def all_green(self):
        return all([o.color=='green' for o in self.operators])
    @property
    def any_red(self):
        return any([o.color=='red' for o in self.operators])
    
    def get_color(self):
        node_color = [(n.label,n.color) for n in self.nodes]
        operator_color = [(o.label,o.color) for o in self.operators]
        return node_color+['before node, after operator']+operator_color

    def color_update(self):        
        no_update = False
        while not no_update:
            #print(f'the color is {self.get_color()}, root color: {self.root.color}')
            no_update = True
            #node_color = [n.color for n in self.nodes]
            #operator_color = [o.color for o in self.operators]
            '''if self.root.label == 'residual end':
                print(f'residual end, color is {self.get_color()}')'''
            for o in self.operators:
                #if not yellow, we are not allowed to change no_update!
                if o.type == 'AND' and o.color == 'yellow':
                    if all([n.color == 'green' for n in o.inn]):
                        #o.out.color = 'green'
                        o.color = 'green'
                        no_update = False
                    elif any([n.color == 'red' for n in o.inn]):
                        #o.out.color = 'red'
                        o.color = 'red'
                        no_update = False
                        for pre in o.inn:
                            if pre.color == 'yellow':
                                #grey refers no consideration necessary
                                pre.color = 'grey'
                elif o.type == 'OR' and o.color == 'yellow':
                    if all([n.color == 'red' for n in o.inn]):
                        #o.out.color = 'red'
                        o.color = 'red'
                        no_update = False
                    elif any([n.color == 'green' for n in o.inn]):
                        #o.out.color = 'green'
                        o.color = 'green'
                        no_update = False
                        for pre in o.inn:
                            if pre.color == 'yellow':
                                #grey refers no consideration necessary
                                pre.color = 'grey'
            #the node color should also be updated
            for n in self.nodes:
                if len(n.inn) > 1:
                    return ValueError('the node has multiple children operators!')
                
                # The node has no children! which means it has to be marked as red 
                # Node has only one child!!!
                '''if len(n.inn) == 0 and n.color=='yellow':
                    n.color = 'yellow'
                    n.end = True
                    no_update = False'''
                #only focus on the yellow nodes, otherwise could not terminate
                # the end yellow node should not be colored here! because the construction is not done!
                if len(n.inn) == 1 and n.color == 'yellow':
                    place = list(n.inn)[0]
                    if place.color == 'green' and not place.end:
                        n.color = 'green'
                        no_update = False
                    elif place.color == 'red' and not place.end:
                        n.color = 'red'
                        no_update = False

    #the function won't extract the root label
    #this function extract all the possible silent sequence for the preset of the current transition
    def extract_silent_sequence(self):       
        '''if self.root.color == 'green':
            return self.get_path_above(self.root)
            #print('the given transition is not activated yet!')
            #return None
        else:'''
        #the root label is not a silent transition!
        #But maybe there is still silent sequence that can reduce the missing tokens
        silent_sequence = []
        for n in self.root.inn:
            if n.color == 'green':
                #print(f'there is green')
                silent_sequence = self.get_path_above(n) + silent_sequence
        return silent_sequence
                           

    def get_BST_label(self):
        return [(n.label,n.end,n.color) for n in self.nodes] + \
            ['before node, after operator'] + [(o.label,o.type,o.color) for o in self.operators]
    

    def get_path_above(self,ele):
        if type(ele) == self.Node:           
            if ele.end and ele.color == 'green':
                #print(f'{ele.label,type(ele)} is green end!')
                return [ele.transition]
            elif ele.color == 'green':
                #print(f'I have green but not end {ele.label}')
                if len(ele.inn) > 1:
                    return ValueError('node has multiple child!!!')
                return self.get_path_above(list(ele.inn)[0])+[ele.transition]
        elif type(ele) == self.Operator:
            if ele.type == 'AND' and ele.color == 'green':
                #print('the AND is green')
                and_join_path = [ele.transition]
                #count819 = 0
                for ele2 in ele.inn:
                    #count819 += 1 
                    #execute AND label at last
                    #print(f'and_join_path {ele2.label} (before): {and_join_path}')
                    and_join_path = self.get_path_above(ele2)+ and_join_path
                    #print(f'and_join_path {ele2.label} (after): {and_join_path}')
                return and_join_path
            if ele.type == 'OR' and ele.color == 'green':    
                #print('the OR is green')                
                for ele2 in ele.inn:
                    if ele2.color == 'green':
                        or_path = self.get_path_above(ele2)
                        break
                return or_path
    
    def get_missing_node(self):
        missing_place = []
        for n in self.root.inn:
            if not n.color == 'green':
                missing_place.append(n.state)
        return missing_place
    
    def is_place_occupied(self,pl):
        for n in self.nodes:
            if n.state == pl and n.end and n.color == 'green':
                return True
        return False
    
    def is_silence_visited(self,tr,node):
        #whether the node is visited along the path to the root
        visited_list= []
        while not node.out==self.root:
            if not tr in visited_list:
                visited_list.append(node.label)
                node = node.out
            else:
                return True
        return False
        


#please consider the object type, thank you
def execute_silent_sequence(silent_sequence,marking,obj):
    #print(f'the executed silent sequence is: {[tr.name for tr in silent_sequence]}')
    marking_copied = {}
    for key,value in marking.items():
        marking_copied[key]=value

    p,c = 0,0
    #we added None to avoid duplication for node label
    silent_sequence = [ele for ele in silent_sequence if not ele == None]   
    for silence in silent_sequence:
        preset = [arc.source for arc in silence.in_arcs if obj[0]==arc.source.object_type]
        postset = [arc.target for arc in silence.out_arcs if obj[0]==arc.target.object_type]
        if all([obj in marking[pl] for pl in preset]):
            c += len(preset)
            for pl in preset:
                marking[pl].remove(obj,multiplicity=1)
            for pl in postset:
                marking[pl].add(obj)
            p += len(postset)           
        else:
            
            #print(f'line956 is the marking get changed: {marking==marking_copied}')
            raise ValueError(f'~~~~~~~~~~a silent transition cannot be executed: {silence.name,silence.label}\
                  the silence sequence is: {[tr.name for tr in silent_sequence]}\
                    the preset is: {preset}, the object is {obj}\
                        the marking of the preset is {[marking[pl] for pl in preset]}')
            return None
    return p,c

'''def build_forward_graph(abstract,node):
    place = node.state
    silent_transition = [arc.target for arc in place.out_arcs if arc.target.silent]
    if len(silent_transition) == 0:
        node.color = 'red'
    else:
        for tr in silent_transition:
            in_silence = [arc.source for arc in tr.in_arcs]
            if len(in_silence) == 1:
'''

# AND then OR missing
def build_backward_graph(abstract,node):
    #abstract = BackwardGraph()
    #node = BackwardGraph.Node(place=place,path=path)
    #abstract.nodes.add(node)
    #the current place
    place = node.state
    object_type = place.object_type
    silence_list = [arc.source for arc in place.in_arcs if arc.source.silent]

    if len(silence_list) == 0:
        node.color = 'red'
    elif len(silence_list) > 1:
        operator1 = BackwardGraph.Operator('OR')
        is_OR = True
    else:
        operator1 = BackwardGraph.Operator(type='AND',transition=silence_list[0])
        is_OR = False

    if len(silence_list) != 0:
        #print('line835', operator1.path,node.path,node.root,node.label)
        abstract.connect_components(operator1,node)
        # I think the post modification will also change the previous added element?
        abstract.operators.add(operator1)

        for silence in silence_list:           
            #silence = arc1.source
            if silence in operator1.path:
                #For AND postsets the label is only stored in AND!!!
                if is_OR:
                    transition = silence
                else:
                    transition = None
                # to avoid building a loop! mark the loop node to red end!
                state = BackwardGraph.Node(state=pl,transition=transition,end=True,color='red')
                abstract.connect_components(state,operator1)
                abstract.nodes.add(state)
            # arc1.source is the silent transition
            # determine operator again
            else:
                preset = [arc for arc in silence.in_arcs if arc.source.object_type == object_type]
                if len(preset) > 1:
                    if is_OR:
                        operator2 = BackwardGraph.Operator('AND',transition=silence)
                        abstract.connect_components(operator2,operator1)
                        abstract.operators.add(operator2)
                        parent_operator = operator2
                    else:
                        parent_operator = operator1
                    for arc2 in preset:
                        #for the preset of AND, the silence transition is stored in AND operator
                        state = BackwardGraph.Node(state=arc2.source,transition=None,end=True)
                        abstract.connect_components(state,parent_operator)
                        abstract.nodes.add(state)
                elif len(preset) == 0:
                    return ValueError('the silence has no preset of an object type')
                else:
                    #there is only one in arc in this case    
                    pl = list(silence.in_arcs)[0].source
                    if is_OR:
                        transition = silence
                    else:
                        transition = None
                    state = BackwardGraph.Node(state=pl,transition=transition,end=True)
                    abstract.connect_components(state,operator1)
                    abstract.nodes.add(state)
        
        #above need to be added to the set of the model
        #below try to determine the color and see whether backtrack in backward replay

def backward_replay3(element,marking,object):
    abstract = BackwardGraph()
    #abstract.root = BackwardGraph.Operator(type='AND')
    if type(element)==objocpa.ObjectCentricPetriNet.Place:
        #element be the place only in final place
        final_place = element
        #the root here is a residual element outwards the final place
        abstract.root = BackwardGraph.Operator(type='AND',label='residual end')
        node = BackwardGraph.Node(state=final_place,transition=None,end=True)
        abstract.connect_components(node,abstract.root)
        abstract.operators.add(abstract.root)
        abstract.nodes.add(node)
    elif type(element)==objocpa.ObjectCentricPetriNet.Transition:
        transition = element
        abstract.root = BackwardGraph.Operator(type='AND',transition=transition)
        abstract.operators.add(abstract.root)
        preset = [arc.source for arc in transition.in_arcs if arc.source.object_type==object[0]]        
        for pl in preset:
            node = BackwardGraph.Node(state=pl,transition=None,end=True)
            abstract.nodes.add(node)
            abstract.connect_components(node,abstract.root)
            #backward_search3(abstract,place,node)
    # determine whether all green or all yellow for the termination

    while abstract.root.color == 'yellow':
        node_color = [(n.label,n.color) for n in abstract.nodes]
        operator_color = [(o.label,o.color) for o in abstract.operators]
        #print('extension node: ',abstract.extension_nodes,f'\n node_color: {node_color},\n\
              #operator color: {operator_color}')

        '''if abstract.extension_nodes == []:
            BST_place_name = [(n.state.name,n.color) for n in abstract.nodes]
            BST_operator_type = [(o.type,o.label,len(o.inn)) for o in abstract.operators]
            #print(f'the BST nodes is: {BST_place_name}, BST operators is: {BST_operator_type}')'''

        for n in abstract.extension_nodes:
            extension_place_name = [(n.state.name,n.color) for n in abstract.extension_nodes]
            #print(f'the extension places is: {extension_place_name}')
            if object in marking[n.state] and not abstract.is_place_occupied(n.state):
                #should avoid object sharing!!!
                #print(f'the place {n.state.name} contains object {object}')
                n.color = 'green'
                #n.end = True
            else:
                build_backward_graph(abstract,n)
        #print('in color_update')
        abstract.color_update()
        #print('out color_update')
    #print('in extract silent sequence')
    silent_sequence = abstract.extract_silent_sequence()
    #print('out extract silent sequence')
    if silent_sequence == None:
        #print('the silent sequence is NONE')
        p,c = 0,0
    else:
        '''if not silent_sequence == []:
            print(f'get BST info: {abstract.get_BST_label()}')
            print(f'the silent sequence is {[tr.name for tr in silent_sequence if tr is not None]}')'''
        #the following code cannot be executed! because once you execute it the marking got changed!
        #print(f'the execute_silent_sequence is {execute_silent_sequence(silent_sequence,marking,object)}')
        '''if execute_silent_sequence(silent_sequence,marking,object) == None:
            print(f'the BST node and operator: {abstract.get_BST_label()}')'''
        #print(f'get BST info: {abstract.get_BST_label()}')
        p,c = execute_silent_sequence(silent_sequence,marking,object)
        print(f'BST silent sequence: {silent_sequence}')

    

    if type(element)==objocpa.ObjectCentricPetriNet.Place:
        m = 0
        missing = []
    elif type(element)==objocpa.ObjectCentricPetriNet.Transition:
        missing = abstract.get_missing_node()
        m = len(missing)
        for pl in missing:
            marking[pl].add(object)
        '''if element.name == 'Pay Order' or element.name == 'Pick Item':
            print(f'---------Pay Order or Pick Item; the BST info: {abstract.get_BST_label()}, then tran: {element.name}')
    '''
    return p,c,m,missing

    #abstract.nodes.add(node)     

def sort_process_execution(process_execution,event_dict):
    event_list = [event_dict[eid] for eid in process_execution]
    sorted_event_list = sorted([event for event in event_list], key=lambda ele: ele.time)
    return sorted_event_list
            
                
            


