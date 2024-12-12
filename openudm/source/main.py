import os
import pandas as pd
import numpy as np
import source.RasterToolkit as rt
import source.MultiCriteriaEval as mce
import source.DevZones as dz
import source.CellularModel as cm

def main(path_to_data, path_to_output):
    
    # Set parameters, read rasters and tables, print number of zones, constraints and attractors, and read raster header
    control_params = set_control_params()
    raster_files = generate_raster_filepaths(path_to_data, path_to_output)
    table_files = generate_table_filepaths(path_to_data, path_to_output)
    parameters = import_parameters(table_files['parameters_tbl'])
    num_zones, num_constraints, num_attractors = print_zones_constraints_attractors(table_files)
    lines, header_values = read_raster_header(raster_files['zone_id_ras'])

    # Standardize attractor layers  
    standardize_attractor_layers(num_attractors, table_files, path_to_data, path_to_output, lines, header_values[-1])

    # Generate the combined constraint layer and the current development rasters   
    rt.create_constraint_ras_and_current_dev_ras(path_to_data, header_values, lines, raster_files['constraint_ras'], 
                                                 raster_files['current_dev_ras'], raster_files['zone_id_ras'],
                                                 table_files['constraints_tbl'], num_constraints, parameters['coverage_threshold'])
    
    # Multi-criteria evaluation
    # Set rval based upon boolean input (reverse) - it can then be tested in place as function argument
    rval = 1 if control_params['attractor_reverse'] else 0
    # Generate suitability raster
    mce.multi_criteria_eval(raster_files['constraint_ras'], num_attractors, table_files['attractors_tbl'], raster_files['cell_suit_ras'], 
                      lines[:6],header_values, path_to_output, rval)
    print("Cell suitability raster generated.")

    # Generate zonal development patches ID raster
    dz.find_zone_dev_patches(parameters['minimum_development_area'], raster_files['constraint_ras'], num_zones,
                          raster_files['dev_patch_id_ras'], lines[:6], header_values, raster_files['zone_id_ras'])
    # Compute average patch suitability   
    dz.patch_avg_suitability(raster_files['dev_patch_id_ras'], raster_files['cell_suit_ras'], raster_files['dev_patch_suit_ras'],
                             lines[:6], header_values)
    print("Average patch suitability computed.")

    # Run the cellular model
    new_development = cm.run_model(num_zones,parameters, table_files, raster_files,header_values)
    print("New development areas generated.")
    return new_development


# Function to set control parameters
def set_control_params():
    return {
        'attractor_reverse': 0,
            }

# Function to generate raster filepaths
def generate_raster_filepaths(path_to_data, path_to_output):
    raster_files = {
        'rast_hdr': 'rasterHeader.hdr',
        'zone_id_ras': 'zone_identity.asc',
        'constraint_ras': 'constraint.asc',
        'current_dev_ras': 'current_development.asc',
        'cell_suit_ras': 'out_cell_suit.asc',
        'dev_patch_id_ras': 'dev_patch_id.asc',
        'dev_patch_suit_ras': 'dev_patch_suit.asc',
        'cell_dev_output_ras': 'out_cell_dev.asc',
        'density_ras': 'density.asc',
        'cell_dph_ras': 'out_cell_dph.asc',
        'cell_pph_ras': 'out_cell_pph.asc'
    }

    for key in raster_files:
        if key in ['rast_hdr', 'zone_id_ras', 'density_ras']:
            raster_files[key] = os.path.join(path_to_data, raster_files[key])
        else:
            raster_files[key] = os.path.join(path_to_output, raster_files[key])
    return raster_files

# Function to generate table filepaths
def generate_table_filepaths(path_to_data, path_to_output):
    table_files = {
        'constraints_tbl': 'constraints.csv',
        'attractors_tbl': 'attractors.csv',
        'population_tbl': 'population.csv',
        'dwellings_tbl': 'dwellings.csv',
        'parameters_tbl': 'parameters.csv',
        'zone_diagnostic_tbl': 'zone_diagnostic.csv',
        'density_tbl': 'density.csv',
        'metadata_tbl': 'out_cell_metadata.csv'
    }

    for key in table_files:
        if key in ['zone_diagnostic_tbl', 'metadata_tbl']:
            table_files[key] = os.path.join(path_to_output, table_files[key])
        else:
            table_files[key] = os.path.join(path_to_data, table_files[key])
    return table_files

def import_parameters(parameters_tbl):
    df = pd.read_csv(parameters_tbl)
    parameters = df.to_dict(orient='records')[0]
    print("Parameters file imported.")
    return parameters

def print_zones_constraints_attractors(table_files):
    num_zones = len(pd.read_csv(table_files['population_tbl'])) 
    num_constraints = len(pd.read_csv(table_files['constraints_tbl'])) 
    num_attractors = len(pd.read_csv(table_files['attractors_tbl'])) 
    print(f'Number of zones: {num_zones}')
    print(f'Number of constraints: {num_constraints}')
    print(f'Number of attractors: {num_attractors}')
    return num_zones, num_constraints, num_attractors

def read_raster_header(zone_id_ras):
    with open(zone_id_ras, 'r') as f:
        lines = f.readlines()
        ncols = int(lines[0].split('ncols')[1].split('\n')[0])
        nrows = int(lines[1].split('nrows')[1].split('\n')[0])
        xllcorner = float(lines[2].split('xllcorner')[1].split('\n')[0])
        yllcorner = float(lines[3].split('yllcorner')[1].split('\n')[0])
        cellsize = float(lines[4].split('cellsize')[1].split('\n')[0])
        nodatavalue = float(lines[5].split('NODATA_value')[1].split('\n')[0])
        header_values = [ncols, nrows, xllcorner, yllcorner, cellsize, nodatavalue]
    return lines, header_values


def standardize_attractor_layers(num_attractors, table_files, path_to_data, path_to_output, lines, nodatavalue):
    attractorflag_list = pd.read_csv(table_files['attractors_tbl'])[['layer_name','reverse_polarity_flag']].values.tolist()
    mask_layer = np.loadtxt(os.path.join(path_to_data, 'zone_identity.asc'), skiprows=6)

    for i in range(num_attractors):
        attractor_path = os.path.join(path_to_data, attractorflag_list[i][0])
        rev_attractor_flag = attractorflag_list[i][1]
        attractor_layer = np.loadtxt(attractor_path, skiprows=6)
        if rev_attractor_flag == 0:
            standarised_attractor_layer = rt.Standardise(attractor_layer, mask_layer, nodatavalue)
        elif rev_attractor_flag == 1:
            standarised_attractor_layer = rt.RevPolarityStandardise(attractor_layer, mask_layer, nodatavalue)
        attractor_output_path = os.path.join(path_to_output, 'std_' + attractorflag_list[i][0])
        with open(attractor_output_path, 'w') as f:
            f.write(''.join(lines[:6]))
            np.savetxt(f, standarised_attractor_layer, fmt='%1.3f')