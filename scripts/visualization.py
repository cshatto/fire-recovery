import geopandas as gpd
import folium
from folium.features import GeoJson, GeoJsonTooltip
import pandas as pd
from utils import vectorize_recovery, vectorize_recovery_kmeans, plot_bar_chart, plot_comparison_bar_chart

def visualize_recovery(scene_sept, scene_nov, scene_apr):
    # Bar charts for thresholding and k-means
    for scene, date in [(scene_nov, '20241109'), (scene_apr, '20250423')]:
        # Thresholding bar chart
        gdf = vectorize_recovery(scene)
        plot_bar_chart(gdf, date, title_prefix='Thresholding ')
        # K-means bar chart
        gdf_kmeans = vectorize_recovery_kmeans(scene)
        plot_bar_chart(gdf_kmeans, date, title_prefix='K-means ')
        # Comparison bar chart
        plot_comparison_bar_chart(gdf, gdf_kmeans, date)

    # Print pixel count
    print(f"ba_mask pixels={scene_sept['ba_mask'].sum().values}")

    # Load GeoJSON files
    try:
        gdf_20241109 = gpd.read_file('data/output/classification/recovery_areas_20241109.geojson')
        gdf_20250423 = gpd.read_file('data/output/classification/recovery_areas_20250423.geojson')
        gdf_kmeans_20241109 = gpd.read_file('data/output/classification/kmeans_areas_20241109.geojson')
        gdf_kmeans_20250423 = gpd.read_file('data/output/classification/kmeans_areas_20250423.geojson')
    except Exception as e:
        print(f"Error loading shapefiles: {e}")
        exit()

    # Ensure CRS is EPSG:4326
    for gdf in [gdf_20241109, gdf_20250423, gdf_kmeans_20241109, gdf_kmeans_20250423]:
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

    # Filter valid geometries
    gdf_20241109 = gdf_20241109[gdf_20241109.geometry.is_valid]
    gdf_20250423 = gdf_20250423[gdf_20250423.geometry.is_valid]
    gdf_kmeans_20241109 = gdf_kmeans_20241109[gdf_kmeans_20241109.geometry.is_valid]
    gdf_kmeans_20250423 = gdf_kmeans_20250423[gdf_kmeans_20250423.geometry.is_valid]
    print(f"Valid features after filtering (Thresholding 2024-11-09): {len(gdf_20241109)}")
    print(f"Valid features after filtering (Thresholding 2025-04-23): {len(gdf_20250423)}")
    print(f"Valid features after filtering (K-means 2024-11-09): {len(gdf_kmeans_20241109)}")
    print(f"Valid features after filtering (K-means 2025-04-23): {len(gdf_kmeans_20250423)}")

    if len(gdf_20241109) == 0 or len(gdf_20250423) == 0 or len(gdf_kmeans_20241109) == 0 or len(gdf_kmeans_20250423) == 0:
        print("Error: One or more GeoDataFrames are empty after validation.")
        exit()

    # Assign recovery labels
    gdf_20241109['recovery_20241109'] = gdf_20241109.get('recovery', 'unknown').astype(str).replace('nan', 'unknown')
    gdf_20250423['recovery_20250423'] = gdf_20250423.get('recovery', 'unknown').astype(str).replace('nan', 'unknown')
    gdf_kmeans_20241109['recovery_kmeans_20241109'] = gdf_kmeans_20241109.get('recovery', 'unknown').astype(str).replace('nan', 'unknown')
    gdf_kmeans_20250423['recovery_kmeans_20250423'] = gdf_kmeans_20250423.get('recovery', 'unknown').astype(str).replace('nan', 'unknown')

    colors = {
        'No Recovery': '#FF0000CC',
        'Moderate Recovery': '#FFFF00CC',
        'High Recovery': '#00FF00CC',
        'unknown': '#808080CC'
    }

    # Initialize Folium map
    m = folium.Map(
        location=[(41.07 + 41.48) / 2, (-8.247 + -7.49) / 2],
        zoom_start=10,
        tiles='CartoDB positron',
        name='Light Basemap'
    )

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite Imagery'
    ).add_to(m)

    # Style functions
    def style_nov(feature):
        recovery = feature['properties'].get('recovery_20241109', 'unknown')
        return {
            'fillColor': colors.get(recovery, '#00000080'),
            'color': 'black',
            'weight': 0,
            'fillOpacity': 0.6
        }

    def style_apr(feature):
        recovery = feature['properties'].get('recovery_20250423', 'unknown')
        return {
            'fillColor': colors.get(recovery, '#00000080'),
            'color': 'black',
            'weight': 0,
            'fillOpacity': 0.6
        }

    def style_kmeans_nov(feature):
        recovery = feature['properties'].get('recovery_kmeans_20241109', 'unknown')
        return {
            'fillColor': colors.get(recovery, '#00000080'),
            'color': 'black',
            'weight': 0,
            'fillOpacity': 0.6
        }

    def style_kmeans_apr(feature):
        recovery = feature['properties'].get('recovery_kmeans_20250423', 'unknown')
        return {
            'fillColor': colors.get(recovery, '#00000080'),
            'color': 'black',
            'weight': 0,
            'fillOpacity': 0.6
        }

    # Tooltips
    tooltip_nov = folium.GeoJsonTooltip(
        fields=["recovery_20241109"],
        aliases=["Thresholding 2024-11-09"],
        labels=True,
        sticky=True,
        localize=True,
        style="font-size: 14px; font-weight: bold;"
    )

    tooltip_apr = folium.GeoJsonTooltip(
        fields=["recovery_20250423"],
        aliases=["Thresholding 2025-04-23"],
        labels=True,
        sticky=True,
        localize=True,
        style="font-size: 14px; font-weight: bold;"
    )

    tooltip_kmeans_nov = folium.GeoJsonTooltip(
        fields=["recovery_kmeans_20241109"],
        aliases=["K-means 2024-11-09"],
        labels=True,
        sticky=True,
        localize=True,
        style="font-size: 14px; font-weight: bold;"
    )

    tooltip_kmeans_apr = folium.GeoJsonTooltip(
        fields=["recovery_kmeans_20250423"],
        aliases=["K-means 2025-04-23"],
        labels=True,
        sticky=True,
        localize=True,
        style="font-size: 14px; font-weight: bold;"
    )

    # Add GeoJSON layers
    folium.GeoJson(
        gdf_20241109,
        style_function=style_nov,
        tooltip=tooltip_nov,
        name='Thresholding Recovery 2024-11-09'
    ).add_to(m)

    folium.GeoJson(
        gdf_20250423,
        style_function=style_apr,
        tooltip=tooltip_apr,
        name='Thresholding Recovery 2025-04-23'
    ).add_to(m)

    folium.GeoJson(
        gdf_kmeans_20241109,
        style_function=style_kmeans_nov,
        tooltip=tooltip_kmeans_nov,
        name='K-means Recovery 2024-11-09'
    ).add_to(m)

    folium.GeoJson(
        gdf_kmeans_20250423,
        style_function=style_kmeans_apr,
        tooltip=tooltip_kmeans_apr,
        name='K-means Recovery 2025-04-23'
    ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save('data/output/classification/recovery_map.html')
    print("Folium map saved as 'recovery_map.html'")
    
if __name__ == "__main__":
    from preprocessing import preprocess_data
    from classification import classify_recovery
    mscn = preprocess_data()
    scene_sept, scene_nov, scene_apr = classify_recovery(mscn)
    visualize_recovery(scene_sept, scene_nov, scene_apr)