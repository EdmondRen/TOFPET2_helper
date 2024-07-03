import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
import scipy.signal
from math import sqrt 
import joblib
import csv
import ROOT
from IPython.display import display
import json
from array import array
import argparse

id_mapping = "../configurations/MATHUSLA teststand pinout - Preamp to ASIC.csv" #asic mappings
inputs_path = "../configurations/teststand_config.json" #module info
pair_info = "../configurations/MATHUSLA teststand pinout - Channel_pair.csv" #pair information

parser = argparse.ArgumentParser(
                    prog='Mapper Script',
                    description='Maps raw data to coordinates',
                    epilog='MATHUSLA 2024')
parser.add_argument('filepath')
parser.add_argument('mapped_filepath')

args = parser.parse_args()
filepath = args.filepath
mapped_filepath = args.mapped_filepath

idmap = {}
with open(id_mapping) as id_map_file:
    linecount = 0
    id_reader = csv.reader(id_map_file, delimiter=',')
    for row in id_reader:
        if linecount == 0:
            linecount += 1
            continue
        else:
            linecount += 1
            idmap[int(row[7])] = [int(row[11]),int(row[1]),int(row[9]),int(row[10])]

input_file = open(inputs_path)
inputs = json.load(input_file)
input_file.close()

pair_details = {}
with open(pair_info) as pair_info_file:
    linecount = 0
    pair_reader = csv.reader(pair_info_file, delimiter=',')
    for row in pair_reader:
        if linecount == 0:
            linecount += 1
            continue
        else:
            linecount += 1
            pair_details[int(row[0])] = [int(row[0]),np.float64(row[1]),np.float64(row[2]),np.float64(row[3]),np.float64(row[4])]

def assembly(abschid,idmap):
    return int(idmap[abschid][0])

def channel(abschid,idmap):
    return int(idmap[abschid][1])

def ass_ch(abschid,idmap):
    return int(idmap[abschid][0]),int(idmap[abschid][1])

def det_id(abschid,idmap):
    return int(idmap[abschid][2])

def pair_id(abschid,idmap):
    return int(idmap[abschid][3])

def det_pair(abschid,idmap):
    return int(idmap[abschid][2]),int(idmap[abschid][3])

def checkhit(ass1,ass2,ch1,ch2):
    if ass1 == ass2:
        if abs(ch1-ch2) == 5:
            return 1
        else:
            return 0
    else:
        return 0
    
def hit_coord(t1,t2,pair_id,pair_details,inputs):
    c_wsf = 29.9792458/inputs["global"]["fiber_refraction_index"]
    time_dif = abs(t1-t2)
    total_t = pair_details[pair_id][4]/c_wsf
    t = (total_t - time_dif)/2
    hit_d = c_wsf * t
    hit_t = (t1+t2)/2 #min(t1,t2) - t
    return hit_d,hit_t

def lev_civ(indices):
    return ((indices[0]-indices[1])*(indices[1]-indices[2])*(indices[2]-indices[0]))/2

