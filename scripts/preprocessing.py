import os
from datetime import timedelta
import numpy as np
from glob import glob
import xarray as xr
import satpy
from satpy.utils import check_satpy
from satpy.readers import find_files_and_readers
from satpy import Scene, MultiScene
from pyresample.geometry import AreaDefinition
from scipy.ndimage import label
import rioxarray
from rasterio.features import shapes
from shapely.geometry import shape, MultiPolygon


# Get list of SAFE directories
safe_dirs = glob("data/safe_rasters/*")

# Collect files for each SAFE directory
scene_files = []
for safe_dir in safe_dirs:
    files = find_files_and_readers(base_dir=safe_dir, reader="msi_safe_l2a")
    scene_files.append(files)
    
scenes = []
for files in scene_files:
    scn = Scene(reader="msi_safe_l2a", filenames=files)
    scn.load(["B04","B08","B12","ndvi_l2a", "natural_color_l2a"],calibration="reflectance") 
    scenes.append(scn)
scenes = sorted(scenes, key=lambda scn: scn.start_time)

mscn = MultiScene(scenes)

# challenge info
area_id = "northern_portugal"
description = "Northern Portugal region"
proj_id = "latlong"
projection = {"proj": "latlong", "datum": "WGS84"}
width = 1000
height = 1000
area_extent = (-8.24721, 41.06626, -7.48991, 41.48443)  # South West to North East
area_def = AreaDefinition(area_id, description, proj_id, projection, width, height, area_extent)

# Resample images to same grid and resolution
mscn = mscn.resample(area_def)

# Group scenes by date (1-day threshold) and mosaic
threshold = timedelta(days=1)
mosaicked_scenes = []
scenes = list(mscn.scenes)
while scenes:
    group = [scenes[0]]
    ref_time = scenes[0].start_time
    for s in scenes[1:]:
        if abs(s.start_time - ref_time) <= threshold:
            group.append(s)
    for s in group:
        scenes.remove(s)
    # Mosaic tiles in the group into a single Scene
    group_mscn = MultiScene(group)
    blended = group_mscn.blend()  # Default stack mosaics tiles
    mosaicked_scenes.append(blended)

mscn = MultiScene(mosaicked_scenes)

for scene in mscn.scenes:
    b08 = scene['B08'].compute()
    b12 = scene['B12'].compute()
    nbr = (b08 - b12) / (b08 + b12 + 1e-10)    
    nbr = np.clip(nbr, -1, 1)
    nbr.attrs = scene['B08'].attrs
    ndvi = scene['ndvi_l2a'].compute()
    ndvi = np.clip(ndvi, -1, 1)
    ndvi.attrs = scene['B08'].attrs
    scene['ndvi'] = ndvi
    scene['nbr'] = nbr

mscn.save_animation('data/output/satpy_animations/{name}_{start_time:%Y%m%d_%H%M%S}.mp4', fps=1)

#TODO preserve float
for scene in mscn.scenes:
    safe_name = f"S2A_MSIL2A_{scene.start_time.strftime('%Y%m%dT%H%M%S')}"    
    for dataset in ['natural_color_l2a', 'ndvi', 'nbr']:
        scene.save_dataset(
            dataset,
            writer='geotiff',
            filename=f"data/satpy_geotiffs/{safe_name}_{dataset}.tif"
        )

#### Vectorize BAs using dNBR

scene_pre, scene_post = list(mscn.scenes)[:2]
# Compute dNBR (NBR_pre - NBR_post)
nbr_pre = scene_pre['nbr'].compute()
nbr_post = scene_post['nbr'].compute()
dnbr = nbr_pre - nbr_post
dnbr.attrs = scene_pre['nbr'].attrs
scene_post['dnbr'] = dnbr.astype('float32')

ba_mask = (dnbr >= 0.3).astype('uint8') # could be higher for severe fires but will do pix count later
ba_mask.attrs = scene_post.attrs
scene_post['ba_mask'] = ba_mask

# Identify connected clusters and filter by size, 150 is best sofar
structure = np.ones((3, 3), dtype=np.uint8)  
labeled_array, num_features = label(ba_mask.values, structure=structure)
filtered_mask = np.zeros_like(labeled_array, dtype=np.uint8)
if num_features > 0:
    for i in range(1, num_features + 1):
        cluster_size = np.sum(labeled_array == i)
        if cluster_size > 150:  
            filtered_mask[labeled_array == i] = 1

ba_mask_filtered = xr.DataArray(
    filtered_mask,
    coords=ba_mask.coords,
    dims=ba_mask.dims,
    attrs=ba_mask.attrs
).astype('uint8')
scene_post['ba_mask'] = ba_mask_filtered


#temp file just for vectorization
temp_tif = 'temp_ba_mask.tif'
scene_post['ba_mask'].rio.to_raster(temp_tif, driver='GTiff')

#vectorize mask using rasterio shapes combined with shapley shape
with rioxarray.open_rasterio(temp_tif) as src:
    mask_data = src.squeeze().values
    transform = src.rio.transform()
    crs = src.rio.crs
    shapes_gen = shapes(mask_data, mask=mask_data == 1, transform=transform)
    polygons = [shape(geom) for geom, value in shapes_gen if value == 1]

# Save 
ba = MultiPolygon(polygons) if polygons else MultiPolygon()
gdf = gpd.GeoDataFrame(geometry=[ba], crs=crs)
gdf.to_file('data/output/burn_areas.geojson')

if __name__ == "__main__":
    mscn = preprocess_data()