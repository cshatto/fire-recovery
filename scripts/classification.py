import xarray as xr
import rioxarray
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape, MultiPolygon
import geopandas as gpd
import os
from sklearn.cluster import KMeans

def classify_recovery(mscn):
    scene_sept, scene_nov, scene_apr = mscn.scenes[1:4]
    for scene in [scene_sept, scene_nov, scene_apr]:
        scene.load(['ndvi'])
    ndvi_sept = scene_sept['ndvi'].compute()
    ndvi_nov = scene_nov['ndvi'].compute()
    ndvi_apr = scene_apr['ndvi'].compute()
    ba_mask = scene_sept['ba_mask'].compute()

    # Thresholding classification
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

    # K-means clustering with reshaping
    for scene, date in [(scene_nov, '20241109'), (scene_apr, '20250423')]:
        dndvi = scene['dndvi'].values
        valid_mask = (ba_mask == 1) & (~np.isnan(dndvi))
        dndvi_valid = dndvi[valid_mask].reshape(-1, 1)
        
        if len(dndvi_valid) > 0:
            kmeans = KMeans(n_clusters=3, random_state=42).fit(dndvi_valid)
            # Get cluster centers and sort by mean dNDVI
            cluster_centers = kmeans.cluster_centers_.flatten()
            sorted_indices = np.argsort(cluster_centers)
            label_map = {sorted_indices[0]: 1, sorted_indices[1]: 2, sorted_indices[2]: 3}
            labels = np.zeros_like(dndvi, dtype='uint8')
            raw_labels = kmeans.labels_
            labels[valid_mask] = np.array([label_map[label] for label in raw_labels])
            scene['kmeans_mask'] = xr.DataArray(labels, coords=scene['dndvi'].coords, dims=scene['dndvi'].dims).astype('uint8')
        else:
            scene['kmeans_mask'] = xr.zeros_like(scene['recovery_mask'], dtype='uint8')

        # Vectorize and save thresholding results
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
        output_dir = "data/output/classification"
        os.makedirs(output_dir, exist_ok=True)
        gdf.to_file(f'{output_dir}/thresh_areas_{date}.geojson') if not gdf.empty else gpd.GeoDataFrame(geometry=[shape(MultiPolygon())], crs='EPSG:4326').to_file(f'{output_dir}/recovery_areas_{date}.geojson')
        os.remove(temp_tif)

        # Vectorize and save k-means results
        temp_tif_kmeans = f'temp_kmeans_{date}.tif'
        scene['kmeans_mask'].rio.to_raster(temp_tif_kmeans)
        with rioxarray.open_rasterio(temp_tif_kmeans) as src:
            mask_data = src.squeeze().values
            transform = src.rio.transform()
            polygons = [
                {'geometry': shape(geom), 'recovery': {1: 'No Recovery', 2: 'Moderate Recovery', 3: 'High Recovery'}[val]}
                for val in [1, 2, 3] for geom, val in shapes(mask_data, mask=mask_data == val, transform=transform)
                if shape(geom).is_valid
            ]
        gdf_kmeans = gpd.GeoDataFrame(polygons, crs='EPSG:4326')
        gdf_kmeans.to_file(f'{output_dir}/kmeans_areas_{date}.geojson') if not gdf_kmeans.empty else gpd.GeoDataFrame(geometry=[shape(MultiPolygon())], crs='EPSG:4326').to_file(f'{output_dir}/kmeans_areas_{date}.geojson')
        os.remove(temp_tif_kmeans)

    return scene_sept, scene_nov, scene_apr
