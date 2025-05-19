from scripts.preprocessing import preprocess_data
from scripts.classification import classify_recovery
from scripts.visualization import visualize_recovery

def main():
    mscn = preprocess_data()
    scene_sept, scene_nov, scene_apr = classify_recovery(mscn)
    visualize_recovery(scene_sept, scene_nov, scene_apr)

if __name__ == "__main__":
    main()