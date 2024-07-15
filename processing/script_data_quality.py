#!/usr/bin/python3
import numpy as np
from math import sqrt 
import joblib
import ROOT
from array import array
import argparse
import os, sys
import shutil

from pylab import *

import muhelper.include_modules_root as hproot


def plot_TH1(h, labels=False, density=False):
    n,ibins,errs=hproot.get_info(h)
    xlabel=h.GetXaxis().GetTitle()
    ylabel=h.GetYaxis().GetTitle()
    if density:
        n = n/np.diff(ibins)
    plt.stairs(n,ibins)
    if labels:
        figtitle=h.GetTitle()
        gca().set_xlabel(xlabel)
        gca().set_ylabel(ylabel)
        # gca().set_title(figtitle)

def process_result(fname_singles, fname_coinc, fname_recon):
    """
    INPUT: 
        three filenames for single events, coincident event and reconstruction
    RETURN:
        Dictionary of plot data
    """
    #-------------------------------------------------------------------
    # Singles
    tfile = ROOT.TFile.Open(fname_singles)
    tree_name = tfile.GetListOfKeys()[0].GetName()
    Tree = tfile.Get(tree_name)
    entries = Tree.GetEntries()
    df = ROOT.RDataFrame(tree_name, fname_singles)
    df = df.Define("time_second", "time*1e-12") # Use dataframe to quickly get things into numpy
    df_keys = list(df.GetColumnNames()); print(list(df.GetColumnNames()))

    # channel list
    singles_ch_list = np.unique(df.AsNumpy(["channelID"])["channelID"])
    time_range = []
    for i in [0,entries-1]:
        Tree.GetEntry(i)
        time_range.append(Tree.time*1e-12)
    time_bins = 100
    time_bin_width = (time_range[1]-time_range[0])/time_bins
    energy_range=[-10,40]
    energy_bins=100

    print("List of single channels:", singles_ch_list, "Time range:", time_range)

    # Trigger rate and energy histograms
    hist1_single_rate={}
    hist2_single_energy={}
    for ch in singles_ch_list:
        df_filter = df.Filter(f"channelID=={ch}")
        hist1_single_rate[ch] = hproot.get_info(df_filter.Histo1D(("", f";Time [s];Rate [Hz]", time_bins, *time_range), "time_second"))
        hist2_single_energy[ch] = hproot.get_info(df_filter.Histo1D(("", f";Energy [];Counts [/{0.5:.1f}s bin]", energy_bins, *energy_range), "energy"))


    #-------------------------------------------------------------------
    # Coincidence
    tfile = ROOT.TFile.Open(fname_coinc)
    tree_name = tfile.GetListOfKeys()[0].GetName()
    Tree = tfile.Get(tree_name)
    entries = Tree.GetEntries()
    branches = [Tree.GetListOfBranches()[i].GetName() for i in range(len(Tree.GetListOfBranches()))]
    print(branches)
    df = ROOT.RDataFrame(tree_name, fname_coinc)
    df = df.Define('dt_ns', '0.001*(time1-time2)')\
        .Define('t_mean_second', '0.5*1e-12*(time1+time2)')

    # channel list
    coinc_ch_list = df.AsNumpy(["channelID1","channelID2"])
    coinc_ch_list = np.unique(np.transpose([coinc_ch_list[key1] for key1 in coinc_ch_list]), axis=0)
    print("List of coincidence channel pairs:", coinc_ch_list)
    dt_range_coinc = [-25,25]
    dt_bins_coinc = 100
    dt_bin_width_coinc = (dt_range_coinc[1]-dt_range_coinc[0])/dt_bins_coinc

    # Trigger rate and dt histograms
    hist3_coinc_rate={}
    hist4_coinc_dt={}
    for pair in coinc_ch_list:
        df_filter = df.Filter(f"channelID1=={pair[0]} && channelID2=={pair[1]}")
        hist3_coinc_rate[tuple(pair)] = hproot.get_info(df_filter.Histo1D(("", f";Time [s];Rate [Hz]", time_bins, *time_range), "t_mean_second"))
        hist4_coinc_dt[tuple(pair)]   = hproot.get_info(df_filter.Histo1D(("", f";dt [ns];Counts [/{dt_bin_width_coinc:.1f}ns bin]", dt_bins_coinc, *dt_range_coinc), "dt_ns"))


    #-------------------------------------------------------------------
    # Reconstructed
    data = joblib.load(fname_recon)
    tracks = data["tracks"]
    tracks_time = []
    tracks_chi2r = []
    for ievent in range(len(tracks)):
        for track in tracks[ievent]:
            tracks_time.append(track.t0*1e-9) # ns to s
            track_dof = 3*len(track.hits)-6
            tracks_chi2r.append(track.chi2/track_dof)

    hist5_tracks_time = np.histogram(tracks_time, bins=100, range=time_range)
    hist6_tracks_chi2 = np.histogram(tracks_chi2r, bins=50, range=[0,4])

    plotdata = {
        "hist1_single_rate":hist1_single_rate,
        "hist2_single_energy":hist2_single_energy,
        "hist3_coinc_rate":hist3_coinc_rate,
        "hist4_coinc_dt":hist4_coinc_dt,
        "hist5_tracks_time":hist5_tracks_time,
        "hist6_tracks_chi2":hist6_tracks_chi2,
    }

    return plotdata




