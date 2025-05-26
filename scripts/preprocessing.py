import os
import subprocess
import satpy
from satpy.utils import check_satpy
from glob import glob
from satpy.readers import find_files_and_readers
from satpy import Scene, MultiScene
from pyresample.geometry import AreaDefinition
from datetime import timedelta
import numpy as np
import xarray as xr
from scipy.ndimage import label
import rioxarray
from rasterio.features import shapes
from shapely.geometry import shape, MultiPolygon
import geopandas as gpd
import warnings
import shutil
warnings.filterwarnings("ignore")



def preprocess_data():
    # satpy_composites_dir = "/root/.local/lib/python3.13/site-packages/satpy/etc/composites"
    # msi_yaml = os.path.join(satpy_composites_dir, "msi.yaml")
    # sen2_msi_yaml = os.path.join(satpy_composites_dir, "sen2_msi.yaml")
    # if os.path.exists(msi_yaml) and not os.path.exists(sen2_msi_yaml):
    #     shutil.copy(msi_yaml, sen2_msi_yaml)
    # Collect SAFE files
    safe_dirs = glob("data/safe_rasters/*")
    scene_files = []
    for safe_dir in safe_dirs:
        files = find_files_and_readers(base_dir=safe_dir, reader="msi_safe_l2a")
        scene_files.append(files)

    # Load scenes
    scenes = []
    for files in scene_files:
        scn = Scene(reader="msi_safe_l2a", filenames=files)
        scn.load(["B04","B08","B12","ndvi_l2a", "natural_color_l2a"], calibration="reflectance")
        scenes.append(scn)
    scenes = sorted(scenes, key=lambda scn: scn.start_time)
    mscn = MultiScene(scenes)

    # Resample to area of interest
    area_id = "northern_portugal"
    description = "Northern Portugal region"
    proj_id = "latlong"
    projection = {"proj": "latlong", "datum": "WGS84"}
    width = 1008 #
    height = 1008
    area_extent = (-8.24721, 41.06626, -7.48991, 41.48443)
    area_def = AreaDefinition(area_id, description, proj_id, projection, width, height, area_extent)
    mscn = mscn.resample(area_def)

    # Mosaic scenes by date
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
        group_mscn = MultiScene(group)
        blended = group_mscn.blend()
        mosaicked_scenes.append(blended)
    mscn = MultiScene(mosaicked_scenes)

    # Calculate NBR and NDVI
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

    # Save animation
    output_dir = "data/output/satpy_animations" 
    os.makedirs(output_dir, exist_ok=True)
    mscn.save_animation('data/output/satpy_animations/{name}_{start_time:%Y%m%d_%H%M%S}.mp4', fps=1)

    # Save GeoTIFFs
    for scene in mscn.scenes:
        safe_name = f"S2A_MSIL2A_{scene.start_time.strftime('%Y%m%dT%H%M%S')}"
        for dataset in ['natural_color_l2a', 'ndvi', 'nbr']:
            scene.save_dataset(
                dataset,
                writer='geotiff',
                filename=f"data/satpy_geotiffs/{safe_name}_{dataset}.tif"
            )

    # Pre-processing II: dNBR and burn area mask
    scene_pre, scene_post = list(mscn.scenes)[:2]
    nbr_pre = scene_pre['nbr'].compute()
    nbr_post = scene_post['nbr'].compute()
    dnbr = nbr_pre - nbr_post
    dnbr.attrs = scene_pre['nbr'].attrs
    scene_post['dnbr'] = dnbr.astype('float32')
    ba_mask = (dnbr >= 0.4).astype('uint8')
    ba_mask.attrs = scene_post.attrs
    scene_post['ba_mask'] = ba_mask

    # Filter clusters
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

    # Vectorize burn areas
    temp_tif = 'temp_ba_mask.tif'
    scene_post['ba_mask'].rio.to_raster(temp_tif, driver='GTiff')
    with rioxarray.open_rasterio(temp_tif) as src:
        mask_data = src.squeeze().values
        transform = src.rio.transform()
        crs = src.rio.crs
        shapes_gen = shapes(mask_data, mask=mask_data == 1, transform=transform)
        polygons = [shape(geom) for geom, value in shapes_gen if value == 1]
    ba = MultiPolygon(polygons) if polygons else MultiPolygon()
    gdf = gpd.GeoDataFrame(geometry=[ba], crs=crs)
    gdf.to_file('data/output/burn_areas.geojson')
    os.remove(temp_tif)

    return mscn
