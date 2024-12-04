import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Function RunModel: This function runs the main model for urban development.
# It takes in various parameters including the number of zones, parameters, table files, raster files, header values,
# and optional parameters for zonal dwellings per cell and zonal required dwellings.
# The function reads population data, checks development requirements, calculates required development,
# and develops non-overflow zones based on suitability.
def RunModel(num_zones,parameters, table_files, raster_files,header_values):
    # read parameters from parameters.csv
    maxDevRate = parameters['maximum_plot_size']
    zone_cur_pop, zone_fut_pop,zone_cur_dwellings, zone_fut_dwellings,dwellings_per_hectare=(0,0,0,0,0)
    density_calculation_type = parameters['density_calculation_type']
    if density_calculation_type == 1:
        #read from population.csv admin_zone, current_population, future_population
        zoneLabel, zone_cur_pop, zone_fut_pop = pd.read_csv(table_files['population_tbl'], usecols=[1, 2, 3]).values.T
    if density_calculation_type == 2:
        #read from dwellings.csv admin_zone, current_dwellings, future_dwellings
        zoneLabel, zone_cur_dwellings, zone_fut_dwellings = pd.read_csv(table_files['dwellings_tbl'], usecols=[1, 2, 3]).values.T
    if density_calculation_type == 3:
        zoneLabel, zone_cur_dwellings, zone_fut_dwellings = pd.read_csv(table_files['dwellings_tbl'], usecols=[1, 2, 3]).values.T
        dwellings_per_hectare = parameters['dwellings_per_hectare']

    
    zone_id_ras = np.loadtxt(raster_files['zone_id_ras'], skiprows=6)
    adminzone_idx = np.unique(zone_id_ras)
    adminzone_idx = adminzone_idx[adminzone_idx!=header_values[5]]

    # Check weather each admin zone requires development by population change > 0
    # original function - CalculatePopulationChange
    # devReq = (zone_fut_pop - zone_cur_pop)>0

    # Multiple admin zones
    dev_area_patchid_array = np.loadtxt(raster_files['dev_area_id_ras'], skiprows=6)
    dev_area_suit_array = np.loadtxt(raster_files['dev_area_suit_ras'], skiprows=6)
    # Same for all admin zones
    cell_suit_ras = np.loadtxt(raster_files['cell_suit_ras'], skiprows=6)
    current_dev_ras = np.loadtxt(raster_files['current_dev_ras'], skiprows=6)
    #AssignZones pass
    
    #CalculateRequiredDevelopment
    num_req_cells_zones = [calculate_required_cells(density_calculation_type,
                             current_dev_ras, zone_id_ras, zone_label,
                             zone_cur_pop, zone_fut_pop,
                             zone_cur_dwellings, zone_fut_dwellings,
                             dwellings_per_hectare) for zone_label in adminzone_idx]
    #FindOverflowWards
    # for each admin zone, sum number of cells of all its patches, compare with the number of cells of required development
    num_suitCells = [(dev_area_patchid_array[zone_id_ras==zone_label]>0).sum() for zone_label in adminzone_idx]
    overFlow_array =  num_suitCells < num_req_cells_zones
    

    #number of non overflow zones
    num_nonOverflowZones = (overFlow_array==False).sum()
    num_OverflowZones = num_zones - num_nonOverflowZones

    # code need to be changed when dealing with multiple admin zones
    # if num_OverflowZones > 0:
    #     for i in range(num_OverflowZones):
    #         new_development = DevelopOverflowZones(current_dev_ras,num_OverflowZones,reqDevCells,dev_area_patchid_array)
    if num_nonOverflowZones > 0:
        for i in range(num_nonOverflowZones):
            new_development = develop_one_non_overflow_zone(current_dev_ras, num_req_cells_zones[i], dev_area_patchid_array, dev_area_suit_array, cell_suit_ras, header_values[5])
    return new_development


####################################################################################################################
# Functions related to calculate required number of development cells
####################################################################################################################
    
# Function sum_current_cells: For one administrative zone, calculate the sum of current developed cells.
def sum_current_cells(current_dev_ras, zone_id_ras, zone_label):
    return current_dev_ras[zone_id_ras==zone_label].sum()

