import os
from gamechangerml.api.fastapi.settings import logger

env_flag = "ENABLE_DEBUGGER"


def check_debug_flagged():
    flag_str = os.getenv(env_flag, "false")
    return flag_str == 'true'


def debug_if_flagged():

    if check_debug_flagged():
        try:
            import debugpy
            debugger_port = 5678
            debugpy.listen(('0.0.0.0', debugger_port))
            logger.info(f"\n Debugger listening on {debugger_port}  🥾🦟 \n")

            # debugpy.wait_for_client()
            # debugpy.breakpoint()
        except Exception as e:
            import time
            logger.warning("ERROR STARTING DEBUGGER CONNECTION")
            time.sleep(3)
            logger.warning(e)
            time.sleep(3)
            logger.info(
                f"Debugging can be turned off by removing env variable {env_flag}")
    else:
        logger.info("ENABLE_DEBUGGER not set, debugger not started")
