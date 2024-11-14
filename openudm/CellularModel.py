import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Function RunModel: This function runs the main model for urban development.
# It takes in various parameters including the number of zones, parameters, table files, raster files, header values,
# and optional parameters for zonal dwellings per cell and zonal required dwellings.
# The function reads population data, checks development requirements, calculates required development,
# and develops non-overflow zones based on suitability.
def RunModel(num_zones,parameters, table_files, raster_files,header_values,zonal_dwellings_per_cell=0,zonal_reqDwellings=[]):
    maxDevRate = parameters['maximum_plot_size']

    #read from population.csv admin_zone, current_population, future_population
    zoneLabel, zone_curPop, zone_futPop = pd.read_csv(table_files['population_tbl'], usecols=[1, 2, 3]).values.T

    #Load admin zone density - currently hardcoded to be false. If True, it will be read from density.csv, and assume same density in an admin zone.
    #Load denstity from raster - currently imported from parameters.csv to be false. It will be read from density.asc and create a layer with values representing dwellings.

    zone_id_ras = np.loadtxt(raster_files['zone_id_ras'], skiprows=6)
    adminzone_idx = np.unique(zone_id_ras)
    adminzone_idx = adminzone_idx[adminzone_idx!=header_values[5]]

    # Check weather each admin zone requires development by population change > 0
    # original function - CalculatePopulationChange
    devReq = (zone_futPop - zone_curPop)>0

    dev_area_patchid_array = np.loadtxt(raster_files['dev_area_id_ras'], skiprows=6)
    dev_area_suit_array = np.loadtxt(raster_files['dev_area_suit_ras'], skiprows=6)
    cell_suit_ras = np.loadtxt(raster_files['cell_suit_ras'], skiprows=6)
    current_dev_ras = np.loadtxt(raster_files['current_dev_ras'], skiprows=6)
    #AssignZones pass
    
    #CalculateRequiredDevelopment
    reqDevCells = CalculateRequiredDevelopment(zonal_dwellings_per_cell=zonal_dwellings_per_cell,zonal_reqDwellings=zonal_reqDwellings,
                                               adminzone_idx=adminzone_idx,header_values=header_values,zone_id_ras=zone_id_ras,
                                               current_dev_ras=current_dev_ras,zone_curPop=zone_curPop,zone_futPop=zone_futPop)
    #FindOverflowWards
    # for each admin zone, sum number of cells of all its patches, compare with the number of cells of required development
    num_suitCells = [(dev_area_patchid_array[zone_id_ras==zone_label]>0).sum() for zone_label in adminzone_idx]
    overFlow_array =  num_suitCells < reqDevCells
    

    #number of non overflow zones
    num_nonOverflowZones = (overFlow_array==False).sum()
    num_OverflowZones = num_zones - num_nonOverflowZones

    # code need to be changed when dealing with multiple admin zones
    # if num_OverflowZones > 0:
    #     for i in range(num_OverflowZones):
    #         new_development = DevelopOverflowZones(current_dev_ras,num_OverflowZones,reqDevCells,dev_area_patchid_array)
    if num_nonOverflowZones > 0:
        new_development = DevelopNonOverflowZones(current_dev_ras,num_nonOverflowZones,reqDevCells,dev_area_patchid_array,dev_area_suit_array,cell_suit_ras)
    
    return new_development

# Function CalculateRequiredDevelopment
# possibility 1. zone density provided (previously no zone density provided): zone density * cellsize^2
# possibility **2. based on dwelling: input zonal_dwellings_per_cell, zonal_reqDwellings needed
# possibility 3. based on population (previous implementation)
def CalculateRequiredDevelopment(zonal_dwellings_per_cell=0,zonal_reqDwellings=[],
                                 adminzone_idx=[],header_values=[],current_dev_ras=[],zone_id_ras=[],
                                 zone_curPop=0,zone_futPop=0):
    if zonal_dwellings_per_cell:
    
        reqDevCells = np.ceil(np.vectorize(lambda x, y: x / y)(zonal_reqDwellings, zonal_dwellings_per_cell))
    else:
        curDevArea = np.array([current_dev_ras[zone_id_ras==zone_label].sum()*header_values[4]**2\
                            for zone_label in adminzone_idx])
        devCells = np.array([current_dev_ras[zone_id_ras==zone_label].sum() for zone_label in adminzone_idx])
        zoneDensity = zone_curPop/curDevArea
        cellDensity = zone_curPop/devCells
        reqDevCells = np.ceil(np.vectorize(lambda x, y: x / y)(zone_futPop - zone_curPop, cellDensity))

    return reqDevCells

