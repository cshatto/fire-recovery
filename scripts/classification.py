import xarray as xr
import rioxarray
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape, MultiPolygon
import geopandas as gpd
import os

def classify_recovery(mscn):
    scene_sept, scene_nov, scene_apr = mscn.scenes[1:4]
    for scene in [scene_sept, scene_nov, scene_apr]:
        scene.load(['ndvi'])
    ndvi_sept = scene_sept['ndvi'].compute()
    ndvi_nov = scene_nov['ndvi'].compute()
    ndvi_apr = scene_apr['ndvi'].compute()
    ba_mask = scene_sept['ba_mask'].compute()

    # 2024-11-09 dNDVI
    scene_nov['dndvi'] = (ndvi_nov - ndvi_sept).where(ba_mask == 1, np.nan)
    scene_nov['recovery_mask'] = xr.where(ba_mask == 1, np.select(
        [scene_nov['dndvi'] < 0.1, scene_nov['dndvi'] < 0.4, scene_nov['dndvi'] >= 0.4],
        [1, 2, 3], 0
    ), 0).astype('uint8')

    # 2025-04-23 dNDVI
    scene_apr['dndvi'] = (ndvi_apr - ndvi_sept).where(ba_mask == 1, np.nan)
    scene_apr['recovery_mask'] = xr.where(ba_mask == 1, np.select(
        [scene_apr['dndvi'] < 0.1, scene_apr['dndvi'] < 0.4, scene_apr['dndvi'] >= 0.4],
        [1, 2, 3], 0
    ), 0).astype('uint8')

    # Vectorize and save
    for scene, date in [(scene_nov, '20241109'), (scene_apr, '20250423')]:
        temp_tif = f'temp_recovery_{date}.tif'
        scene['recovery_mask'].rio.to_raster(temp_tif)
        with rioxarray.open_rasterio(temp_tif) as src:
            mask_data = src.squeeze().values
            transform = src.rio.transform()
            polygons = [
                {'geometry': shape(geom), 'recovery': {1: 'No Recovery', 2: 'Moderate Recovery', 3: 'High Recovery'}[val]}
                for val in [1, 2, 3] for geom, val in shapes(mask_data, mask=mask_data == val, transform=transform)
                if shape(geom).is_valid
            ]
        gdf = gpd.GeoDataFrame(polygons, crs='EPSG:4326')
        gdf.to_file(f'data/output/classification/recovery_areas_{date}.geojson') if not gdf.empty else gpd.GeoDataFrame(geometry=[shape(MultiPolygon())], crs='EPSG:4326').to_file(f'data/output/classification/recovery_areas_{date}.geojson')
        os.remove(temp_tif)

    return scene_sept, scene_nov, scene_apr

if __name__ == "__main__":
    from scripts.preprocessing import preprocess_data
    mscn = preprocess_data()
    scene_sept, scene_nov, scene_apr = classify_recovery(mscn)