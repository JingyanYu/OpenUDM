import numpy as np
import pandas as pd
import os

############################################################################################################
# Functions related find_zone_dev_patches
############################################################################################################
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

############################################################################################################
#Function create_constraint_ras_and_current_dev_ras: Create constraint raster and current development raster
############################################################################################################
def create_constraint_ras_and_current_dev_ras(path_to_data, header_values, header_text, constraint_ras, current_dev_ras, zone_id_ras,
                                              constraints_tbl, num_constraints, coverage_threshold):
    # Read Constraint layers
    current_development_flag_list, layer_threshold_list, constraint_layers = read_constraint_layers(constraints_tbl, path_to_data, num_constraints)
    
    # Calculate Threshold Areas
    constraint_threshold_area, layer_threshold_area_list = calculate_threshold_areas(header_values, coverage_threshold, layer_threshold_list, num_constraints)
    
    # Generate Binary Constraint Layer
    output_constraint_layer = generate_binary_constraint_layer(constraint_layers, layer_threshold_area_list, constraint_threshold_area, num_constraints)
    # Mask NoData Value
    zone_id_ras_data = np.loadtxt(zone_id_ras, skiprows=6)
    output_constraint_layer = mask_nodatavalue(output_constraint_layer, zone_id_ras_data, header_values)
    # Write Binary Constraint Layer to File
    write_raster_to_file(output_constraint_layer, constraint_ras, header_text[:6])
    
    # Create Current Development Layer
    current_dev_layer = create_current_development_layer(constraint_layers, current_development_flag_list, layer_threshold_area_list, zone_id_ras_data, header_values, num_constraints)
    # Write Current Development Layer to File
    write_raster_to_file(current_dev_layer, current_dev_ras, header_text[:6])

def read_constraint_layers(constraints_tbl, path_to_data, num_constraints):
    layer_name_list, current_development_flag_list, layer_threshold_list = pd.read_csv(constraints_tbl, usecols=[0, 1, 2]).values.T
    constraint_layers = [np.loadtxt(os.path.join(path_to_data, layer_name_list[i]), skiprows=6) for i in range(num_constraints)]
    return current_development_flag_list, layer_threshold_list, constraint_layers

def calculate_threshold_areas(header_values, coverage_threshold, layer_threshold_list, num_constraints):
    constraint_threshold_area = (coverage_threshold / 100) * (header_values[4] ** 2)
    layer_threshold_area_list = [layer_threshold_list[i] / 100 * header_values[4] ** 2 for i in range(num_constraints)]
    return constraint_threshold_area, layer_threshold_area_list

def generate_binary_constraint_layer(constraint_layers, layer_threshold_area_list, constraint_threshold_area, num_constraints):
    summed_value_all_layers = sum(constraint_layers)
    output_constraint_layer = np.ones(summed_value_all_layers.shape)
    for i in range(num_constraints):
        output_constraint_layer[constraint_layers[i] > layer_threshold_area_list[i]] = 0
    output_constraint_layer[summed_value_all_layers > constraint_threshold_area] = 0
    return output_constraint_layer

def write_raster_to_file(raster, file_path, header_text, fmt='%d'):
    with open(file_path, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, raster, fmt=fmt)

def create_current_development_layer(constraint_layers, current_development_flag_list, layer_threshold_area_list, zone_id_ras, header_values, num_constraints):
    current_dev_layer = np.zeros(constraint_layers[0].shape)
    for i in range(num_constraints):
        if current_development_flag_list[i] == 1:
            current_dev_layer[constraint_layers[i] > layer_threshold_area_list[i]] = 1
    current_dev_layer[zone_id_ras == header_values[-1]] = header_values[-1]
    return current_dev_layer

def mask_nodatavalue(ras,mask_layer,header_values):
    ras[mask_layer == header_values[-1]] = header_values[-1]
    return ras