import pm4py
import tempfile
from graphviz import Source
from pm4py.util import exec_utils
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from ocpa.objects.oc_petri_net import obj as objocpa
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
from ocpa.objects.log.importer.csv import factory as csv_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
from multiset import *
import tempfile
from graphviz import Source
from matplotlib import pyplot as plt
import numpy as np
from OCFM import OCEL2OCFM, OCPN2OCFM, EvalOCFM
from model import decomposeOCPN, Restrictedmodel, Flowermodel
from token_based_replay import OC_Conformance, OCtokenbasedreplay
from translation import PNtranslate_OCPA2PM4PY, PNtranslate_PM4PY2OCPA
from pm4py.objects.ocel.util import extended_table
import pandas as pd

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

def Drawcomparisontable(ocellist,ocpnlist,automodel=True):
    col = ['Ground truth','','Flattened TBR','','OC TBR','','Alignment','','FP-based method','']
    col2 = []
    for ele in range(5):
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

        #For different EL format, using different parsing method
        suffix = name.split('.')[-1]
        if suffix == 'csv':
            #CSV is the toughest problem, we have to do attribute mapping!
            #However, pm4py and ocpa accepts different attribute names!!!
            #The following mappings are the minimal mappings for EL parsing! Otherwise error!
            if name == 'BPI2017-Final.csv':
                object_types = ["application", "offer"]
                attrmap1 = {"obj_names":object_types,
                            "val_names":[],
                            "act_name":"event_activity",
                            "time_name":"event_timestamp",
                            "sep":","}
                attrmap2 = {'event_activity':'ocel:activity', 'event_timestamp':'ocel:timestamp', 'event_id':'ocel:eid'\
                               ,'order':'ocel:type:order','application':'ocel:type:application'}
            ELocpa[name] = csv_import_factory.apply(file_path = ocel, parameters = attrmap1)
            table = pd.read_csv(ocel)
            table = table.rename(columns=attrmap2)
            ELpm4py[name] = extended_table.get_ocel_from_extended_table(table,None,parameters={})
        elif suffix == 'jsonocel':
            ELocpa[name] = ocel_import_factory.apply(ocel,variant="ocel_json")
            ELpm4py[name] = pm4py.read_ocel(ocel)
        elif suffix == 'xmlocel':
            ELocpa[name] = ocel_import_factory.apply(ocel,variant="ocel_xml")     
            ELpm4py[name] = pm4py.read_ocel(ocel)
        
        PNocpa[name] = ocpn_discovery_factory.apply(ELocpa[name], parameters={"debug": False})
    if automodel:
        ocpnlist = [PNocpa[name] for name in row]
    a = [PNtranslate_OCPA2PM4PY(pn) for pn in ocpnlist]
    #print('------',a)
    PNpm4py = [PNtranslate_OCPA2PM4PY(pn) for pn in ocpnlist if type(pn)==objocpa.ObjectCentricPetriNet] 
    value = []

    # Used for printing out
    fitness = dict(dict())
    precision = dict(dict())

    for i in range(len(row)):
        row1 = [row[i],'Origin']
        row2 = ['','Flower model']
        row3 = ['','Restricted model']
        #print('@@@@@@',PNpm4py)
        flower = Flowermodel(PNpm4py[i])
        restrict = PNtranslate_OCPA2PM4PY(Restrictedmodel(ELocpa[row[i]]))
        #print('PNpm4py-----',PNpm4py)
        #Now is different to @@@@
        #print('Flower:',flower,"\n restrict",restrict,'\n model:',ELpm4py[row[i]])
        #the flower model and restricted model are the same here
        #break
        fitness[row[i]] = dict()
        precision[row[i]] = dict()
        for j in range(5):
            if j == 0:
                prec1,_ = quality_measure_factory.apply(ELocpa[row[i]], ocpnlist[i])
                _,fit1 = quality_measure_factory.apply(ELocpa[row[i]], ocpnlist[i])
                row1.extend([fit1,prec1])
                prec2,_ = quality_measure_factory.apply(ELocpa[row[i]], PNtranslate_PM4PY2OCPA(flower))
                _,fit2 = quality_measure_factory.apply(ELocpa[row[i]], PNtranslate_PM4PY2OCPA(flower))
                row2.extend([fit2,prec2])
                prec3,_ = quality_measure_factory.apply(ELocpa[row[i]], PNtranslate_PM4PY2OCPA(restrict))
                _,fit3 = quality_measure_factory.apply(ELocpa[row[i]], PNtranslate_PM4PY2OCPA(restrict))
                row3.extend([fit3,prec3])
                #print(i,fit1,prec1,fit2,prec2,fit3,prec3)
                fitness[row[i]]['Ground Truth (o/f/r)'] = [fit1,fit2,fit3]
                precision[row[i]]['Ground Truth (o/f/r)'] = [prec1,prec2,prec3]
            elif j == 1:
                fit1,_ = OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'token-based',True)
                _,prec1 = OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'token-based',True)
                row1.extend([fit1,prec1])
                fit2,_ = OC_Conformance(flower,ELpm4py[row[i]],'token-based',True)
                _,prec2 = OC_Conformance(flower,ELpm4py[row[i]],'token-based',True)
                row2.extend([fit2,prec2])
                fit3,_ = OC_Conformance(restrict,ELpm4py[row[i]],'token-based',True)
                _,prec3 = OC_Conformance(restrict,ELpm4py[row[i]],'token-based',True)
                row3.extend([fit3,prec3])
                fitness[row[i]]['Flattened TBR (o/f/r)'] = [fit1,fit2,fit3]
                precision[row[i]]['Flattened TBR (o/f/r)'] = [prec1,prec2,prec3]
                #print('token',i,fit1,prec1,fit2,prec2,fit3,prec3)
                #print('token',i,OC_Conformance(PNpm4py[i],ELpm4py[row[i]],'token-based',True),\
                      #OC_Conformance(flower,ELpm4py[row[i]],'token-based',True),\
                      #OC_Conformance(restrict,ELpm4py[row[i]],'token-based',True))
                #print('token-----:',flower,restrict,PNpm4py[i],ELpm4py[row[i]])
            elif j == 2:
                prec1, prec2, prec3 = np.nan, np.nan, np.nan
                fit1 = OCtokenbasedreplay(PNocpa[row[i]],ELocpa[row[i]])
                row1.extend([fit1,prec1])
                fit2 = OCtokenbasedreplay(PNtranslate_PM4PY2OCPA(flower),ELocpa[row[i]])
                row2.extend([fit2,prec2])
                fit3 = OCtokenbasedreplay(PNtranslate_PM4PY2OCPA(restrict),ELocpa[row[i]])
                row3.extend([fit3,prec3])
                fitness[row[i]]['OC TBR (o/f/r)'] = [fit1,fit2,fit3]
                precision[row[i]]['OC TBR (o/f/r)'] = [prec1,prec2,prec3]
            elif j == 3:
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
                    
                #print('alignment',i,fit1,prec1,fit2,prec2,fit3,prec3)
                row1.extend([fit1,prec1])
                row2.extend([fit2,prec2])
                row3.extend([fit3,prec3])
                fitness[row[i]]['Flattened Alignment (o/f/r)'] = [fit1,fit2,fit3]
                precision[row[i]]['Flattened Alignment (o/f/r)'] = [prec1,prec2,prec3]
            elif j == 4:
                fitness[row[i]]['FPB Method (o/f/r)'] = []
                precision[row[i]]['FPB Method (o/f/r)'] = []
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
                    ocpn = decomposeOCPN(model)
                    ocfmmodel = OCPN2OCFM(ocpn)
                    ocfmlog = OCEL2OCFM(ELpm4py[row[i]])
                    fit,_,_ = EvalOCFM(ocfmlog,ocfmmodel)
                    _,prec,_ = EvalOCFM(ocfmlog,ocfmmodel)
                    currow.extend([fit,prec])
                    fitness[row[i]]['FPB Method (o/f/r)'].append(fit)
                    precision[row[i]]['FPB Method (o/f/r)'].append(prec)
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
        mergecells(table,[(2+3*i,0),(2+3*i+1,0),(2+3*i+2,0)])
    #tab.scale(1,2)

    #Collect the outputs
    return 'The fitness is: ' + ', '.join([str(fitness[row[i]]) for i in range(len(row))]) + \
       '\nThe precision is: ' + ', '.join([str(precision[row[i]]) for i in range(len(row))])