import asyncio

import typer

app = typer.Typer()


@app.command("init-db")
def init_db():
    from app.commands import init_db

    asyncio.run(init_db())


@app.command("drop-db")
def drop_db():
    from app.commands import drop_db

    asyncio.run(drop_db())


if __name__ == "__main__":
    app()
