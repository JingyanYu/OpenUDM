import os
import pandas as pd
import numpy as np
from scipy.ndimage import label

# Function CreateDevPatch
# Input:
#      bval - Boolean flag indicating whether to use binary rasters, e.g. True
#      minimum_development_area - parameter from the parameters table, e.g. parameters['minimum_development_area']
#      mval - Boolean flag indicating whether to use Moore neighbourhood, e.g. True
#      constraint_ras - path to the constraint raster file, e.g. raster_files['constraint_ras']
#      dev_area_id_ras - path to the development area identity raster file, e.g. raster_files['dev_area_id_ras']
#      header_text - header text for the raster file, e.g. header_text
#      header_values - header values for the raster file, e.g. header_values
#      swap_path - path to the swap directory, e.g. swap_path
#      zone_id_ras - path to the zone identity raster file, e.g. raster_files['zone_id_ras']
# Output: write the result to a raster file dev_area_id_ras
# 1. Read the constraint raster file into a numpy array constraint_array.
# 2. Get the number of columns and rows from the header values.
# 3. If zone_id_ras is provided, read the zone identity raster file into adminzoneID_array, otherwise initialize it to ones.
# 4. If the minimum value in adminzoneID_array (excluding nodata values) is 0, add 1 to the whole array.
# 5. Get the number of unique zones in adminzoneID_array (excluding nodata values).
# 6. For each zone, create a copy of constraint_array named array_tolabel and set non-zone cells to 0.
# 7. Label the patches in array_tolabel and filter out patches smaller than minimum_development_area.
# 8. Adjust the patch IDs to ensure uniqueness across zones and accumulate them.
# 9. Set the value of the nodata cells in patchID to the nodata value.
# 10. Write the final patch ID raster to dev_area_id_ras.

def CreateDevPatch(bval, minimum_development_area, mval, constraint_ras, num_zones,
                   dev_area_id_ras, header_text, header_values, swap_path, zone_id_ras=''):
    constraint_array = np.loadtxt(constraint_ras, skiprows=6)
    rCols = header_values[0]
    rRows = header_values[1]
    if  zone_id_ras != '':
        adminzoneID_array = np.loadtxt(zone_id_ras, skiprows=6)
    else:
        adminzoneID_array = np.ones((rRows, rCols))
    if np.min(adminzoneID_array[adminzoneID_array!=header_values[-1]])==0:
        adminzoneID_array+=1

    zone_idx = 0
    adminzones_patches_list = []
    for i in range(1, num_zones+1):
        array_tolabel = constraint_array.copy()
        array_tolabel[adminzoneID_array != i] = 0
        zone_patches, numPatches = label(array_tolabel)
        for j in range(1,numPatches+1):
            if np.sum(zone_patches==j)<minimum_development_area:
                zone_patches[zone_patches==j]=0
        count = np.unique(zone_patches).shape[0]-1
        zone_patches[zone_patches>0]+=zone_idx
        zone_idx = zone_idx + count
        adminzones_patches_list.append(zone_patches)
    patchID = sum(adminzones_patches_list)
    patchID[constraint_array==header_values[-1]]=header_values[-1]
    with open(dev_area_id_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, patchID, fmt='%1.0f')


# Function DevZoneAVGSuit
# Input:
#      bval - Boolean flag indicating whether to use binary rasters, e.g. True
#      dev_area_id_ras - path to the development area identity raster file, e.g. raster_files['dev_area_id_ras']
#      cell_suit_ras - path to the cell suitability raster file, e.g. raster_files['cell_suit_ras']
#      dev_area_suit_ras - path to the development area suitability raster file, e.g. raster_files['dev_area_suit_ras']
#      rast_hdr - path to the raster header file, e.g. raster_files['rast_hdr']
#      swap_path - path to the swap directory, e.g. swap_path
# Output: write the result to a raster file dev_area_suit_ras
# 1. Read the zonal development patches ID raster file into a numpy array dev_area_patchid_array.
# 2. Read the cell suitability raster file into a numpy array cell_suit_array.
def DevZoneAVGSuit(bval, dev_area_id_ras, cell_suit_ras, dev_area_suit_ras, 
                   header_text, header_values, swap_path):
    dev_area_patchid_array = np.loadtxt(dev_area_id_ras, skiprows=6)
    cell_suit_array = np.loadtxt(cell_suit_ras, skiprows=6)
    dev_area_suit_array = np.zeros((header_values[1],header_values[0]))
    
    unique_patchids = np.unique(dev_area_patchid_array)
    unique_patchids = unique_patchids[(unique_patchids != header_values[-1]) & (unique_patchids != 0)]
    for zone_id in unique_patchids:
        dev_area_suit_array[dev_area_patchid_array==zone_id] = np.mean(cell_suit_array[dev_area_patchid_array==zone_id])
    with open(dev_area_suit_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, dev_area_suit_array, fmt='%1.3f')

