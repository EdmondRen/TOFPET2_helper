#!/usr/bin/python3
import numpy as np
from math import sqrt 
import joblib
import ROOT
from array import array
import argparse
import os, sys
import shutil

#Handle input arguments
parser = argparse.ArgumentParser(
                                prog='Trigger Script',
                                description='Groups Events within time window',
                                epilog='MATHUSLA 2024')
parser.add_argument('mapped_filepath')
parser.add_argument('triggered_filepath')
parser.add_argument('time_window')
args = parser.parse_args()

#File paths
mapped_filepath = args.mapped_filepath
mapped_filename = os.path.basename(mapped_filepath)
if args.triggered_filepath[-5:]!=".root":
    triggered_filepath = args.triggered_filepath + mapped_filename.replace(".root", "_final.root")
else:
    triggered_filepath = args.triggered_filepath
os.makedirs(os.path.dirname(triggered_filepath), exist_ok=True)
timewindow = np.float128(args.time_window) #ns

# Open the source file (list of hits)
tfile = ROOT.TFile.Open(mapped_filepath)
tree_name = tfile.GetListOfKeys()[0].GetName()
Tree = tfile.Get(tree_name)
branches = [Tree.GetListOfBranches()[i].GetName() for i in range(len(Tree.GetListOfBranches()))]
entries = Tree.GetEntries()

# Open a new file to save result
newFile = ROOT.TFile.Open(triggered_filepath,"RECREATE")
triggered_tree = ROOT.TTree("triggered","triggered_data")

# Get a sorted list of time
times = ROOT.RDataFrame(tree_name, mapped_filepath).AsNumpy(columns=["hit_t"])["hit_t"]
sorted_indices = np.argsort(times)

hitxs = ROOT.vector('float')()
hitys = ROOT.vector('float')()
hitzs = ROOT.vector('float')()
hitts = ROOT.vector('double')()
hitxerrs = ROOT.vector('float')()
hityerrs = ROOT.vector('float')()
hitzerrs = ROOT.vector('float')()
hitterrs = ROOT.vector('float')()
hitlays = ROOT.vector('int')()
hitasss = ROOT.vector('int')()
hitdetids = ROOT.vector('int')()
hitpairids = ROOT.vector('int')()
hitnrg1s = ROOT.vector('float')()
hitnrg2s = ROOT.vector('float')()
triggered_tree.Branch("hit_x",hitxs)
triggered_tree.Branch("hit_y",hitys)
triggered_tree.Branch("hit_z",hitzs)
triggered_tree.Branch("hit_t",hitts)
triggered_tree.Branch("hit_x_err",hitxerrs)
triggered_tree.Branch("hit_y_err",hityerrs)
triggered_tree.Branch("hit_z_err",hitzerrs)
triggered_tree.Branch("hit_t_err",hitterrs)
triggered_tree.Branch("hit_layer",hitlays)
triggered_tree.Branch("hit_ass",hitasss)
triggered_tree.Branch("hit_det_id",hitdetids)
triggered_tree.Branch("hit_pair_id",hitpairids)
triggered_tree.Branch("hit_nrg1",hitnrg1s)
triggered_tree.Branch("hit_nrg2",hitnrg2s)

ind_counter = 0
ind = sorted_indices[ind_counter]
window_count = 0
initial_t = 0

# Print 20 times
nprint = 20
entries_print = entries//nprint
print(f"Triggering. Event time window {args.time_window}")
while ind_counter < entries:

    if (ind_counter-1)%(entries_print)==entries_print-1:
        print(f"{ind_counter}/{entries} events ({ind_counter/entries*100:.1f}%)", end="\r")

    Tree.GetEntry(ind)
    initial_t = Tree.hit_t
    hitxs.push_back(Tree.hit_x)
    hitys.push_back(Tree.hit_y)
    hitzs.push_back(Tree.hit_z)
    hitts.push_back(Tree.hit_t)
    hitxerrs.push_back(Tree.hit_x_err)
    hityerrs.push_back(Tree.hit_y_err)
    hitzerrs.push_back(Tree.hit_z_err)
    hitterrs.push_back(Tree.hit_t_err)
    hitlays.push_back(Tree.hit_layer)
    hitasss.push_back(Tree.hit_ass)
    hitdetids.push_back(Tree.hit_det_id)
    hitpairids.push_back(Tree.hit_pair_id)
    hitnrg1s.push_back(Tree.hit_nrg1)
    hitnrg2s.push_back(Tree.hit_nrg2)
    ind_counter += 1
    if ind_counter < entries:
        ind = sorted_indices[ind_counter]
        window_count += 1
        Tree.GetEntry(ind)
        diff = abs(Tree.hit_t - initial_t)
        #If the next entry is within the timewindow, append to vector and check subsequent entries
        while diff < timewindow:
            hitxs.push_back(Tree.hit_x)
            hitys.push_back(Tree.hit_y)
            hitzs.push_back(Tree.hit_z)
            hitts.push_back(Tree.hit_t)
            hitxerrs.push_back(Tree.hit_x_err)
            hityerrs.push_back(Tree.hit_y_err)
            hitzerrs.push_back(Tree.hit_z_err)
            hitterrs.push_back(Tree.hit_t_err)
            hitlays.push_back(Tree.hit_layer)
            hitasss.push_back(Tree.hit_ass)
            hitdetids.push_back(Tree.hit_det_id)
            hitpairids.push_back(Tree.hit_pair_id)
            hitnrg1s.push_back(Tree.hit_nrg1)
            hitnrg2s.push_back(Tree.hit_nrg2)
            ind_counter += 1
            if ind_counter < entries:
                ind = sorted_indices[ind_counter]
                window_count += 1
                Tree.GetEntry(ind)
                diff = abs(Tree.hit_t - initial_t)
            else:
                diff = timewindow + 1
        if window_count >= 3:
            triggered_tree.Fill()
        #Reset values
    window_count = 0
    hitxs.clear()
    hitys.clear()
    hitzs.clear()
    hitts.clear()
    hitxerrs.clear()
    hityerrs.clear()
    hitzerrs.clear()
    hitterrs.clear()
    hitlays.clear()
    hitasss.clear()
    hitdetids.clear()
    hitpairids.clear()
    hitnrg1s.clear()
    hitnrg2s.clear()
print("\nFinished, file saved as ", triggered_filepath)
triggered_tree.Write()
tfile.Close()
newFile.Close()

