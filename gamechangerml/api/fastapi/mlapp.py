import faulthandler
from fastapi import FastAPI

from gamechangerml.api.fastapi.routers import startup, search, controls
from gamechangerml.debug.debug_connector import debug_if_flagged

# start debugger if flagged
debug_if_flagged()

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
