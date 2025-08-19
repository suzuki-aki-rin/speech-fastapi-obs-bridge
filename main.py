"""Main module for FastAPI app.

Examples:
    python main.py
"""

from pathlib import Path

import uvicorn

# from bot import Bot
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.router import router as fastapi_router
from logging_config import LOGGING_CONFIG


app = FastAPI()
# bot = Bot()
# set_bot(bot)
app.include_router(fastapi_router)

# set static directory
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Bot code
# async def start_fastapi():
#     config = uvicorn.Config(app, host="0.0.0.0", port=8000)
#     server = uvicorn.Server(config)
#     await server.serve()
#
#
# async def main():
#     await asyncio.gather(start_fastapi(), bot.start())


if __name__ == "__main__":
    # asyncio.run(main())
    uvicorn.run(
        "main:app", port=8000, reload=True, log_config=LOGGING_CONFIG, log_level="info"
    )
