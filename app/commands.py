import csv

from app.models import database


async def is_empty_db() -> bool:
    row = await database.fetch_one("SELECT 1 FROM state_tax LIMIT 1")
    if row:
        return False
    row = await database.fetch_one("SELECT 1 FROM discount LIMIT 1")
    if row:
        return False
    return True


async def init_db():
    if not await is_empty_db():
        print("table is not empty")
        return

    await database.execute_many(
        "INSERT INTO state_tax(state_code, tax_rate) VALUES (:state_code, :tax_rate)",
        list(csv.DictReader(open("etc/state_tax.csv"))),
    )

    await database.execute_many(
        "INSERT INTO discount(min_price, discount) VALUES (:min_price, :discount)",
        list(csv.DictReader(open("etc/discount.csv"))),
    )


async def drop_db():
    await database.execute("TRUNCATE TABLE state_tax RESTART IDENTITY",)
    await database.execute("TRUNCATE TABLE discount RESTART IDENTITY",)