# def mapper(hi_ass,lo_ass,hi_ch,lo_ch,hi_id,lo_id,hi_t,lo_t,pair_id,idmap,inputs,pair_details):
#     pair_adj_mean = (inputs["global"]["bars_pcb_time_offset"][lo_ch-1]+inputs["global"]["bars_pcb_time_offset"][hi_ch-1])/2
#     hi_t_adj = (hi_t/1000)-pair_adj_mean-inputs["assemblies"][str(hi_ass)]["cable_time_offset"]-pair_details[pair_id][2]-pair_details[pair_id][3]-(pair_details[pair_id][1]/2) #the -1 is important!
#     lo_t_adj = (lo_t/1000)-pair_adj_mean-inputs["assemblies"][str(hi_ass)]["cable_time_offset"]-pair_details[pair_id][2]-pair_details[pair_id][3]+(pair_details[pair_id][1]/2)
#     m,hit_t = hit_coord(hi_t_adj,lo_t_adj,pair_id,pair_details,inputs)
#     det_dir = inputs["assemblies"][str(hi_ass)]["direction"][0]
#     ass_dir = inputs["assemblies"][str(hi_ass)]["direction"][1]
#     ref_coord = [inputs["assemblies"][str(hi_ass)]["reference_point"][0],inputs["assemblies"][str(hi_ass)]["reference_point"][1],inputs["assemblies"][str(hi_ass)]["reference_point"][2]]
#     assembly_width = inputs["global"]["assembly_width"]
#     bar_width = inputs["global"]["bar_width"]
#     pos_unc = [0,0,0] #add uncertainties later
#     t_unc = inputs["global"]["time_resolution"]
#     if hi_t_adj >= lo_t_adj:
#         hit_det_id = lo_id
#         hit_ch = lo_ch
#     else:
#         hit_det_id = hi_id
#         hit_ch = hi_ch

#     # loc_coord = [m,-(hit_ch-1)*bar_width,0]
#     ind_map = [abs(det_dir),6-abs(det_dir)-abs(ass_dir),abs(ass_dir)]
#     sign = lev_civ(ind_map)
#     signed_coord = [m*det_dir/abs(det_dir),(-(hit_ch-1)*bar_width)*sign*(det_dir*ass_dir/abs(det_dir*ass_dir)),0*ass_dir/abs(ass_dir)]
#     ind_map = np.array(ind_map)-1
#     final_coords = np.zeros(3)
#     final_uncerts = np.zeros(3)
#     for i in range(3):
#         final_coords[ind_map[i]] = signed_coord[i]
#         final_uncerts[ind_map[i]] = pos_unc[i] 
#     final_coords += np.array(ref_coord)

#     return pd.Series([final_coords[0],final_coords[1],final_coords[2],hit_t,final_uncerts[0],final_uncerts[1],final_uncerts[2],t_unc,int(hi_ass),int(hit_det_id),int(pair_id)])

def mapper2(hi_ass,lo_ass,hi_ch,lo_ch,hi_id,lo_id,hi_t,lo_t,pair_id,idmap,inputs,pair_details):
    pair_adj_mean = (inputs["global"]["bars_pcb_time_offset"][lo_ch-1]+inputs["global"]["bars_pcb_time_offset"][hi_ch-1])/2
    hi_t_adj = (hi_t/1000)-pair_adj_mean-inputs["assemblies"][str(hi_ass)]["cable_time_offset"]-pair_details[pair_id][2]-(pair_details[pair_id][1]/2) #the -1 is important!
    lo_t_adj = (lo_t/1000)-pair_adj_mean-inputs["assemblies"][str(hi_ass)]["cable_time_offset"]-pair_details[pair_id][2]+(pair_details[pair_id][1]/2)
    m,hit_t = hit_coord(hi_t_adj,lo_t_adj,pair_id,pair_details,inputs)
    det_dir = inputs["assemblies"][str(hi_ass)]["direction"][0]
    ass_dir = inputs["assemblies"][str(hi_ass)]["direction"][1]
    ref_coord = [inputs["assemblies"][str(hi_ass)]["reference_point"][0],inputs["assemblies"][str(hi_ass)]["reference_point"][1],inputs["assemblies"][str(hi_ass)]["reference_point"][2]]
    assembly_width = inputs["global"]["assembly_width"]
    bar_width = inputs["global"]["bar_width"]
    pos_unc = [0,0,0] #add uncertainties later
    t_unc = inputs["global"]["time_resolution"]
    if hi_t_adj >= lo_t_adj:
        hit_det_id = lo_id
        hit_ch = lo_ch
    else:
        hit_det_id = hi_id
        hit_ch = hi_ch

    # loc_coord = [m,-(hit_ch-1)*bar_width,0]
    ind_map = [abs(det_dir),6-abs(det_dir)-abs(ass_dir),abs(ass_dir)]
    sign = lev_civ(ind_map)
    signed_coord = [m*det_dir/abs(det_dir),(-(hit_ch-1)*bar_width)*sign*(det_dir*ass_dir/abs(det_dir*ass_dir)),0*ass_dir/abs(ass_dir)]
    ind_map = np.array(ind_map)-1
    final_coords = np.zeros(3)
    final_uncerts = np.zeros(3)
    for i in range(3):
        final_coords[ind_map[i]] = signed_coord[i]
        final_uncerts[ind_map[i]] = pos_unc[i] 
    final_coords += np.array(ref_coord)
    return final_coords[0],final_coords[1],final_coords[2],hit_t,final_uncerts[0],final_uncerts[1],final_uncerts[2],t_unc,int(hi_ass),int(hit_det_id),int(pair_id)

