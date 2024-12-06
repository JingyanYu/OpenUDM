import numpy as np
from scipy.ndimage import label

############################################################################################################
# Functions related find_zone_dev_patches
############################################################################################################

# Function remove_patch_smaller_than_minimum_development_area
def remove_patch_smaller_than_minimum_development_area(zone_patches, num_zone_patches, minimum_development_area,zone_id):
    # Calculate the size of each patch
    patch_sizes = np.array([np.sum(zone_patches == i) for i in range(1, num_zone_patches + 1)])
    
    # Find the patche ids that are smaller than the minimum development
    patches_to_remove = np.where(patch_sizes < minimum_development_area)[0] + 1
    # If there are patches smaller than the minimum development area, remove them
    if len(patches_to_remove) > 0:

        # Exception: Check if the largest patch is smaller than the minimum development area
        if max(patch_sizes) < minimum_development_area:
            print('No patches larger than the minimum development area')
        else:
            print('Removing patches smaller than the minimum development area in zone', zone_id)
            zone_patches_cp = zone_patches.copy()
            # Remove the patches smaller than the minimum development area by setting the patch cells to 0 and adjusting the patch IDs given the removal
            for patch_id in patches_to_remove:
                zone_patches_cp[zone_patches == patch_id] = 0
                zone_patches_cp[zone_patches > patch_id] -= 1
            return zone_patches_cp, num_zone_patches - len(patches_to_remove)
    else:
        return zone_patches, num_zone_patches


# Helper Function - label_patches_in_zone: Label patches in a zone and filter out patches smaller than the minimum development area
def label_patches_in_zone(constraint_array, zone_id_ras, zone_id, minimum_development_area):
    array_tolabel = constraint_array.copy()

    # Prepare the array to be labeled SciPy's label function - set all cells not in the current zone to 0
    array_tolabel[zone_id_ras != zone_id] = 0
    
    # Run scipy's label function - zone_patches is the labeled array, numPatches is the number of patches found
    zone_patches, num_zone_patches = label(array_tolabel)

    # Check if a found patch is smaller than the minimum development area; if so, set the patch cells to background value 0
    zone_patches, num_zone_patches = remove_patch_smaller_than_minimum_development_area(zone_patches,num_zone_patches, minimum_development_area,zone_id)
    
    return zone_patches, num_zone_patches

# Helper Function - adjust_zonal_patch_ids: Adjust the patch IDs to ensure uniqueness across all zones
def adjust_zonal_patch_ids(zone_patches, zone_patch_initial_id,num_zone_patches,no_data_value):

    # Start the numbering of patch ids from the last patch id of the previous zone
    zone_patches[(zone_patches != 0) & (zone_patches != no_data_value)] += zone_patch_initial_id

    # Update the zone_patch_initial_id to add the number of patches in the current zone
    zone_patch_initial_id += num_zone_patches

    return zone_patches, zone_patch_initial_id 

# Function find_zone_dev_patches: Generate zonal development patches ID raster
def find_zone_dev_patches(minimum_development_area, constraint_ras, num_zones,
                          dev_patch_id_ras, header_text, header_values, zone_id_ras):
    # Load the constraint raster
    constraint_array = np.loadtxt(constraint_ras, skiprows=6)
    # Load the zone ID raster
    zone_id_ras = np.loadtxt(zone_id_ras, skiprows=6)
    
    # Check if the zone ID starts from 0 and change to start from 1
    if np.min(zone_id_ras[zone_id_ras!=header_values[-1]])==0:
        zone_id_ras += 1

    num_patches_allzones = 0
    allzones_patches_list = []

    for id in range(1, num_zones+1):
        # Label the patches in the current zone
        zone_patches, num_zone_patches = label_patches_in_zone(constraint_array, zone_id_ras, id, minimum_development_area)
        
        # Adjust the patch IDs to be unique across all zones
        zone_patches, num_patches_allzones = adjust_zonal_patch_ids(zone_patches, num_patches_allzones,num_zone_patches,header_values[-1])
        
        allzones_patches_list.append(zone_patches)
    
    # Merge each zone's patches into a single patch id raster    
    patchID = sum(allzones_patches_list)
    patchID[constraint_array==header_values[-1]]=header_values[-1]
    # Save the patch ID raster
    with open(dev_patch_id_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, patchID, fmt='%d')
    


############################################################################################################
# Functions DevZoneAVGSuit
############################################################################################################
# Function patch_avg_suitability: Compute average patch suitability
def patch_avg_suitability(dev_patch_id_ras, cell_suit_ras, dev_patch_suit_ras, header_text, header_values):

    # Load the zonal development patches ID raster and cell suitability raster
    dev_patchid_array = np.loadtxt(dev_patch_id_ras, skiprows=6)
    cell_suit_array = np.loadtxt(cell_suit_ras, skiprows=6)
    # Initialize the avg patch suitability array
    patch_avg_suit_array = np.zeros((header_values[1],header_values[0]))
    
    # Find unique patch IDs 
    unique_patchids = np.unique(dev_patchid_array)
    unique_patchids = unique_patchids[(unique_patchids != header_values[-1]) & (unique_patchids != 0)]

    # Calculate the average suitability for each patch and assign it to the corresponding cells in the patch_avg_suit_array
    for zone_id in unique_patchids:
        patch_avg_suit_array[dev_patchid_array==zone_id] = np.mean(cell_suit_array[dev_patchid_array==zone_id])

    with open(dev_patch_suit_ras, 'w') as f:
        f.write(''.join(header_text))
        np.savetxt(f, patch_avg_suit_array, fmt='%1.3f')

