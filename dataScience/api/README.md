![Alt text](../img/tags/GAMECHANGER-NoPentagon_CMYK@3x.png)

# 

# GC Machine Learning API
## PROD
### Run ML API in PROD
1. be sure to have aws cli setup to pull dependencies
2. start FastAPI `. ./dataScience/api/fastapi/startFash.sh`  

## DEVELOPMENT
### Setup AWS configuration by exporting default profile
1. aws configure
2. this will allow you to get dependency models
### Build and Run ML API:
1. `. ./dataScience/setup_env.sh DEV` 
2. `cd dataScience/api`
3. `docker-compose build`
4. `docker-compose up`
5. check `http://localhost:5000/`