# Function calculate_req_cells_population: For one administrative zone, calculate the required development cells
# based on the given population change. It calculates the number of current developed cells, the current population
# per cell, and then calculates the required number of development cells based on the population change.
def calculate_req_cells_population(current_dev_ras, zone_id_ras, zone_label, zone_cur_pop, zone_fut_pop):
    
    #calculate number of current developed cells in the admin zone
    num_current_developed_cells = sum_current_cells(current_dev_ras, zone_id_ras, zone_label)
    
    # Handle case where num_current_developed_cells is zero
    if num_current_developed_cells == 0:
        print('The number of current developed cells is zero.')
        return 0
    
    #calculate current population per cell
    cur_pop_per_cell = zone_cur_pop / num_current_developed_cells if zone_cur_pop > 0 else 0
    
    # Handle case where cur_pop_per_cell is zero or negative
    if cur_pop_per_cell <= 0:
        print('The current population per cell is zero or negative.')
        return 0
    
    # Calculate required number of development cells by population change
    population_change = zone_fut_pop - zone_cur_pop
    if population_change <= 0:
        print('The population change is zero or negative.')
        num_cells = 0
    else:
        num_cells = np.ceil(population_change / cur_pop_per_cell)
    
    return num_cells

# Function calculate_req_cells_dwellings: For one administrative zone, calculate the required development cells 
# based on the given increase number of dwellings. It calculates the number of current developed cells, the 
# current dwellings per cell, and then calculates the required number of development cells based on the increase 
# in the number of dwellings.
def calculate_req_cells_dwellings(current_dev_ras, zone_id_ras, zone_label, zone_cur_dwellings, zone_fut_dwellings):
    # Calculate number of current developed cells in the admin zone
    num_current_developed_cells = sum_current_cells(current_dev_ras, zone_id_ras, zone_label)
    
    # Handle case where num_current_developed_cells is zero
    if num_current_developed_cells == 0:
        print('The number of current developed cells is zero.')
        return 0
    
    # Calculate current dwellings per cell
    cur_dwellings_per_cell = zone_cur_dwellings / num_current_developed_cells if zone_cur_dwellings > 0 else 0
    
    # Handle case where cur_dwellings_per_cell is zero or negative
    if cur_dwellings_per_cell <= 0:
        print('The current dwellings per cell is zero or negative.')
        return 0
    
    # Calculate required number of development cells by dwellings
    dwelling_increase = zone_fut_dwellings - zone_cur_dwellings
    if dwelling_increase <= 0:
        print('The dwelling increase is zero or negative.')
        return 0
    else:
        num_cells = np.ceil(dwelling_increase / cur_dwellings_per_cell)
    
    return num_cells

# Function calculate_req_cells_DwellingsPerHectare: For one administrative zone, calculate the required development cells
# based on the given increase in the number of dwellings and the specified dwellings per hectare value. 
def calculate_req_cells_DwellingsPerHectare(zone_cur_dwellings, zone_fut_dwellings, dwellings_per_hectare):
    # Calculate the increase in dwellings
    dwelling_increase = zone_fut_dwellings - zone_cur_dwellings
    
    # Handle case where dwelling_increase is zero or negative
    if dwelling_increase <= 0:
        print('The dwelling increase is zero or negative.')
        return 0
    
    # Handle case where dwellings_per_hectare is zero or negative
    if dwellings_per_hectare <= 0:
        print('The dwellings per hectare is zero or negative.')
        return 0
    
    # Calculate the required number of cells
    num_cells = np.ceil(dwelling_increase / dwellings_per_hectare)
    
    return num_cells

# Function CalculateRequiredDevelopment for an admin zone
# This function calculates the required number of development cells for an administrative zone.
# It supports multiple options for calculating the required cells:
# 1. Based on population change: Calculates the required cells based on the change in population.
# 2. Based on dwellings change: Calculates the required cells based on the increase in the number of dwellings.
# 3. Based on dwellings change and dwellings per hectare: Calculates the required cells based on a user-specified dwellings per hectare value.
# 4. Placeholder for future variable density calculation methods.
def calculate_required_cells(density_calculation_type,
                             current_dev_ras, zone_id_ras, zone_label,
                             zone_cur_pop=0, zone_fut_pop=0,
                             zone_cur_dwellings=0, zone_fut_dwellings=0,
                             dwellings_per_hectare=0):
    
    # Validate the density calculation type
    if density_calculation_type not in {1, 2, 3, 4}:
        raise ValueError("density_calculation_type must be an integer in {1, 2, 3, 4}")
    
    # Calculate required cells based on population
    if density_calculation_type == 1:
        num_req_cells = calculate_req_cells_population(current_dev_ras, zone_id_ras, zone_label, zone_cur_pop, zone_fut_pop)
    
    # Calculate required cells based on dwellings
    elif density_calculation_type == 2:
        num_req_cells = calculate_req_cells_dwellings(current_dev_ras, zone_id_ras, zone_label, zone_cur_dwellings, zone_fut_dwellings)
    
    # Calculate required cells based on dwellings per hectare
    elif density_calculation_type == 3:
        num_req_cells = calculate_req_cells_DwellingsPerHectare(zone_cur_dwellings, zone_fut_dwellings, dwellings_per_hectare)
    
    # Placeholder for future density calculation type
    elif density_calculation_type == 4:
        pass
    
    return num_req_cells