# Function DevelopNonOverflowZones: for admin zones with sufficient development area, 
# develop from the highest suitable patch. The function iterates through each zone, 
# and for each zone, it iterates through the patches in descending order of suitability.
# It assigns development cells to the new_development_ras array until the required 
# number of development cells is reached for each zone. If a patch cannot fully 
# accommodate the required development, it continues to the next most suitable patch.
def DevelopNonOverflowZones(current_dev_ras,num_zones,reqDevCells,dev_area_patchid_array,dev_area_suit_array,cell_suit_ras):
    new_development_ras = current_dev_ras.copy()
    for i in range(num_zones):
        num_new_dev_cells = 0
        patch_idx = np.unique(dev_area_patchid_array)
        patch_idx = patch_idx[patch_idx>0]
        patch_suit = np.array([dev_area_suit_array[dev_area_patchid_array==patch][0] for patch in patch_idx])
        patch_idx = patch_idx[np.argsort(patch_suit)]
        while num_new_dev_cells < reqDevCells[i]:
            for patch in reversed(patch_idx):
                num_patchcells = (dev_area_patchid_array==patch).sum()
                if num_new_dev_cells + num_patchcells <= reqDevCells[i]:
                    num_new_dev_cells += num_patchcells
                    new_development_ras[dev_area_patchid_array==patch] = 1
                    continue
                else:
                    seed_cell_idx = np.unravel_index(np.argmax(cell_suit_ras * (dev_area_patchid_array==patch)), cell_suit_ras.shape)
                    new_development_ras[seed_cell_idx[0],seed_cell_idx[1]] = 1
                    num_new_dev_cells += 1
                    seed_cells = [seed_cell_idx]
                    patch_cells = np.argwhere(dev_area_patchid_array==patch)
                    potential_cells = [tuple(cell) for cell in patch_cells]
                    potential_cells.remove(seed_cell_idx)
                    if num_new_dev_cells == reqDevCells[i]:
                        break
                    while num_new_dev_cells < reqDevCells[i]:
                        #find 8-connected neighbours of seed_cells
                        neighbours = find_neighbours(seed_cells[-1],potential_cells)
                        if neighbours == []:
                            #find the most suitable cell in potential_cells
                            cell_suit = [cell_suit_ras[cell] for cell in potential_cells]
                            max_idx = np.argmax(cell_suit)
                            new_cell_idx = potential_cells[max_idx]
                            seed_cells.append(new_cell_idx)
                            potential_cells.remove(new_cell_idx) 
                            new_development_ras[new_cell_idx[0],new_cell_idx[1]] = 1
                            num_new_dev_cells += 1  
                        else:
                            #find the most suitable cell in neighbours
                            neighbour_suit = [cell_suit_ras[cell] for cell in neighbours]
                            #find the corresponding index of the most suitable cell
                            max_idx = np.argmax(neighbour_suit)
                            new_cell_idx = neighbours[max_idx]
                            seed_cells.append(new_cell_idx)
                            potential_cells.remove(new_cell_idx)
                            new_development_ras[new_cell_idx[0],new_cell_idx[1]] = 1
                            num_new_dev_cells += 1
                        
    return new_development_ras

# Function find_neighbours: Given a seed cell index and a list of potential cell indices,
# find the indices of the 8-connected neighbours within the potential cells.
def find_neighbours(seed_idx,potential_indices_list):
    neighbours = []
    potential_indices_set = set(potential_indices_list)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        neighbour = (seed_idx[0] + dx, seed_idx[1] + dy)
        if neighbour in potential_indices_set:
            neighbours.append(neighbour)
    return neighbours

def DevelopOverflowZones(current_dev_ras,num_OverflowZones,reqDevCells,dev_area_patchid_array):
    pass