import numpy as np
import pandas as pd
import os

#Function Standardise, which standardises the values of a matrix to a range of 0 to 1
#Input: matrix - a 2D numpy array; mask - a 2D numpy array
#Output: matrix - a 2D numpy array
def Standardise(ras_2darray, mask_2darray,novalue_data):
    #standardise the values of matrix to a range of 0 to 1
    valid_data = ras_2darray[mask_2darray != novalue_data]
    min_val = np.min(valid_data)
    max_val = np.max(valid_data)
    standardised_array = (ras_2darray - min_val) / (max_val - min_val)
    return standardised_array

#Function RevPolarityStandardise
def RevPolarityStandardise(ras_2darray, mask_2darray,novalue_data):
    #standardise the values of matrix to a range of 0 to 1
    valid_data = ras_2darray[mask_2darray != novalue_data]
    min_val = np.min(valid_data)
    max_val = np.max(valid_data)
    standardised_array = (max_val - ras_2darray) / (max_val - min_val)
    return standardised_array

# Function RasteriseAreaThresholds
# Input: 
#      header_values - header values of the raster file, [ncols, nrows, xllcorner, yllcorner, cellsize, nodatavalue]
#      header_text - header text of the raster file, lines[:6]
#      constraint_ras - path to the constraint raster file, e.g. raster_files['constraint_ras']
#      current_dev_ras - path to the current development raster file, e.g. raster_files['current_dev_ras']
#      constraints_tbl - path to the constraints table, e.g. table_files['constraints_tbl']
#      coverage_threshold - parameter from the parameters table, e.g. parameters['coverage_threshold']
# Output: None
# 1. Read from the constraints table: layer_name, current_development_flag, and layer_threshold into variables
#    layerRasStr, devFlag, layerThreshold
# 2. Create a list inputCoverage containing 2D numpy arrays of the raster files named in layerRasStr
# 3. Calculate summedThresholdArea = (coverage_threshold / 100) * (cellsize^2); cellsize is in the header file
# 4. Calculate individual constraint threshold areas: layerThresholdArea = layerThreshold / 100 * cellsize^2
# 5. Create a 2D numpy array summedLayerArea as the sum of all layers in inputCoverage
#    Create a 2D numpy array outputCoverage of the same size as summedLayerArea, filled with 1s
#    Assign 0 to elements in outputCoverage where input layer element value > layerThresholdArea, indicating 0 suitability
#    Assign 0 to elements in outputCoverage where summedLayerArea > summedThresholdArea, indicating 0 suitability
# 6. Write outputCoverage to a raster file with header
# 7. Create a 2D numpy array currentDev of the same size as summedLayerArea, filled with zeros
#    For layers in devFlag with value 1, assign 1 to elements in currentDev where layer value > corresponding layerThresholdArea
def RasteriseAreaThresholds(swap_path, header_values, header_text, constraint_ras, current_dev_ras, 
                            constraints_tbl, num_constraints, coverage_threshold):
    layerRasStr = pd.read_csv(constraints_tbl, usecols=[0]).values.flatten()
    devFlag = pd.read_csv(constraints_tbl, usecols=[1]).values.flatten()
    layerThreshold = pd.read_csv(constraints_tbl, usecols=[2]).values.flatten()
    inputCoverage = [np.loadtxt(os.path.join(swap_path, layerRasStr[i]), skiprows=6) for i in range(num_constraints)]
    summedThresholdArea = (coverage_threshold / 100) * (header_values[4] ** 2)
    layerThresholdArea = [layerThreshold[i] / 100 * header_values[4] ** 2 for i in range(num_constraints)]
    summedLayerArea = sum(inputCoverage)
    outputCoverage = np.ones(summedLayerArea.shape)
    for i in range(num_constraints):
        outputCoverage[inputCoverage[i] > layerThresholdArea[i]] = 0
    outputCoverage[summedLayerArea > summedThresholdArea] = 0
    with open(constraint_ras, 'w') as f:
            f.write(''.join(header_text))
            np.savetxt(f, outputCoverage, fmt='%1.0f')
    currentDev = np.zeros(summedLayerArea.shape)
    for i in range(num_constraints):
        if devFlag[i] == 1:
            currentDev[inputCoverage[i] > layerThresholdArea[i]] = 1
    with open(current_dev_ras, 'w') as f:
            f.write(''.join(header_text))
            np.savetxt(f, currentDev, fmt='%1.0f')


#Function IRasterSetNoDataToRef: set the elements in a raster to nodata value where the reference raster is nodata
def IRasterSetNoDataToRef(constraint_ras,header_text,mask_layer,header_values):
    ras = np.loadtxt(constraint_ras, skiprows=6)
    ras[mask_layer == header_values[-1]] = header_values[-1]
    with open(constraint_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, ras, fmt='%1.0f')