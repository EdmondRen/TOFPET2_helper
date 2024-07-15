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

//FINAL BATCH GENERATOR - USE THIS ONE

using namespace std;
namespace fs = filesystem;
using recursive_directory_iterator = filesystem::recursive_directory_iterator;

double rand_gen(double low, double up);

int main(int argc, char *argv[]) {
    //data_dir -> where the raw data is, recorded_dir -> where the new data should be
    string data_dir = string(argv[1]);
    string recorded_dir = string(argv[2]);
    // string data_dir = "test_data5"; //Directory for raw data
    int valid_entries = 0;
    map<int,vector<pair<int,int>>> ch_tracks;
    map<int,double> true_offsets;
    vector<TString> filenames = {};
    vector<TString> rec_filenames = {};
    ofstream truth_offsets;
    for (const auto & entry : recursive_directory_iterator(data_dir)){ //Store filenames, generate filenames for 'recorded' files
        cout << entry.path() << endl;
        TString filename = TString(entry.path());
        string file_str = entry.path();
        if(file_str.substr(file_str.find_last_of(".")+1)=="root"){
            string cur_file_directory = file_str.substr(0,file_str.find_last_of("/"));
            string super_dir = cur_file_directory.substr(0,cur_file_directory.find_last_of("/"));
            int len_rec_file_name = cur_file_directory.find_last_of("/")-super_dir.find_last_of("/");
            string rec_file_start = file_str.substr(super_dir.find_last_of("/")+1,len_rec_file_name-1);
            TString rec_filename(recorded_dir + "/rec_" + rec_file_start + ".root");
            cout << rec_filename << endl;
            filenames.push_back(filename);
            rec_filenames.push_back(rec_filename);
        }
    }
    truth_offsets.open(recorded_dir + "/truth_offsets.txt"); //Write true offsets into a text file.
    truth_offsets << "channel_id true_offset" << endl;
    for (int i = 0; i < filenames.size();i++){ //Iterate over raw data files
        int track_num = 0;
        TString filename = filenames[i];
        TString rec_filename = rec_filenames[i];
        TFile f(filename);
        TIter iter1(f.GetListOfKeys());
        TKey* treekey = (TKey*)iter1();
        TTree* main_tree = (TTree*) treekey->ReadObj();
        TFile g(rec_filename,"recreate"); //Make new file for recorded coordinates files
        TTree* rec_tree = new TTree("Recorded","Recorded Coordinates");
        cout << "Filename: " << filename << endl;
        printf("Main Tree Name: %s\n",main_tree->GetName());
        printf("Recorded Tree Name: %s\n",rec_tree->GetName());
        // main_tree->GetListOfBranches()->Print();
        string branch_names[54];
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
        main_tree->SetBranchAddress("Digi_x", &digi_x); //Set branch addresses
        main_tree->SetBranchAddress("Digi_y", &digi_y);
        main_tree->SetBranchAddress("Digi_z", &digi_z);
        main_tree->SetBranchAddress("Digi_time", &digi_hit_t);
        main_tree->SetBranchAddress("Digi_det_id", &det_id);
        main_tree->SetBranchAddress("Digi_pdg_id", &pdg_id);
        rec_tree->Branch("Digi_x", &digi_x);
        rec_tree->Branch("Digi_y", &digi_y);
        rec_tree->Branch("Digi_z", &digi_z);
        rec_tree->Branch("Digi_time", &digi_hit_t);
        rec_tree->Branch("Digi_det_id", &det_id);
        for (int k=0; k < main_tree->GetBranch(branch_names[0].c_str())->GetEntries(); k++){
            main_tree->GetEntry(k);
            for (int j=0; j < det_id->size(); j++){ //Generate true offsets
                // id_list.push_back((*det_id)[j]);
                if (true_offsets.count((*det_id)[j]) == 0){
                    true_offsets[(*det_id)[j]] = rand_gen(-9,9);
                    truth_offsets << (*det_id)[j] << " " << true_offsets[(*det_id)[j]] << endl;
                }
            }
  
            //SELECTION CRITERIA SET HERE
            if ((digi_hit_t->size() < 7)&&(digi_hit_t->size() > 3)&&((count((*pdg_id).begin(),(*pdg_id).end(),13)==(*pdg_id).size())||(count((*pdg_id).begin(),(*pdg_id).end(),-13)==(*pdg_id).size()))){
                std::set<float> unique(digi_y->begin(),digi_y->end());
                if (unique.size() == digi_y->size()){ //Checking if track has unique y values for each hit
                    for (int l=0; l < digi_hit_t->size(); l++){
                        int ch_id = (*det_id)[l]; //target channel
                        pair<int,int> save_pair = {i,track_num}; //recording the file and entry number in recorded file
                        (*digi_hit_t)[l] += true_offsets[(*det_id)[l]]; //adjusting digitized t for hit according to offset values 
                        if (ch_tracks.count((*det_id)[l]) == 0){ //checking if channel already has entry in ch_tracks
                            ch_tracks.insert(pair<int,vector<pair<int,int>>>(ch_id,vector<pair<int,int>>()));
                            ch_tracks[(ch_id)].push_back(save_pair);
                        }
                        else {
                            ch_tracks[(ch_id)].push_back(save_pair);
                        }
                    }
                    track_num++;
                    rec_tree->Fill();
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
        g.Write();
        g.Close();
        f.Close();
    }
    truth_offsets.close();

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

    //Shuffling function for ch_tracks, to randomly sample tracks
    unsigned seed = chrono::system_clock::now().time_since_epoch().count();
    mt19937 gen(seed);
    for (map<int,vector<pair<int,int>>>::iterator it = ch_tracks.begin(); it != ch_tracks.end(); ++it){
        vector<pair<int,int>> shuffled;
        copy((it->second).begin(),(it->second).end(),back_inserter(shuffled));
        shuffle(shuffled.begin(),shuffled.end(),gen);
        // cout << it->first << endl;
        map<int,vector<pair<int,int>>>::iterator it3 = ch_tracks.find(it->first);
        it->second = shuffled;
    }
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

    int cur_file_ind;
    int start_ind = 0;
    int end_ind = 50;
    for (int i=0; i<20;i++){
        //Shuffling
        unsigned seed = chrono::system_clock::now().time_since_epoch().count();
        mt19937 gen(seed);
        for (map<int,vector<pair<int,int>>>::iterator it = ch_tracks.begin(); it != ch_tracks.end(); ++it){
            vector<pair<int,int>> shuffled;
            copy((it->second).begin(),(it->second).end(),back_inserter(shuffled));
            shuffle(shuffled.begin(),shuffled.end(),gen);
            // cout << it->first << endl;
            map<int,vector<pair<int,int>>>::iterator it3 = ch_tracks.find(it->first);
            it->second = shuffled;
        }
        start_ind = 0 + (i*50);
        end_ind = 50 + (i*50);
        TString bat_filename(recorded_dir + "/" + to_string(i) + ".root"); //Batch filename
        vector<int> *ch_ind = nullptr; //Initialize pointers
        vector<double> *bat_x = nullptr;
        vector<double> *bat_y = nullptr;
        vector<double> *bat_z = nullptr;
        vector<double> *bat_hit_t = nullptr;
        vector<int> *det_id = nullptr;
        unique_ptr<TFile> h{TFile::Open(bat_filename,"recreate")}; //Generate new file for batch
        TTree batch_tree = TTree("batch_tree","tracks to batch");
        batch_tree.Branch("ch_it",&ch_ind);
        batch_tree.Branch("Batch_x",&bat_x);
        batch_tree.Branch("Batch_y",&bat_y);
        batch_tree.Branch("Batch_z",&bat_z);
        batch_tree.Branch("Batch_t",&bat_hit_t);
        batch_tree.Branch("det_id",&det_id);

        vector<vector<int>> bat_entrylist = {};
        //Generate list of entries for a batch
        for (map<int,vector<pair<int,int>>>::iterator it = ch_tracks.begin(); it != ch_tracks.end(); ++it){
            (*ch_ind) = {it->first};
            for (int chan = start_ind; chan < end_ind; chan++){
                vector<int> identifier{(*ch_ind)};
                identifier.push_back(((it->second).begin()+(chan % (it->second).size()))->first); 
                identifier.push_back(((it->second).begin()+(chan % (it->second).size()))->second);
                bat_entrylist.push_back(identifier);
            }
        }
        sort(bat_entrylist.begin(),bat_entrylist.end(),[](const auto& a,const auto& b){return (a[1])<(b[1]);}); //Sort list to reduce I/O required?
        map<int,int> entrycount;
        for (auto v : bat_entrylist){
            if (entrycount.count(v[1]) == 0){
                entrycount[v[1]] = 0;
            }
            entrycount[v[1]] += 1;
        }
        //Fill batch file with entries
        int bat_entry_count = 0;
        for (map<int,int>::iterator it = entrycount.begin(); it != entrycount.end(); it++){
            int fileind = it->first;
            int number_of_entries = it->second;
            TString rec_filename = rec_filenames[fileind];
            unique_ptr<TFile> f{TFile::Open(rec_filename,"read")};
            TIter iter1(f->GetListOfKeys());
            TKey* treekey = (TKey*)iter1();
            TTree* main_tree = (TTree*) treekey->ReadObj();
            main_tree->SetBranchAddress("Digi_x", &bat_x);
            main_tree->SetBranchAddress("Digi_y", &bat_y);
            main_tree->SetBranchAddress("Digi_z", &bat_z);
            main_tree->SetBranchAddress("Digi_time", &bat_hit_t);
            main_tree->SetBranchAddress("Digi_det_id", &det_id);
            for (int p = 0; p < number_of_entries;p++){
                vector<int> bat_vec = bat_entrylist[bat_entry_count];
                (*ch_ind) = {bat_vec[0]};
                main_tree->GetEntry(bat_vec[2]);
                batch_tree.Fill();
                bat_entry_count++;
            }
            f->Close();
        }

        // for (map<int,vector<pair<int,int>>>::iterator it = ch_tracks.begin(); it != ch_tracks.end(); ++it){
        //     cur_file_ind = 0;
        //     TString rec_filename = rec_filenames[cur_file_ind];
        //     // cout << rec_filename << endl;
        //     (*ch_ind) = {it->first};
        //     vector<pair<int,int>> temp = {};
        //     for (int chan = start_ind; chan < end_ind; chan++){
        //         pair<int,int> te = make_pair(((it->second).begin()+(chan % (it->second).size()))->first,((it->second).begin()+(chan % (it->second).size()))->second);
        //         temp.push_back(te);
        //     }
        //     for (auto it2 = temp.begin(); it2 != temp.end(); it2++){
        //         cur_file_ind = it2->first;
        //         rec_filename = rec_filenames[cur_file_ind];
        //         unique_ptr<TFile> f{TFile::Open(rec_filename,"read")};
        //         TIter iter1(f->GetListOfKeys());
        //         TKey* treekey = (TKey*)iter1();
        //         TTree* main_tree = (TTree*) treekey->ReadObj();
        //         main_tree->SetBranchAddress("Digi_x", &bat_x);
        //         main_tree->SetBranchAddress("Digi_y", &bat_y);
        //         main_tree->SetBranchAddress("Digi_z", &bat_z);
        //         main_tree->SetBranchAddress("Digi_time", &bat_hit_t);
        //         main_tree->SetBranchAddress("Digi_det_id", &det_id);
        //         main_tree->GetEntry(it2->second);
        //         batch_tree.Fill();
        //         f->Close();
        //     }
        // }
        h->Write();
        h->Close();
    }
}

//Generating random number in a range
double rand_gen(double low, double up){
    random_device dev;
    mt19937 gen(dev());
    uniform_real_distribution<> dist6(low,up);
    return dist6(gen);
}