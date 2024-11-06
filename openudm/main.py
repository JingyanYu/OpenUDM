import os
import pandas as pd
import numpy as np
import RasterToolkit as rt
import MultiCriteriaEval as mce

def main(swap_path, output_path):
    # HARDCODED CONTROL PARAMETERS - NOT NEEDED BY USER
    control_params = {
        'bin_ras': 0,
        'unlog_ras': 0,
        'is_driven': 0,
        'attractor_reverse': 0,
        'moore': 0,
        'zonal_density': 0
    }

    # RASTER HEADER AND HARDCODED NAMES
    raster_files = {
        'rast_hdr': 'rasterHeader.hdr',
        'zone_id_ras': 'zone_identity.asc',
        'constraint_ras': 'constraint.asc',
        'current_dev_ras': 'current_development.asc',
        'cell_suit_ras': 'out_cell_suit.asc',
        'dev_area_id_ras': 'dev_area_id.asc',
        'dev_area_suit_ras': 'dev_area_suit.asc',
        'cell_dev_output_ras': 'out_cell_dev.asc',
        'density_ras': 'density.asc',
        'cell_dph_ras': 'out_cell_dph.asc',
        'cell_pph_ras': 'out_cell_pph.asc'
    }

    raster_files['rast_hdr'] = os.path.join(swap_path, raster_files['rast_hdr'])
    raster_files['zone_id_ras'] = os.path.join(swap_path, raster_files['zone_id_ras'])

    for key in raster_files:
        if key not in ['rast_hdr', 'zone_id_ras']:
            raster_files[key] = os.path.join(output_path, raster_files[key])

    # TABLE NAMES
    table_files = {
        'constraints_tbl': 'constraints.csv',
        'attractors_tbl': 'attractors.csv',
        'population_tbl': 'population.csv',
        'parameters_tbl': 'parameters.csv',
        'overflow_tbl': 'out_cell_overflow.csv',
        'density_tbl': 'density.csv',
        'metadata_tbl': 'out_cell_metadata.csv'
    }

    for key in ['constraints_tbl', 'attractors_tbl', 'population_tbl', 'parameters_tbl']:
        table_files[key] = os.path.join(output_path, table_files[key])
    for key in ['overflow_tbl', 'density_tbl', 'metadata_tbl']:
        table_files[key] = os.path.join(swap_path, table_files[key])


    # IMPORT PARAMETERS
    df = pd.read_csv(table_files['parameters_tbl'])
    parameters = df.to_dict(orient='records')[0]

    print("Parameters file imported.")

    # COUNT ROWS IN TABLES
    num_zones = len(pd.read_csv(table_files['population_tbl'])) 
    num_constraints = len(pd.read_csv(table_files['constraints_tbl'])) 
    num_attractors = len(pd.read_csv(table_files['attractors_tbl'])) 
    # Print the number of zones, constraints, and attractors
    print(f'Number of zones: {num_zones}')
    print(f'Number of constraints: {num_constraints}')
    print(f'Number of attractors: {num_attractors}')

    # READ RASTER HEADER
    with open(raster_files['zone_id_ras'], 'r') as f:
        lines = f.readlines()
        ncols = int(lines[0].split('ncols')[1].split('\n')[0])
        nrows = int(lines[1].split('nrows')[1].split('\n')[0])
        xllcorner = float(lines[2].split('xllcorner')[1].split('\n')[0])
        yllcorner = float(lines[3].split('yllcorner')[1].split('\n')[0])
        cellsize = float(lines[4].split('cellsize')[1].split('\n')[0])
        nodatavalue = float(lines[5].split('NODATA_value')[1].split('\n')[0])
        header_values = [ncols, nrows, xllcorner, yllcorner, cellsize, nodatavalue]

    # STANDARDIZE ATTRACTOR LAYERS: 
    # Read attractor table and extract layer names and polarity flags
    # For each attractor, open the raster file, standardize it based on polarity flag
    # Save the standardized attractor layer with the original header (first 6 lines)
    # Save as ASCII file in the output folder with the name prefixed by 'std_'
    attractorflag_list = pd.read_csv(table_files['attractors_tbl'])[['layer_name','reverse_polarity_flag']].values.tolist()
    mask_layer = np.loadtxt(raster_files['zone_id_ras'], skiprows=6)

    for i in range(num_attractors):
        attractor_path = os.path.join(swap_path, attractorflag_list[i][0])
        rev_attractor_flag = attractorflag_list[i][1]
        attractor_layer = np.loadtxt(attractor_path, skiprows=6)
        if rev_attractor_flag == 0:
            standarised_attractor_layer = rt.Standardise(attractor_layer, mask_layer, nodatavalue)
        elif rev_attractor_flag == 1:
            standarised_attractor_layer = rt.RevPolarityStandardise(attractor_layer, mask_layer, nodatavalue)
        attractor_output_path = os.path.join(output_path, 'std_' + attractorflag_list[i][0])
        with open(attractor_output_path, 'w') as f:
            f.write(''.join(lines[:6]))
            np.savetxt(f, standarised_attractor_layer, fmt='%1.3f')

    # COVERAGE TO CONSTRAINT
    #generate combined constraint and current development rasters
    rt.RasteriseAreaThresholds(swap_path, header_values, lines[:6], raster_files['constraint_ras'], 
                               raster_files['current_dev_ras'], table_files['constraints_tbl'], num_constraints, parameters['coverage_threshold'])
    
    #mask nodata for region using zone_id_ras
    rt.IRasterSetNoDataToRef(raster_files['constraint_ras'],lines[:6],mask_layer,header_values)

    # MULTI CRITERIA EVALUATION
    # Set bval based upon boolean input (bin_ras) - it can then be tested in place as function argument
    bval = 1 if control_params['bin_ras'] else 0
    # Set rval based upon boolean input (reverse) - it can then be tested in place as function argument
    rval = 1 if control_params['attractor_reverse'] else 0
    # Generate suitability raster
    mce.MaskedWeightedSum(bval, raster_files['constraint_ras'], num_attractors, table_files['attractors_tbl'], raster_files['cell_suit_ras'], 
                      lines[:6],header_values, swap_path, rval)
    print("Suitability raster generated.")

    # CREATE DEVELOPMENT AREAS
    # hardcoded minimum plot size and moore parameters
    mval = 1 if control_params['moore'] else 0

    

