![Alt text](../img/tags/GAMECHANGER-NoPentagon_CMYK@3x.png)

# 

# GC Machine Learning API
## PROD
### Run ML API in PROD
1. be sure to have aws cli setup to pull dependencies
2. start FastAPI `. ./gamechangerml/api/fastapi/startFash.sh`  

## DEVELOPMENT
### Setup AWS configuration by exporting default profile
1. aws configure
2. this will allow you to get dependency models
### Build and Run ML API:
1. `. ./gamechangerml/setup_env.sh DEV` 
2. `cd gamechangerml/api`
3. `docker-compose build`
4. `docker-compose up`
5. check `http://localhost:5000/`
### Kubernetes Locally with Minikube
requires: docker, docker-compose, kubectl, minikube or other cluster
1. In gamechangerml/api/ update docker image with `docker-compose build`
2. if using minikube `minikube start`, optionally start dash with `minikube dashboard`
3. Make sure you have models in gamechangerml/models
4. mount your models with minikube mount /Users:/Users (must leave open)
5. in gamechangerml/api/kube, run `kubectl apply -f .`
6. go to open dashboard and check if pods are running
7. optionally run `kubeclt get pods` copy gamechanger-ml pod name,  `kubectl port-forward gamechanger-ml-gpu-****** 5000:5000` to expose the port locally and to be able to test.