tfile = ROOT.TFile.Open(filepath)
tree_name = tfile.GetListOfKeys()[0].GetName()
Tree = tfile.Get(tree_name)
branches = [Tree.GetListOfBranches()[i].GetName() for i in range(len(Tree.GetListOfBranches()))]
entries = Tree.GetEntries()

newFile = ROOT.TFile.Open(mapped_filepath,"RECREATE")
mapped_tree = ROOT.TTree("mapped","mapped_data")
hitx = array('f',[ 0 ])
hity = array('f',[ 0 ])
hitz = array('f',[ 0 ])
hitt = array('d',[ 0 ])
hitxerr = array('f',[ 0 ])
hityerr = array('f',[ 0 ])
hitzerr = array('f',[ 0 ])
hitterr = array('f',[ 0 ])
hitass = array('i',[ 0 ])
hitdetid = array('i',[ 0 ])
hitpairid = array('i',[ 0 ])
hitnrg1 = array('f',[ 0 ])
hitnrg2 = array('f',[ 0 ])
mapped_tree.Branch("hit_x",hitx,"leafname/F")
mapped_tree.Branch("hit_y",hity,"leafname/F")
mapped_tree.Branch("hit_z",hitz,"leafname/F")
mapped_tree.Branch("hit_t",hitt,"leafname/D")
mapped_tree.Branch("hit_x_err",hitxerr,"leafname/F")
mapped_tree.Branch("hit_y_err",hityerr,"leafname/F")
mapped_tree.Branch("hit_z_err",hitzerr,"leafname/F")
mapped_tree.Branch("hit_t_err",hitterr,"leafname/F")
mapped_tree.Branch("hit_ass",hitass,"leafname/I")
mapped_tree.Branch("hit_det_id",hitdetid,"leafname/I")
mapped_tree.Branch("hit_pair_id",hitpairid,"leafname/I")
mapped_tree.Branch("hit_nrg1",hitnrg1,"leafname/F")
mapped_tree.Branch("hit_nrg2",hitnrg2,"leafname/F")

for x in range(entries):
    Tree.GetEntry(x)
    hi_ass,hichannel = ass_ch(Tree.channelID1,idmap)
    lo_ass,lochannel = ass_ch(Tree.channelID2,idmap)
    if checkhit(hi_ass,lo_ass,hichannel,lochannel)==1:
        hi_detid,hi_pairid=det_pair(Tree.channelID1,idmap)
        lo_detid,lo_pairid=det_pair(Tree.channelID2,idmap)
        hitx[0],hity[0],hitz[0],hitt[0],hitxerr[0],hityerr[0],hitzerr[0],hitterr[0],hitass[0],hitdetid[0],hitpairid[0]=mapper2(hi_ass,lo_ass,hichannel,lochannel,hi_detid,lo_detid,Tree.time1,Tree.time2,hi_pairid,idmap,inputs,pair_details)
        hitnrg1[0] = Tree.energy1
        hitnrg2[0] = Tree.energy2
        mapped_tree.Fill()
mapped_tree.Write()
tfile.Close()
newFile.Close()