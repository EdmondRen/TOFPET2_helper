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
#include <set>

#include "TFile.h"
#include "TTree.h"
#include "Riostream.h"
#include "TROOT.h"
#include "TH1F.h"
#include "TNtuple.h"
#include "TKey.h"
#include "TIterator.h"
#include "TCanvas.h"
#include "TLegend.h"

//VELOCITY ITERATOR - USE TO CHECK RAW DATA

using namespace std;
namespace fs = filesystem;
using recursive_directory_iterator = filesystem::recursive_directory_iterator;

double rand_gen(double low, double up);

int main(int argc, char *argv[]) {
    //data_dir-> raw data, output_dir-> where histogram should be stored
    string data_dir = string(argv[1]);
    string output_dir = string(argv[2]);
    // string data_dir = "full_data5"; //Folder containing raw data
    int valid_entries = 0;
    vector<TString> filenames = {};
    for (const auto & entry : recursive_directory_iterator(data_dir)){ //Store filenames, generate filenames for 'recorded' files
        //cout << entry.path() << endl;
        TString filename = TString(entry.path());
        string file_str = entry.path();
        if(file_str.substr(file_str.find_last_of(".")+1)=="root"){
            filenames.push_back(filename);
        }
    }
    TString histo_filename(output_dir+"/velocity_hist.root"); //Generate histogram to analyze results
    unique_ptr<TFile> h{TFile::Open(histo_filename,"recreate")};
    double velocity;
    TH1D *velo_hist = new TH1D("velocities","velocity",200,25,33); //150 bins, min 27 max 33

    // for (int i = 0; i < filenames.size();i++){
    for (int i = 0; i <99 ;i++){ 
        int track_num = 0;
        TString filename = filenames[i];
        TFile f(filename);
        TIter iter1(f.GetListOfKeys());
        TKey* treekey = (TKey*)iter1();
        TTree* main_tree = (TTree*) treekey->ReadObj();
        cout << "Filename: " << filename << endl;
        printf("Main Tree Name: %s\n",main_tree->GetName());
        // main_tree->GetListOfBranches()->Print();
        string branch_names[54];
        vector<double> *hit_x = nullptr;
        vector<double> *hit_y = nullptr;
        vector<double> *hit_z = nullptr;
        vector<double> *hit_time = nullptr;
        vector<double> *hit_particle_energy = nullptr;
        vector<double> *digi_x = nullptr;
        vector<double> *digi_y = nullptr;
        vector<double> *digi_z = nullptr;
        vector<double> *digi_hit_t = nullptr;
        vector<int> *det_id = nullptr;
        vector<int> *pdg_id = nullptr;
        // list<int> id_list;
        for (int j = 0; j < main_tree->GetListOfBranches()->GetEntries(); j++){
            branch_names[j] = main_tree->GetListOfBranches()->At(j)->GetName();
            // cout << (branch_names[i]) << endl;
        }
        main_tree->SetBranchAddress("Hit_x", &hit_x);
        main_tree->SetBranchAddress("Hit_y", &hit_y);
        main_tree->SetBranchAddress("Hit_z", &hit_z);
        main_tree->SetBranchAddress("Digi_x", &digi_x);
        main_tree->SetBranchAddress("Digi_z", &digi_z);
        main_tree->SetBranchAddress("Hit_time", &hit_time);
        main_tree->SetBranchAddress("Hit_particleEnergy", &hit_particle_energy);
        main_tree->SetBranchAddress("Digi_y", &digi_y);
        main_tree->SetBranchAddress("Digi_time", &digi_hit_t);
        main_tree->SetBranchAddress("Digi_det_id", &det_id);
        main_tree->SetBranchAddress("Digi_pdg_id", &pdg_id);
        for (int k=0; k < main_tree->GetBranch(branch_names[0].c_str())->GetEntries(); k++){
            main_tree->GetEntry(k);
         
            //Same selection criteria for tracks as batch_generator_final.cpp
            if ((digi_hit_t->size() < 7)&&(digi_hit_t->size() > 4)&&((count((*pdg_id).begin(),(*pdg_id).end(),13)==(*pdg_id).size())||(count((*pdg_id).begin(),(*pdg_id).end(),-13)==(*pdg_id).size()))){
                std::set<float> unique(digi_y->begin(),digi_y->end());
                if (unique.size() == digi_y->size()){
                    //Modify depending on what you want to keep track of
                    int ind_1 = (int) rand_gen(1,digi_x->size()+1);
                    // int ind_2 = (int) rand_gen(0,hit_x->size()+1);
                    // int ind_1 = distance((digi_hit_t)->begin(),max_element((digi_hit_t)->begin(),(digi_hit_t)->end()));
                    int ind_2 = 0;
                    // while (ind_1 == ind_2){
                    //     ind_1 = (int) rand_gen(0,hit_x->size()+1);
                    //     ind_2 = (int) rand_gen(0,hit_x->size()+1);
                    // }
                    if ((*hit_time)[ind_1] != (*hit_time)[ind_2]){
                        vector<double> pos_1 = {(*hit_x)[ind_1],(*hit_y)[ind_1],(*hit_z)[ind_1],(*hit_time)[ind_1]};
                        vector<double> pos_2 = {(*hit_x)[ind_2],(*hit_y)[ind_2],(*hit_z)[ind_2],(*hit_time)[ind_2]};
                        double dist = (sqrt(pow(pos_1[0]-pos_2[0],2)+pow(pos_1[1]-pos_2[1],2)+pow(pos_1[2]-pos_2[2],2)));
                        (velocity) = abs(dist/(pos_1[3]-pos_2[3]));
                        velo_hist->Fill(velocity);
			            //cout << velocity << endl;
                    }
                    // (velocity) = 29.9792458*sqrt(pow((*hit_particle_energy)[ind_1],2) - pow(105,2))/(*hit_particle_energy)[ind_1];
                    // velo_hist->Fill(velocity);
                    track_num++;
                }
            }
            //main_tree->GetBranch(branch_names[0].c_str())->GetEntries()-1
        }
        // cout << "id_list size " << id_list.size() << endl;
        // cout << "true_offsets size " << true_offsets.size() << endl;
        // list<int>::iterator it;
        // for (it = id_list.begin(); it != id_list.end(); it++){
        //     cout << '\n' << *it;
        // }

        main_tree->ResetBranchAddresses();
        f.Close();
    }

    //Generate histogram
    auto canvas_hist = new TCanvas();
    velo_hist->Draw();
    canvas_hist->Draw();
    h->Write();
    h->Close();
    //To view, in terminal do root, TBrowser b, then search for histogram file and open it

    // for (auto it = ch_tracks.cbegin(); it != ch_tracks.cend(); ++it){
    //     cout << "channel: " << it->first << ", tracks: [";
    //     for (auto it2 = (it->second).begin(); it2 != (it->second).end(); it2++){
    //         cout << "<" << it2->first << "," << it2->second << ">";
    //     }
    //     cout << "]" << endl;
    // }
    // for (auto it = true_offsets.cbegin(); it != true_offsets.cend(); ++it){
    //     cout << "channel: " << it->first << ", offset: " << it->second << endl;
    // }

    // Use modulus to loop around vector 

    unsigned seed = chrono::system_clock::now().time_since_epoch().count();
    mt19937 gen(seed);

    // for(std::map<int,vector<pair<int,int>>>::iterator it = ch_tracks.begin(); it != ch_tracks.end(); ++it) {
    //     cout << "Key: " << it->first << endl;
    // }

    // cout << "channel: 616202, shuffled tracks: [";
    // for (int k=0;k < ch_tracks[616202].size();k++){
    //     cout << "<" << ch_tracks[616202][k].first << ","<< ch_tracks[616202][k].second << ">";
    // }
    // cout << "]" << endl;
    
    // for (map<int,vector<pair<int,int>>>::iterator it = ch_tracks.begin(); it != ch_tracks.end(); ++it){
    //     cout << it->first << endl;
    // }

}

//Random number generator between low and up
double rand_gen(double low, double up){
    random_device dev;
    mt19937 gen(dev());
    uniform_real_distribution<> dist6(low,up);
    return dist6(gen);
}
