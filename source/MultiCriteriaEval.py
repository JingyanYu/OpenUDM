import pandas as pd
import numpy as np
import os


#Function: MaskedWeightedSum
def multi_criteria_eval(constraint_ras, num_attractors, attractors_tbl, cell_suit_ras, 
                      header_text,header_values, output_path, rval):
    # Read the attractors table - names and weights
    attractor_name_list, attractor_weight_list = pd.read_csv(attractors_tbl, usecols=[0, 2]).values.T
    # Normalise the weights
    sum_weight = sum(attractor_weight_list)
    normalised_weight_list = attractor_weight_list / sum_weight
    # Load the attractor layers
    attractor_layers = [np.loadtxt(os.path.join(output_path,'std_' + attractor_name_list[i]), skiprows=6) for i in range(num_attractors)]
    # Calculate the weighted sum
    summed_attractor_layer = sum(attractor_layers[i] * normalised_weight_list[i] for i in range(num_attractors))
    if rval:
        summed_attractor_layer = np.ones((header_values[1],header_values[0]))-summed_attractor_layer
    # Load the constraint layer
    constraint_layer = np.loadtxt(constraint_ras, skiprows=6)
    # Calculate the suitability layer
    suitability_layer = constraint_layer * summed_attractor_layer
    # Mask the suitability layer
    suitability_layer[constraint_layer == header_values[-1]] = header_values[-1]
    # Save the suitability layer
    with open(cell_suit_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, suitability_layer, fmt='%1.3f')
    