def make_plots(plotdata, fig=None, plot_singles_list=None, plot_coinc_list=None):
    # Prepare the canvas
    if fig is None:
        fig,axes=plt.subplots(2, 3, figsize=(12, 6), dpi=100, tight_layout=True)
        axes=axes.flat
    else:
        axes=fig.axes


    plot_singles_list = list(plotdata["hist1_single_rate"].keys()) if plot_singles_list is None else plot_singles_list
    plot_coinc_list = list(plotdata["hist3_coinc_rate"].keys()) if plot_coinc_list is None else plot_coinc_list

    for i, ax in enumerate(axes):
        ax.tick_params(axis="x", direction='in', pad = 3)
        ax.tick_params(axis="y", direction='in', pad = 3)

    # 1. singles trigger rate
    ax = axes[0]
    if len(plot_singles_list)>0:
        for ch in plot_singles_list:
            ax.stairs(plotdata["hist1_single_rate"][ch][0],plotdata["hist1_single_rate"][ch][1])
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Rate [Hz]", labelpad=0)
    ax.text(0.98, 0.9, 'Singles rate', horizontalalignment='right',
     verticalalignment='center', transform=ax.transAxes, fontsize=16, fontweight="bold")            
    ax.margins(x=0, y=0)


    # 2. singles energy
    ax = axes[3]
    if len(plot_singles_list)>0:
        for ch in plot_singles_list[:-1]:
            ax.stairs(plotdata["hist2_single_energy"][ch][0],plotdata["hist2_single_energy"][ch][1])
    ax.set_xlabel("Energy [s]")
    ax.set_ylabel("Counts", labelpad=0)
    ax.text(0.98, 0.9, 'Singles energy', horizontalalignment='right',
     verticalalignment='center', transform=ax.transAxes, fontsize=16, fontweight="bold")                    
    ax.margins(x=0, y=0)

    # 3. coinc trigger rate
    ax = axes[1]
    if len(plot_coinc_list)>0:
        for ch in plot_coinc_list[:-1]:
            ax.stairs(plotdata["hist3_coinc_rate"][ch][0],plotdata["hist3_coinc_rate"][ch][1])
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Rate [Hz]", labelpad=0)
    ax.text(0.98, 0.9, 'coinc rate', horizontalalignment='right',
     verticalalignment='center', transform=ax.transAxes, fontsize=16, fontweight="bold", color="C1")        
    ax.margins(x=0, y=0)


    # 4. coinc dt
    ax = axes[4]
    if len(plot_coinc_list)>0:
        for ch in plot_coinc_list[:-1]:
            ax.stairs(plotdata["hist4_coinc_dt"][ch][0],plotdata["hist4_coinc_dt"][ch][1])
    ax.set_xlabel("$\delta$t [ns]")
    ax.set_ylabel("Counts", labelpad=0)
    ax.text(0.98, 0.9, 'coinc dt', horizontalalignment='right',
     verticalalignment='center', transform=ax.transAxes, fontsize=16, fontweight="bold", color="C1")                    
    ax.margins(x=0, y=0)


    # 5. Tracks rate
    ax = axes[2]
    n,ibins = plotdata["hist5_tracks_time"]
    ax.stairs(n,ibins)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Rate [Hz]", labelpad=0)
    ax.text(0.98, 0.9, 'track rate', horizontalalignment='right',
     verticalalignment='center', transform=ax.transAxes, fontsize=16, fontweight="bold", color="C2")      
    ax.margins(x=0, y=0)

    # 5. Tracks chi2
    ax = axes[5]
    n,ibins = plotdata["hist6_tracks_chi2"]
    ax.stairs(n,ibins)
    ax.set_xlabel("$\chi^2$/DOF")
    ax.set_ylabel("Counts", labelpad=0)
    ax.text(0.98, 0.9, 'track chi2', horizontalalignment='right',
     verticalalignment='center', transform=ax.transAxes, fontsize=16, fontweight="bold", color="C2")    
    ax.margins(x=0, y=0)

    return fig


#-------------------------------------------------------------------------------------------------------------------------\
# Main

if __name__ == "__main__":
    #Handle input arguments
    parser = argparse.ArgumentParser(
                                    prog='Data quality plots',
                                    description='Generate data quality plots for hits, events and tracks',
                                    epilog='MATHUSLA 2024')
    parser.add_argument('fname_singles')
    parser.add_argument('fname_coinc')
    parser.add_argument('fname_recon')
    args = parser.parse_args()

    #File paths
    fname_singles = args.fname_singles
    fname_coinc = args.fname_coinc
    fname_recon = args.fname_recon
    if not (os.path.exists(fname_singles) & os.path.exists(fname_coinc) & os.path.exists(fname_recon)):
        print("File not found")
        exit(0)



    # Run processing
    plotdata = process_result(fname_singles, fname_coinc, fname_recon)
    # Make plots
    fig = make_plots(plotdata, fig=None, plot_singles_list=None, plot_coinc_list=None)

    # Save the processed result and plot in the same folder as input filie.
    fig.savefig(fname_singles.replace("single.root", "data_quality.jpg"))
    joblib.dump(plotdata, fname_singles.replace("single.root", "data_quality.joblib"))    

