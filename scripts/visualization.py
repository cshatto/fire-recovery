import geopandas as gpd
import folium
from folium.features import GeoJson, GeoJsonTooltip
import pandas as pd
from utils import vectorize_recovery, plot_bar_chart

def visualize_recovery(scene_sept, scene_nov, scene_apr):
    # Bar charts
    for scene, date in [(scene_nov, '20241109'), (scene_apr, '20250423')]:
        gdf = vectorize_recovery(scene)
        plot_bar_chart(gdf, date)

    # Print pixel count
    print(f"ba_mask_filtered pixels={scene_sept['ba_mask_filtered'].sum().values}")

    # Folium map
    try:
        gdf_20241109 = gpd.read_file('data/output/classification/recovery_areas_20241109.geojson')
        gdf_20250423 = gpd.read_file('data/output/classification/recovery_areas_20250423.geojson')
    except Exception as e:
        print(f"Error loading shapefiles: {e}")
        exit()

    if gdf_20241109.crs != "EPSG:4326":
        gdf_20241109 = gdf_20241109.to_crs("EPSG:4326")
    if gdf_20250423.crs != "EPSG:4326":
        gdf_20250423 = gdf_20250423.to_crs("EPSG:4326")

    gdf_20241109 = gdf_20241109[gdf_20241109.geometry.is_valid]
    gdf_20250423 = gdf_20250423[gdf_20250423.geometry.is_valid]
    print(f"Valid features after filtering (2024-11-09): {len(gdf_20241109)}")
    print(f"Valid features after filtering (2025-04-23): {len(gdf_20250423)}")

    if len(gdf_20241109) == 0 or len(gdf_20250423) == 0:
        print("Error: One or both GeoDataFrames are empty after validation.")
        exit()

    gdf_20241109['recovery_20241109'] = gdf_20241109.get('recovery', 'unknown').astype(str).replace('nan', 'unknown')
    gdf_20250423['recovery_20250423'] = gdf_20250423.get('recovery', 'unknown').astype(str).replace('nan', 'unknown')

    colors = {
        'No Recovery': '#FF0000CC',
        'Moderate Recovery': '#FFFF00CC',
        'High Recovery': '#00FF00CC',
        'unknown': '#808080CC'
    }

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

    tooltip_nov = folium.GeoJsonTooltip(
        fields=["recovery_20241109"],
        aliases=["2024-11-09"],
        labels=True,
        sticky=True,
        localize=True,
        style="font-size: 14px; font-weight: bold;"
    )

    tooltip_apr = folium.GeoJsonTooltip(
        fields=["recovery_20250423"],
        aliases=["2025-04-23"],
        labels=True,
        sticky=True,
        localize=True,
        style="font-size: 14px; font-weight: bold;"
    )

    folium.GeoJson(
        gdf_20241109,
        style_function=style_nov,
        tooltip=tooltip_nov,
        name='Recovery 2024-11-09'
    ).add_to(m)

    folium.GeoJson(
        gdf_20250423,
        style_function=style_apr,
        tooltip=tooltip_apr,
        name='Recovery 2025-04-23'
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