####################################################################################################################
# Functions related to developing non-overflow zones
####################################################################################################################
def initialize_development_raster(current_dev_ras):
    return current_dev_ras.copy()

# Function get_patch_indices: Given the patch ID array and the nodata value,
# this function returns the unique patch indices excluding the nodata value and 0 - the background value in scipy label function.
def get_patch_indices(dev_area_patchid_array, nodata_value):
    patch_idx = np.unique(dev_area_patchid_array)
    patch_idx = patch_idx[(patch_idx > 0) & (patch_idx != nodata_value)]
    return patch_idx

# Function get_patch_suitability: Given the patch ID array, the suitability array, and the patch indices,
# this function returns the suitability values for cells with the specified patch indices.
def get_patch_suitability(dev_area_patchid_array, dev_area_suit_array, patch_idx):
    if len(patch_idx) == 0:
        print('The patch indices are empty.')
        return np.array([])
    else:
        patch_suit = np.array([dev_area_suit_array[dev_area_patchid_array == patch][0] for patch in patch_idx])
        return patch_suit

# Sorts patch indices based on their suitability scores.
def sort_patch_indices_by_suitability(patch_idx, patch_suit):
    return patch_idx[np.argsort(patch_suit)]

# Function develop_entire_patch: Given the new development raster, the patch ID array, a patch ID, the number of new development cells,
# and the number of cells in the patch, this function updates the new development raster by developing the entire patch.  
def develop_entire_patch(new_development_ras, dev_area_patchid_array, patch_id, num_new_dev_cells,num_patchcells):
    num_new_dev_cells += num_patchcells
    new_development_ras[dev_area_patchid_array == patch_id] = 1
    return num_new_dev_cells, new_development_ras

# Function initialize_patch_potential_cells: Given the development area patch ID array and a patch ID,
# this function initializes the potential cells to be the cells in the patch.
def initialize_patch_potential_cells(dev_area_patchid_array, patch_id):
    patch_cells = np.argwhere(dev_area_patchid_array == patch_id)
    potential_cells = {tuple(cell) for cell in patch_cells}
    return potential_cells

# Function develop_seed_cell: Given the new development raster, the cell suitability raster, the number of new development cells,
# the potential cells, and the seed cells set, this function finds the cell with the highest suitability in the potential cells,
# develops it, and adds it to the seed cells set. 
# The functions updates the new development raster, the number of new development cells, the seed cells set, and the potential cells set.
def develop_seed_cell(new_development_ras, cell_suit_ras, num_new_dev_cells,potential_cells,seed_cells):
    potential_cells_list = list(potential_cells)
    cell_suit = [cell_suit_ras[cell] for cell in potential_cells_list]
    max_idx = np.argmax(cell_suit)
    seed_cell_idx = potential_cells_list[max_idx]
    seed_cells.add(seed_cell_idx)
    potential_cells.remove(seed_cell_idx)
    new_development_ras[seed_cell_idx[0], seed_cell_idx[1]] = 1
    num_new_dev_cells += 1
    return seed_cell_idx,new_development_ras,num_new_dev_cells, seed_cells, potential_cells

# Function find_neighbours: Given a seed cell index and a list of potential cell indices,
# find the indices of the 8-connected neighbours within the potential cells.
def find_neighbours(seed_idx,potential_indices_list):
    cell_neighbours = []
    potential_indices_set = set(potential_indices_list)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        neighbour = (seed_idx[0] + dx, seed_idx[1] + dy)
        if neighbour in potential_indices_set:
            cell_neighbours.append(neighbour)
    return set(cell_neighbours)

# Function update_neighbours: Given the cell neighbours, the current neighbours set, and the potential cells set,
# this function updates the neighbours set to include the new cell neighbours and updates the potential cells set to remove the new cell neighbours.
def update_neighbours(cell_neighbours,neighbours,potential_cells):
    neighbours = neighbours|cell_neighbours
    potential_cells -= cell_neighbours
    return neighbours, potential_cells

# Function develop_neighbouring_cells: Given the neighbouring cells, the seed cells list, the potential cells list,
# the new development raster, and the cell suitability raster, this function finds the cell with the highest suitability
# among the neighbours, develops it, and adds it to the seed cells list.
# The function updates the seed cells list, the potential cells list, the new development raster, and the number of new development cells.
def develop_neighbouring_cell(neighbours,seed_cells,potential_cells,new_development_ras,cell_suit_ras):
    neighbour_suit = [cell_suit_ras[cell] for cell in neighbours]
    max_idx = np.argmax(neighbour_suit)
    new_cell_idx = neighbours[max_idx]
    seed_cells.append(new_cell_idx)
    potential_cells.remove(new_cell_idx)
    new_development_ras[new_cell_idx[0], new_cell_idx[1]] = 1
    num_new_dev_cells += 1
    return new_cell_idx,seed_cells, potential_cells, new_development_ras, num_new_dev_cells


