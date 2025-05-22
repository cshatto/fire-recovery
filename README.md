### Fire Recovery Tool 
This README provides simple steps to run the fire-recovery Docker image and access its directories. The benefit of using docker here instead of just cloning the Github repository is that the Docker comes with preloaded Sentinel-2 SAFE data to work through the entire workflow. 
The image runs a script, main.py and returns an .html. All output data used in the creation of the html (geojson, geotiffs, etc.) are created and stored in the system volume. Outputs are also stored on GitHub for easy usage together with GIS software.



#### 1. Pull the Image
fire-recovery Docker is in a public registry (e.g., Docker Hub), pull it:
```
docker pull cshatto/fire-recovery:latest
```

Once pulled, verify it exists locally with:
```
docker images
```


#### 2. Run the Container
Running the Docker will expose it to a port 8000 so we include a flag (-p) in the run:
```
docker run -d -p 8000:8000 cshatto/fire-recovery

```


Check that the container is running in the backgroound and copy the container ID:
```
docker ps
```

#### 5. Run main.py
Enter container using the 'exec' command and the <container> id you copied in the previous step.
```
docker exec -it <container_id> bash
python3 main.py

```

### 6. Check Output
The script (main.py) should now run, writing outputs to data/output/. It should take 1-2 minutes depending on your machine. Open a new browser tab and past the 
```
http://localhost:8000/data/output/classification/recovery_map.html

```


