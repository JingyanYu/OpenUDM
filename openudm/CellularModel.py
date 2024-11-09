import numpy as np
import pandas as pd

#Function RunModel
def RunModel(parameters, table_files, raster_files,header_values,zonal_dwellings_per_cell=0,zonal_reqDwellings=[]):
    maxDevRate = parameters['maximum_plot_size']

    #read from population.csv admin_zone, current_population, future_population
    zoneLabel, zone_curPop, zone_futPop = pd.read_csv(table_files['population_tbl'], usecols=[1, 2, 3]).values.T

    #Load admin zone density - currently hardcoded to be false. If True, it will be read from density.csv, and assume same density in an admin zone.
    #Load denstity from raster - currently imported from parameters.csv to be false. It will be read from density.asc and create a layer with values representing dwellings.

    zone_id_ras = np.loadtxt(raster_files['zone_id_ras'], skiprows=6)
    dev_area_patchid_array = np.loadtxt(raster_files['dev_area_id_ras'], skiprows=6)
    dev_area_suit_array = np.loadtxt(raster_files['dev_area_suit_ras'], skiprows=6)
    cell_suit_ras = np.loadtxt(raster_files['cell_suit_ras'], skiprows=6)
    current_dev_ras = np.loadtxt(raster_files['current_dev_ras'], skiprows=6)
    adminzone_idx = np.unique(zone_id_ras)
    adminzone_idx = adminzone_idx[adminzone_idx!=header_values[5]]

    # Check weather each admin zone requires development by population change > 0
    # original function - CalculatePopulationChange
    devReq = (zone_futPop - zone_curPop)>0

    #AssignZones pass
    
    #CalculateRequiredDevelopment
    reqDevCells = CalculateRequiredDevelopment(zonal_dwellings_per_cell=zonal_dwellings_per_cell,zonal_reqDwellings=zonal_reqDwellings,
                                               adminzone_idx=adminzone_idx,header_values=header_values,zone_id_ras=zone_id_ras,
                                               current_dev_ras=current_dev_ras,zone_curPop=zone_curPop,zone_futPop=zone_futPop)
    #FindOverflowWards
    # for each admin zone, sum number of cells of all its patches, compare with the number of cells of required development
    num_suitCells = [(dev_area_patchid_array[zone_id_ras==zone_label]>0).sum() for zone_label in adminzone_idx]
    overFlow_array =  num_suitCells < reqDevCells

    #
    
    return reqDevCells

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

# Function DevelopNonOverflowWards: for admin zones with sufficient development area, 
# develop from the highest suitable patch.
def DevelopNonOverflowWards():
    pass
