import asyncio
from contextlib import asynccontextmanager

import typer

from app.models import database

app = typer.Typer()


@asynccontextmanager
async def database_context():
    await database.connect()
    try:
        yield
    finally:
        await database.disconnect()


@app.command("init-db")
def init_db():
    from app.commands import init_db

    async def _init_db():
        async with database_context():
            await init_db()

    asyncio.run(_init_db())


@app.command("drop-db")
def drop_db():
    from app.commands import drop_db

    async def _drop_db():
        async with database_context():
            await drop_db()

    asyncio.run(_drop_db())


if __name__ == "__main__":
    app()
