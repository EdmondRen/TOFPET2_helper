#include <stdio.h>
#include <vector>
#include <iterator>
#include <iostream>
#include <filesystem>
#include <fstream>
#include <list>
#include <random>
#include <map>
#include <algorithm>
#include <chrono>

#include "TFile.h"
#include "TTree.h"
#include "Riostream.h"
#include "TROOT.h"
#include "TH1F.h"
#include "TNtuple.h"
#include "TKey.h"
#include "TIterator.h"

//FINAL ITERATOR - USE THIS ONE

using namespace std;
namespace fs = filesystem;
void lin_regress(vector<double> xs,vector<double> ys, double *slopeint);
int dim;
int vec_len; 
double c = 29.18853457; //speed of muons set here

int main(int argc, char *argv[]){
    string data_dir = string(argv[1]);
    // string data_dir = "bat_data6";
    vector<TString> filenames = {};
    //obtain filenames for batches in directory
    for (const auto & entry : fs::directory_iterator(data_dir)){
        string file_str = entry.path();
        TString filename = TString(entry.path());
        if ((file_str.length() - file_str.find_last_of("/")) < 10){
            cout << entry.path() << endl;
            filenames.push_back(filename);
        }
    }
    map<int,double> pred_offsets; //keeps track of the predicted offsets
    map<int,vector<double>> entry_count; //keeps track of number of tracks fitted, sum of residuals, number of invalid tracks, for each channel
    double learning_rate = 1; //learning rate set here
    //iterate through files
    for (int i = 0; i < filenames.size();i++){
        learning_rate = 1.3 - (i*0.06); //adaptive learning rate
        ofstream predicted_offsets; //writing predicted offsets to txt file
        string pred_file = data_dir + "/pred_offsets" + to_string(i) +".txt";
        predicted_offsets.open(pred_file);
        predicted_offsets << "channel_id pred_offset" << endl;
        cout << "file: " << filenames[i] << endl; //current file
        TString filename = filenames[i];
        unique_ptr<TFile> f{TFile::Open(filename,"read")}; //open batch file
        TIter iter1(f->GetListOfKeys());
        TKey* treekey = (TKey*)iter1();
        TTree* main_tree = (TTree*) treekey->ReadObj();
        vector<int> *ch_ind = nullptr; // initialize pointers for batch addresses
        vector<double> *bat_x = nullptr;
        vector<double> *bat_y = nullptr;
        vector<double> *bat_z = nullptr;
        vector<double> *bat_hit_t = nullptr;
        vector<int> *det_id = nullptr;
        main_tree->SetBranchAddress("Batch_x",&bat_x); //set branch addresses
        main_tree->SetBranchAddress("Batch_y",&bat_y);
        main_tree->SetBranchAddress("Batch_z",&bat_z);
        main_tree->SetBranchAddress("Batch_t",&bat_hit_t);
        main_tree->SetBranchAddress("det_id",&det_id);
        main_tree->SetBranchAddress("ch_it",&ch_ind);
        int targ_ind;
        int largest_ind;
        int smallest_ind;
        //iterate through entries in a file
        for (int j = 0; j < main_tree->GetBranch("Batch_x")->GetEntries(); j++){
            main_tree->GetEntry(j);
            for (int k = 0; k < det_id->size(); k++){ // check if predicted offsets map and entry count map have an entry for each channel
                if (pred_offsets.count((*det_id)[k]) == 0){
                    pred_offsets.insert(pair<int,double>((*det_id)[k],0));
                }
                if (entry_count.count((*det_id)[k])==0){
                    entry_count.insert(pair<int,vector<double>>((*det_id)[k],{0,0,0}));
                }
                (*bat_hit_t)[k] -=  pred_offsets[(*det_id)[k]];
            }
            targ_ind = find((*det_id).begin(),(*det_id).end(),(*ch_ind)[0]) - (det_id->begin()); //find index of target channel at (*ch_ind)[0]
            double slopeintx[2] = {0};
            double slopeintz[2] = {0};
            vec_len = bat_y->size();
            lin_regress(*bat_y,*bat_x,slopeintx); //linear regression fit 
            lin_regress(*bat_y,*bat_z,slopeintz);
            vector<double> pred_x;
            vector<double> pred_z;
            vector<double> pred_dists;
            double sumfit = 0;
            double fitted = 0;
            double pred_t = 0;
            double pred_dist = 0;
            smallest_ind = distance((*bat_y).begin(),max_element((*bat_y).begin(),(*bat_y).end())); //index of channel with largest y value, set as origin for distance calculations
            //calculate distance from the hit in the channel corresponding to smallest_ind, then calculate the adjustment for the fit
            for (int k = 0; k < bat_hit_t->size(); k++){
                pred_x.push_back((*bat_y)[k]*slopeintx[0] + slopeintx[1]);
                pred_z.push_back((*bat_y)[k]*slopeintz[0] + slopeintz[1]);
                if (k != targ_ind){
                    double dist = (sqrt(pow((pred_x[k]-pred_x[smallest_ind]),2.0) + pow((pred_z[k]-pred_z[smallest_ind]),2.0) + pow(((*bat_y)[k]-(*bat_y)[smallest_ind]),2.0)));
                    double t = ((*bat_hit_t)[k]);
                    pred_dists.push_back(dist);
                    sumfit += (t - (dist/c));
                }
            }
            fitted = sumfit/(bat_hit_t->size()-1);
            pred_dist = (sqrt(pow((pred_x[targ_ind]-pred_x[smallest_ind]),2.0) + pow((pred_z[targ_ind]-pred_z[smallest_ind]),2.0) + pow(((*bat_y)[targ_ind]-(*bat_y)[smallest_ind]),2.0)));
            pred_t = (pred_dist/c) + fitted; //the predicted time from the fit
            if (abs((*bat_hit_t)[targ_ind] - pred_t) < 50){ // if the adjustment is a reasonable number
                (entry_count[(*ch_ind)[0]])[1] += (*bat_hit_t)[targ_ind] - pred_t;
            }
            else {
                (entry_count[(*ch_ind)[0]])[2]++;
            }

            // if ((*ch_ind)[0] == 1911){
            //     cout << "Entry: " << j << " ";
            //     cout << "Recorded t: " << (*bat_hit_t)[targ_ind]<< j << " ";
            //     cout << "Predicted t: " << pred_t << endl;
            //     if (j == 11985){
            //         cout << "detected" << endl;
            //     }
            // }

            //Once all 50 entries for a channel have been fitted, the offset for that channel is updated and entry_count for that channel is reset
            if ((int((entry_count[(*ch_ind)[0]])[0])+1)%50 == 0){
                // cout << (*ch_ind)[0] << endl;
                double avg_residual;
                if ((entry_count[(*ch_ind)[0]])[2] != 50){
                    avg_residual = (entry_count[(*ch_ind)[0]])[1]/(50-(entry_count[(*ch_ind)[0]])[2]);
                }
                else {
                    avg_residual = 0;
                }
                pred_offsets[(*ch_ind)[0]] += learning_rate*avg_residual;//curr 1 best -> maybe use variable learning rate!
                predicted_offsets << (*ch_ind)[0] << " " << pred_offsets[(*ch_ind)[0]] << endl;
                (entry_count[(*ch_ind)[0]])[0] = 0;
                (entry_count[(*ch_ind)[0]])[1] = 0;
                (entry_count[(*ch_ind)[0]])[2] = 0;
            }
            (entry_count[(*ch_ind)[0]])[0]++;

        }
    }
}

//Simple linear regression fit taking in two vectors and returning slope and intercept
void lin_regress(vector<double> xs,vector<double> ys, double *slopeint){
    double det = 0;
    double H_H[2][2] = {0};
    double err[2][2];
    double HTY[2] = {0};
    double det_HH;
    int i;
    for (i = 0; i < vec_len; i++){
        H_H[0][0] += xs[i]*xs[i];
        H_H[0][1] += xs[i];
        HTY[0] += xs[i]*ys[i];
        HTY[1] += ys[i];
    }
    H_H[1][0] = H_H[0][1];
    H_H[1][1] = vec_len;
    det_HH = H_H[0][0]*H_H[1][1] - H_H[0][1]*H_H[1][0];
    if (det_HH == 0){
        cout << "hmm";
    }
    else{
        err[0][0] = H_H[1][1]/det_HH;
        err[0][1] = -H_H[0][1]/det_HH;
        err[1][0] = -H_H[1][0]/det_HH;
        err[1][1] = H_H[0][0]/det_HH;
        slopeint[0] = err[0][0]*HTY[0] + err[0][1]*HTY[1];
        slopeint[1] = err[1][0]*HTY[0] + err[1][1]*HTY[1];
    }
}
