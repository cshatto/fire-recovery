### Fire Recovery Tool 
This README provides simple steps to run the fire-recovery Docker image and access its directories. The benefit of using docker here instead of just cloning the Github repository is that the Docker comes with preloaded Sentinel-2 SAFE data to work through the entire workflow. 
The image runs a script (main.py) that attempts to write to /fire-recovery, which causes an error unless a writable directory is mounted. 
We’ll use the local directory (~/ot-recovery) to store output files.

Prerequisites
Docker: Please install Docker from docker.com.

Ensure ~/ot-recovery exists and is empty (or a similar path, e.g., C:\Users\ {YourUsername}\ot-recovery on Windows).


#### 1. Make local directory
If not done so already.
```
mkdir -p ~/ot-recovery
```

#### 2. Pull the Image
fire-recovery Docker is in a registry (e.g., Docker Hub), pull it:
```
docker pull cshatto/fire-recovery:latest
```

Once pulled, verify it exists locally with:
```
docker images
```


#### 3. Run the Container
Run the container with a volume mount to make /fire-recovery writable and persist files to your local ~/ot-recovery directory:
```
docker run -d -p 8000:8000 cshatto/fire-recovery

```


Check that the container is running in the backgroound (-d):
```
docker ps
```

#### 4. Run main.py
```
docker exec -it <container_id> bash
python3 main.py

```

### 6. Check Output
The script (main.py) should now run, writing outputs to data/output/. It should take 1-2 minutes depending on your machine.
```
http://localhost:8000/data/output/classification/recovery_map.html

```


