parameters = {}


# Run parameters
parameters["debug"]=False                   # Show debug info
parameters["debug_tracker"]=False
parameters["debug_vertexer"]=False
parameters["print_n"]=1000
parameters["start_event"]=0                 # 0-based index
parameters["end_event"]=1000000
parameters["seed"]=1                        # Seed for random number generator (used for scintillator efficiency)
parameters["detector_efficiency"]=1         # Scintillator efficiency, any number between 0-1, 1 is 100%

# Global parameters:
parameters["multiple_scattering_p"]= 500            # [MeV/c] momentum of multiple scattering, 
parameters["multiple_scattering_length"]=0.06823501107481977 # [1] material thickness in the unit of attenuation length = thickness/attenuation_length


# Track parameters
parameters["cut_track_SeedSpeed"]=1                 # in the unit of c. Limit the maximum speed formed by the seed.
parameters["cut_track_HitAddChi2"]=12               # Only used when method is "greedy"
parameters["cut_track_HitDropChi2"]=7               # Set to -1 to turn off
parameters["cut_track_HitProjectionSigma"]=7        # Number of sigmas
parameters["cut_track_TrackChi2Reduced"]=3          # Only use this for track with 3 hits
parameters["cut_track_TrackChi2Prob"]=0.9           # Chi-square probablity (calculated from chi2_cdf(x, DOF))
parameters["cut_track_TrackNHitsMin"]=3             # Minimum number of hits per track
parameters["cut_track_TrackSpeed"] = [25,35]        # [cm/ns], [speed_low, speed_high]. 30 is the speed of light
parameters["fit_track_MultipleScattering"]=True
parameters["cut_track_MultipleScatteringFind"]=False
parameters["fit_track_Method"]="backward"           # choose one of {"backward", "forward", "forward-seed", "least-square", "least-square-ana"}

# Vertex parameters
parameters["cut_vertex_SeedDist"]=300
parameters["cut_vertex_SeedChi2"]=25
parameters["cut_vertex_TrackAddDist"]=300
parameters["cut_vertex_TrackAddChi2"]=25
parameters["cut_vertex_TrackDropChi2"]=15
parameters["cut_vertex_VertexChi2ReducedAdd"]=10
parameters["cut_vertex_VertexChi2Reduced"]=7