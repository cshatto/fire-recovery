from scripts import preprocess_data, classify_recovery, visualize_recovery
def main():
    mscn = preprocess_data()
    scene_sept, scene_nov, scene_apr = classify_recovery(mscn)
    visualize_recovery(scene_sept, scene_nov, scene_apr)

if __name__ == "__main__":
    main()