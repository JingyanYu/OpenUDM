import pandas as pd
import numpy as np
import os


#Function: MaskedWeightedSum
# Input:
#      bval - Boolean flag indicating whether to use binary rasters, e.g. True
#      constraint_ras - path to the constraint raster file, e.g. raster_files['constraint_ras']
#      num_attractors - number of attractors, e.g. num_attractors
#      attractors_tbl - path to the attractors table, e.g. table_files['attractors_tbl']
#      cell_suit_ras - path to the cell suitability raster file, e.g. raster_files['cell_suit_ras']
#      output_path - path to the output directory, e.g. output_path
#      rast_hdr - path to the raster header file, e.g. raster_files['rast_hdr']
#      swap_path - path to the swap directory, e.g. swap_path
#      rval - Boolean flag indicating whether to use reverse, e.g. True
# Output:
# 1. Read the first column of attribute table (csv), layer_name, into a numpy array dRasStr;
# 2. read the third column of attribute table, layer_weight, into a numpy array;
#normalize the weights by the sum of all weights
# 3. for number in num_attractors, read the raster file into a numpy array, store in a list dVec
# 4. create a 2d numpy array result with size ncols, nrows from header_value, with initial values 0; 
# the rval is True, set all elements to 1.
# 5. sum all the raster layers in dVec, weighted by dNormWgt, and store in result
# if rval is True, elements in result are subtracted from 1 by the weighted sum
# 6. Apply mask to result using constraint_ras
# for the elements where there is nodata, set corresponding elements in result to nodata value
# for the elements where there is data, set corresponding elements to constraint_ras value * result value
# 7. Write result to a raster file at path cell_suit_ras with header
def MaskedWeightedSum(bval, constraint_ras, num_attractors, attractors_tbl, cell_suit_ras, 
                      header_text,header_values, swap_path, rval):
    dRasStr, dWgt = pd.read_csv(attractors_tbl, usecols=[0, 2]).values.T
    sumWgt = sum(dWgt)
    dNormWgt = dWgt / sumWgt
    dVec = [np.loadtxt(os.path.join(swap_path, dRasStr[i]), skiprows=6) for i in range(num_attractors)]
    summed_attractor_layer = sum(dVec[i] * dNormWgt[i] for i in range(num_attractors))
    if rval:
        summed_attractor_layer = np.ones((header_values[1],header_values[0]))-summed_attractor_layer
    constraint_layer = np.loadtxt(constraint_ras, skiprows=6)
    suitability_layer = constraint_layer * summed_attractor_layer
    suitability_layer[constraint_layer == header_values[-1]] = header_values[-1]
    with open(cell_suit_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, suitability_layer, fmt='%1.3f')
    