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
#      rast_hdr - header values for the raster file, e.g. header_values
#      swap_path - path to the swap directory, e.g. swap_path
#      zone_id_ras - path to the zone identity raster file, e.g. raster_files['zone_id_ras']
# Output: write the result to a raster file dev_area_id.asc
# 1. Read the constraint raster file into a numpy array mask_array.
# 2. Get the number of columns and rows from the header values.
# 3. create a 2d numpy array admin zone ID of the same size as mask_array, initialized to 1 if path is ''.
# 4. **Different from James' code** Label the constraint raster and generated the labelled array patchID
# 4.1 Prepare data in adminzoneID_array for the label function: increment if zone number starts at 0
# 4.2 Apply label function to array_tolabel, and get the number of unique patches numPatches and labelled array patchID
# 4.3 If the number of elements labelled as one value is less than the minimum_development_area, set the value to 0
# 4.4 Set the value of the nodata cells to the nodata value
# 5. Write final patch ID raster - outputZoneID

def CreateDevPatch(bval, minimum_development_area, mval, constraint_ras, 
                   dev_area_id_ras, header_text, header_values, swap_path, zone_id_ras=''):
    mask_array = np.loadtxt(constraint_ras, skiprows=6)
    array_tolabel = np.loadtxt(constraint_ras, skiprows=6)
    rCols = header_values[0]
    rRows = header_values[1]
    if  zone_id_ras != '':
        adminzoneID_array = np.loadtxt(zone_id_ras, skiprows=6)
    else:
        adminzoneID_array = np.ones((rRows, rCols))
    
    array_tolabel[mask_array==header_values[-1]]=0
    patchID, numPatches = label(array_tolabel)
    for i in range(1,numPatches+1):
        if np.sum(patchID==i)<minimum_development_area:
            patchID[patchID==i]=0
    patchID[mask_array==header_values[-1]]=header_values[-1]
    with open(dev_area_id_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, patchID, fmt='%1.0f')

    