# Function develop_one_non_overflow_zone: Given the current development raster, the required number of cells in the zone,
# the development area patch ID array, the development area suitability array, the cell suitability raster, and the nodata value,
# this function develops one non-overflow zone by developing the entire patch if the required cells are less than the patch size,
# or by developing the cells with the highest suitability in the patch.
def develop_one_non_overflow_zone(current_dev_ras, zone_required_cells, dev_area_patchid_array, dev_area_suit_array, cell_suit_ras, nodata_value):
    # Initialize new development raster to be the copy of current development raster
    new_development_ras = initialize_development_raster(current_dev_ras)
    num_new_dev_cells = 0
    
    # Get patch indices and suitability
    patch_idx = get_patch_indices(dev_area_patchid_array, nodata_value)
    patch_suit = get_patch_suitability(dev_area_patchid_array, dev_area_suit_array, patch_idx)
    
    # Sort patch indices by patch suitability 
    patch_idx = sort_patch_indices_by_suitability(patch_idx, patch_suit)
    
    # Develop the zone patch by patch
    while num_new_dev_cells < zone_required_cells:
        for patch_id in reversed(patch_idx):
            #Calculate the number of cells in the patch
            num_patchcells = (dev_area_patchid_array == patch_id).sum()

            # When developing all cells of a patch is still insufficient, develop the entire patch
            if num_new_dev_cells + num_patchcells <= zone_required_cells:
                num_new_dev_cells, new_development_ras = develop_entire_patch(new_development_ras, dev_area_patchid_array, patch_id, num_new_dev_cells,num_patchcells)
                continue
            
            #If all cells of the patch developed is more than enough, develop from the cell in the patch with highest cell sutiability
            else:
                # Initialize for developing seed & neighbours in the patch
                # Initialize potential cells for development to be all cells in the patch
                potential_cells = initialize_patch_potential_cells(dev_area_patchid_array, patch_id)
                # Initialize neighbours
                neighbours = set()
                # Initialize seed cells
                seed_cells = set()

                # If the number of development cells not met, develop the rest of the cells in the patch
                while num_new_dev_cells < zone_required_cells:


                    #Find and develop seed - the cell with highest suitability in the potential cells
                    seed_cell_idx,new_development_ras,num_new_dev_cells, seed_cells, potential_cells = develop_seed_cell(new_development_ras, cell_suit_ras, num_new_dev_cells,potential_cells,seed_cells)
                    # Test if after developing the seed cell, the required number of cells is already met
                    if num_new_dev_cells == zone_required_cells:
                        break

                    # Find the neighbours of the last added seed cell:
                    cell_neighbours = find_neighbours(seed_cell_idx, potential_cells)
                    # Update the neighbours to include the new cell neighours; update potential cells to remove the new cell neighbours
                    neighbours, potential_cells = update_neighbours(cell_neighbours,neighbours,potential_cells)

                    # If the last added seed cell has no neighbours, find a non-adjacent new seed cell in rest of patch cells with the highest suitability
                    if neighbours == set():
                        continue
                    # If the last added seed cell has neighbours, develop the neighbours
                    else:
                        while len(neighbours)>0:
                            new_cell_idx,seed_cells, potential_cells, new_development_ras, num_new_dev_cells = develop_neighbouring_cell(neighbours,seed_cells,
                                                                                                                         potential_cells,new_development_ras,cell_suit_ras)
                            if num_new_dev_cells == zone_required_cells:
                                break
                            # Find the neighbours of the last added seed cell:
                            cell_neighbours = find_neighbours(new_cell_idx, potential_cells)
                            # Update the neighbours to include the new cell neighours; update potential cells to remove the new cell neighbours
                            neighbours, potential_cells = update_neighbours(cell_neighbours,neighbours,potential_cells)
    return new_development_ras


def develop_non_overflow_zones(current_dev_ras, num_zones, reqDevCells, dev_area_patchid_array, dev_area_suit_array, cell_suit_ras, nodata_value):
    new_development_ras = current_dev_ras.copy()
    for i in range(num_zones):
        new_development_ras = develop_one_non_overflow_zone(new_development_ras, reqDevCells[i], dev_area_patchid_array, dev_area_suit_array, cell_suit_ras, nodata_value)
    return new_development_ras


####################################################################################################################
# Functions related to developing Overflow zones
####################################################################################################################


def DevelopOverflowZones(current_dev_ras,num_OverflowZones,reqDevCells,dev_area_patchid_array):
    pass