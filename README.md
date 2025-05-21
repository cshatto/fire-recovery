### Fire Recovery Tool 
This README provides simple steps to run the fire-recovery Docker image and access its directories. 
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
If fire-recovery is in a registry (e.g., Docker Hub), pull it:
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
docker run -d -it --name fire-recovery-container -v ~/ot-recovery:/fire-recovery fire-recovery
```
Windows Users: Use -v C:\Users\{USER}\ot-recovery:/fire-recovery.


Check that the container is running:
```
docker ps
```

#### 4. Copy Directories
I'd like for you to be able to explore the code straightaway, a nice way to do that is to copy the docker volume directory directly to your local volume. 
```
docker cp fire-recovery-container:/fire-recovery ~/ot-recovery
```
From here, you should be able to set up your local environment to run the full project.


#### 5. Set up your local environment
```
cd ot-recovery/fire-recovery
python3 -m venv venv
pip install -r requirements.txt
source venv/bin/activate
```

### 6. Check Output
The script (main.py) should now run, writing output to your local test/fire-recovery directory. It should take 1-2 minutes depending on your machine.
```
python3 scripts/main.py
```

Check your local directory:
```
ls ~/test/fire-recovery
```

Navigate to the main output file which is the folium html map saved as 'recovery_map.html' and open it in your preferred browser. All vectors and geotiffs used in the creation of the html map are saved in the output/ folder.
