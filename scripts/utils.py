import xarray as xr
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

colors = {1: '#FF0000CC', 2: '#FFFF00CC', 3: '#00FF00CC'}
labels = {1: 'No recovery', 2: 'Moderate recovery', 3: 'High recovery'}

def vectorize_recovery(scene):
    mask_data = scene['recovery_mask'].values
    transform = scene['recovery_mask'].rio.transform()
    crs = scene['recovery_mask'].rio.crs
    polygons = [
        {'geometry': shape(geom), 'recovery': val}
        for val in [1, 2, 3] for geom, val in shapes(mask_data, mask=mask_data == val, transform=transform)
        if shape(geom).is_valid
    ]
    return gpd.GeoDataFrame(polygons, crs=crs) if polygons else gpd.GeoDataFrame(geometry=[], crs=crs)

def plot_bar_chart(gdf, date, labels=labels):
    gdf['area_ha'] = gdf.geometry.area / 10000
    areas = gdf.groupby('recovery')['area_ha'].sum().reindex([1, 2, 3], fill_value=0)
    df = pd.DataFrame({
        'Recovery': [labels.get(i, 'Unknown') for i in [1, 2, 3]],
        'Area (ha)': areas.values
    })
    plt.figure(figsize=(8, 6))
    sns.barplot(data=df, x='Recovery', y='Area (ha)', palette=[colors[i] for i in [1, 2, 3]])
    plt.title(f'Recovery Areas - {date}', fontsize=14)
    plt.xlabel('Recovery Class', fontsize=12)
    plt.ylabel('Area (hectares)', fontsize=12)
    plt.savefig(f'data/output/classification/recovery_bar_{date}.png', dpi=300, bbox_inches='tight')