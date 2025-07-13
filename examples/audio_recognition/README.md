# User Guide
## Proxy Issues
If you are running in a Linux environment, you need to configure a proxy to access GitHub.

Running on Mac:
```
sudo pip install proxy.py  
proxy --port 8420 --hostname 0.0.0.0
```

Running on Server:
```
# Running on codelab
# Remember to change the IP. First, check your IP, then run: proxy --port 8420 --hostname 0.0.0.0
export http_proxy=http://{your_ip}:8420
export https_proxy=https://{your_ip}:8420
```

## ModuleNotFoundError

```
cd {xxx}/audio_recognition
export PYTHONPATH={}/src
```