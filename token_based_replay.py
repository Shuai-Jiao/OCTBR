import pm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from multiset import *

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
    fitness = sum([fitdict[ot]*elweight[ot] for ot in ocpn['object_types']])
    if getprecision:
        precision = sum([precdict[ot]*pnweight[ot] for ot in ocpn['object_types']])
    if getprecision:
        return fitness, precision
    else:
        return fitness
    
def OCtokenbasedreplay(ocpn,ocel,handle_silence=False):
    #start with the initial
    if type(ocpn) is not objocpa.ObjectCentricPetriNet:
        raise ValueError("The ocpn format is not well-defined in ocpa")
    eventdict = ocel.obj.raw.events
    acttrans = []
    p,m,c,r = 0,0,0,0
    #the tokens(objects) in the corresponding place
    marking: Dict[objocpa.Place,Multiset]
    marking = {}
    for eventID in eventdict:
        event = eventdict[eventID]
        tr = ocpn.find_transition(event.act)
        for obj in event.omap:
            #Consider precondition
            missing = True
            for arc in tr.in_arcs:
                #Check whether the marking is initialized
                Initializemarking(marking,arc.source)
                #first determine whether the start place for the corr. type is
                if arc.source.initial and arc.source.object_type == Findobject(ocel,obj).type:
                    missing = False
                    p += 1
                    c += 1
                #discuss the case the token exist for firing
                elif obj in marking[arc.source]:
                    #fire all possible token
                    #marking_copy = copy.deepcopy(marking[arc.source])
                    marking[arc.source].remove(obj)
                    missing = False
                    c += 1
            if missing:
                m += 1
                c += 1
            #Consider effect
            for arc in tr.out_arcs:
                #use the obj's name to find the obj
                #instance = Findobject(ocel,obj)
                #It has to be set for the two if-statement
                
                if arc.target.object_type == Findobject(ocel,obj).type:
                    Initializemarking(marking,arc.target)
                    marking[arc.target].add(obj)
                    p += 1
                #consider the end place
                if arc.target.final and arc.target.object_type == Findobject(ocel,obj).type:
                    print(arc.target.object_type,obj)
                    #Initializemarking(marking,arc.target)
                    if obj in marking[arc.target]:
                        marking[arc.target].remove(obj)
                    c += 1
    for k in marking.keys():
            r += len(marking[k])
    #print(p,c,m,r,p+m,c+r)
    return 1/2*(1-m/c)+1/2*(1-r/p)

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
