import xarray as xr
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

def get_postgis_engine():
    load_dotenv('.env.local')
    # Credentials (only stored locally)
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST', 'localhost'), 
        'port': os.getenv('DB_PORT', '5432')  
    }
    
    # Validate that all required credentials are present
    missing_params = [key for key, value in db_params.items() if value is None]
    if missing_params:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_params)}")
    
    return create_engine(
        f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
    )

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

def vectorize_recovery_kmeans(scene):
    mask_data = scene['kmeans_mask'].values
    transform = scene['kmeans_mask'].rio.transform()
    crs = scene['kmeans_mask'].rio.crs
    polygons = [
        {'geometry': shape(geom), 'recovery': val}
        for val in [1, 2, 3] for geom, val in shapes(mask_data, mask=mask_data == val, transform=transform)
        if shape(geom).is_valid
    ]
    return gpd.GeoDataFrame(polygons, crs=crs) if polygons else gpd.GeoDataFrame(geometry=[], crs=crs)

def plot_bar_chart(gdf, date, labels=labels, title_prefix=''):
    gdf['area_ha'] = gdf.geometry.area / 10000
    areas = gdf.groupby('recovery')['area_ha'].sum().reindex([1, 2, 3], fill_value=0)
    df = pd.DataFrame({
        'Recovery': [labels.get(i, 'Unknown') for i in [1, 2, 3]],
        'Area (ha)': areas.values
    })
    plt.figure(figsize=(8, 6))
    sns.barplot(data=df, x='Recovery', y='Area (ha)', palette=[colors[i] for i in [1, 2, 3]])
    plt.title(f'{title_prefix}Recovery Areas - {date}', fontsize=14)
    plt.xlabel('Recovery Class', fontsize=12)
    plt.ylabel('Area (hectares)', fontsize=12)
    plt.savefig(f'data/output/classification/{title_prefix.lower().replace(" ", "_")}recovery_bar_{date}.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_comparison_bar_chart(gdf_thresh, gdf_kmeans, date, labels=labels):
    gdf_thresh['area_ha'] = gdf_thresh.geometry.area / 10000
    gdf_kmeans['area_ha'] = gdf_kmeans.geometry.area / 10000
    areas_thresh = gdf_thresh.groupby('recovery')['area_ha'].sum().reindex([1, 2, 3], fill_value=0)
    areas_kmeans = gdf_kmeans.groupby('recovery')['area_ha'].sum().reindex([1, 2, 3], fill_value=0)
    df = pd.DataFrame({
        'Recovery': [labels.get(i, 'Unknown') for i in [1, 2, 3]] * 2,
        'Area (ha)': list(areas_thresh.values) + list(areas_kmeans.values),
        'Method': ['Thresholding'] * 3 + ['K-means'] * 3
    })
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='Recovery', y='Area (ha)', hue='Method', palette=['#4FC3F7', '#1976D2'])    
    plt.title(f'Thresholding vs K-means Recovery Areas - {date}', fontsize=14)
    plt.xlabel('Recovery Class', fontsize=12)
    plt.ylabel('Area (hectares)', fontsize=12)
    plt.legend(title='Method')
    plt.savefig(f'data/output/classification/comparison_recovery_bar_{date}.png', dpi=300, bbox_inches='tight')
    plt.close()