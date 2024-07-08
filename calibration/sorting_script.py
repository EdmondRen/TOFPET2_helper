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

parser = argparse.ArgumentParser(
                                prog='Time Sorting Script',
                                description='Sorts events according to time',
                                epilog='MATHUSLA 2024')
parser.add_argument('mapped_filepath')
parser.add_argument('sorted_filepath')
args = parser.parse_args()

mapped_filepath = args.mapped_filepath
sorted_filepath = args.sorted_filepath

tfile = ROOT.TFile.Open(mapped_filepath)
tree_name = tfile.GetListOfKeys()[0].GetName()
Tree = tfile.Get(tree_name)
branches = [Tree.GetListOfBranches()[i].GetName() for i in range(len(Tree.GetListOfBranches()))]
entries = Tree.GetEntries()

times = []
indices = []
for i in range(entries):
    Tree.GetEntry(i)
    times.append(Tree.hit_t)
    indices.append(i)

sorted_indices = [x for _,x in sorted(zip(times,indices))]

tfile.Close()

tfile = ROOT.TFile.Open(mapped_filepath)
tree_name = tfile.GetListOfKeys()[0].GetName()
Tree = tfile.Get(tree_name)
branches = [Tree.GetListOfBranches()[i].GetName() for i in range(len(Tree.GetListOfBranches()))]
entries = Tree.GetEntries()

newFile = ROOT.TFile.Open(sorted_filepath,"RECREATE")
sorted_tree = ROOT.TTree("sorted","sorted_data")
hitx = array('f',[ 0 ])
hity = array('f',[ 0 ])
hitz = array('f',[ 0 ])
hitt = array('f',[ 0 ])
hitxerr = array('f',[ 0 ])
hityerr = array('f',[ 0 ])
hitzerr = array('f',[ 0 ])
hitterr = array('f',[ 0 ])
hitass = array('i',[ 0 ])
hitdetid = array('i',[ 0 ])
hitpairid = array('i',[ 0 ])
hitnrg1 = array('f',[ 0 ])
hitnrg2 = array('f',[ 0 ])
sorted_tree.Branch("hit_x",hitx,"leafname/F")
sorted_tree.Branch("hit_y",hity,"leafname/F")
sorted_tree.Branch("hit_z",hitz,"leafname/F")
sorted_tree.Branch("hit_t",hitt,"leafname/F")
sorted_tree.Branch("hit_x_err",hitxerr,"leafname/F")
sorted_tree.Branch("hit_y_err",hityerr,"leafname/F")
sorted_tree.Branch("hit_z_err",hitzerr,"leafname/F")
sorted_tree.Branch("hit_t_err",hitterr,"leafname/F")
sorted_tree.Branch("hit_ass",hitass,"leafname/I")
sorted_tree.Branch("hit_det_id",hitdetid,"leafname/I")
sorted_tree.Branch("hit_pair_id",hitpairid,"leafname/I")
sorted_tree.Branch("hit_nrg1",hitnrg1,"leafname/F")
sorted_tree.Branch("hit_nrg2",hitnrg2,"leafname/F")

for i in range(len(sorted_indices)):
    Tree.GetEntry(sorted_indices[i])
    hitx[0]=Tree.hit_x
    hity[0]=Tree.hit_y
    hitz[0]=Tree.hit_z
    hitt[0]=Tree.hit_t
    hitxerr[0]=Tree.hit_x_err
    hityerr[0]=Tree.hit_y_err
    hitzerr[0]=Tree.hit_z_err
    hitterr[0]=Tree.hit_t_err
    hitass[0]=Tree.hit_ass
    hitdetid[0]=Tree.hit_det_id
    hitpairid[0]=Tree.hit_pair_id
    hitnrg1[0]=Tree.hit_nrg1
    hitnrg2[0]=Tree.hit_nrg2
    sorted_tree.Fill()
sorted_tree.Write()
newFile.Close()
tfile.Close()