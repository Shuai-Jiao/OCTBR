from pm4py.objects.petri_net import obj as objpm4py
from ocpa.objects.oc_petri_net import obj as objocpa
from ocpa.objects.log.exporter.ocel.factory import apply as ocpaexporter
import pm4py
from multiset import *

def Activityvariability(act,net):
    for arc in net.arcs:
        if (arc.source.name == act or arc.target.name == act) and arc.variable == True:
            return True
    return False

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
            # ? so you used ocpa's arcs as input of the pm4py transition ?
            #transition = objpm4py.PetriNet.Transition(tr.name,label,tr.in_arcs,tr.out_arcs,tr.properties)
            transition = objpm4py.PetriNet.Transition(tr.name,label)
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
    #You can just remove pnpm4py['activities] and see what kind of errors will occur!
    #print(pnpm4py['activities'])

    #Reconstruct the place with arcs
    for ot in pnpm4py['object_types']:
        for pl in pnpm4py['petri_nets'][ot][0].places:
            in_arcs = set()
            out_arcs = set()
            for arc in pnpm4py['petri_nets'][ot][0].arcs:
                if arc.target == pl:
                    in_arcs.add(arc)
                if arc.source == pl:
                    out_arcs.add(arc)
            pl._Place__in_arcs = in_arcs
            pl._Place__out_arcs = out_arcs
    #Reconstruct the transition with arcs
        for tr in pnpm4py['petri_nets'][ot][0].transitions:
            in_arcs = set()
            out_arcs = set()
            for arc in pnpm4py['petri_nets'][ot][0].arcs:
                if arc.target == tr:
                    in_arcs.add(arc)
                if arc.source == tr:
                    out_arcs.add(arc)
            tr._Transition__in_arcs = in_arcs
            tr._Transition__out_arcs = out_arcs

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

# convert the ocel first to json, then to pm4py ocel
def ELtranslate_OCPA2PM4PY(ocel,export_path='./sample_logs/jsonocel/intermediate.jsonocel'):
    ocpaexporter(ocel,export_path)
    return pm4py.read_ocel(export_path)

def PNtranslate_PM4PY2OCPA(ocpn):
    ocpapn = objocpa.ObjectCentricPetriNet()

    for ot in ocpn['object_types']:
        #first construct places and enrich later
        for pl in ocpn['petri_nets'][ot][0].places:
            i,f = False,False
            #print('@@',type(p),ocpn['petri_nets'][pl.object_type][1][p])
            if ocpn['petri_nets'][ot][1][pl]==1:
                i = True
            if ocpn['petri_nets'][ot][2][pl]==1:
                f = True            
            place = objocpa.ObjectCentricPetriNet.Place(name = ot+pl.name, object_type = ot, initial=i, final=f)
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
        #returned p is in pm4py
        #p = Returncorrespondence(pl,ocpn['petri_nets'][pl.object_type][0],pl.object_type)
        # i and f indicate start or end place
        ##if ocpn['petri_nets'][pl.object_type][1][p]==1:
            #i = True
        #if ocpn['petri_nets'][pl.object_type][2][p]==1:
            #f = True
        #print(type(pl),type(ocpapn.places))
        #p = pl
        # You cannot just remove the old place and then add a new one! Because the linkage of the \
        # new arcs don't have dependency with the new places!!!
        pl._Place__in_arcs = inarcs
        pl._Place__out_arcs = outarcs
        #ocpapn._Place__initial = i
        #ocpapn._Place__final = f
        #ocpapn.places.remove(p)
        #pl = objocpa.ObjectCentricPetriNet.Place(pl.name,pl.object_type,outarcs,inarcs,i,f)
        #p = pl
        #ocpapn.places.add(p)
    for tr in ocpapn.transitions:
        inarcs = set()
        outarcs = set()
        for a in ocpapn.arcs:
            if a.source.name == tr.name:
                outarcs.add(a)
            if a.target.name == tr.name:
                inarcs.add(a)
        tr._Transition__in_arcs = inarcs
        tr._Transition__out_arcs = outarcs
        #t = tr
        #ocpapn.transitions.remove(t)
        #tr = objocpa.ObjectCentricPetriNet.Transition(tr.name,tr.label,inarcs,outarcs,None,tr.silent)
        #t = tr
        #ocpapn.transitions.add(t)

    '''for arc in ocpapn.arcs:
        #if arc.source.name == "productstau1" or arc.target.name == "productstau1":
            #print('kalala')
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
        #if s.name == "productstau1" or t.name == "productstau1":
            print('hhhhh')
        a = arc
        ocpapn.arcs.remove(a)
        arc = objocpa.ObjectCentricPetriNet.Arc(s,t,arc.variable)
        a = arc
        ocpapn.arcs.add(a)'''
    return ocpapn