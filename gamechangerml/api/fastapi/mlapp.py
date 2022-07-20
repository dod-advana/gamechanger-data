from fastapi import FastAPI
import faulthandler

from gamechangerml.api.fastapi.routers import startup, search, controls

# start API
app = FastAPI()
faulthandler.enable()

app.include_router(
    startup.router
)
app.include_router(
    search.router,
    tags=["Search"]
)
app.include_router(
    controls.router,
    tags=["API Controls"]
)
