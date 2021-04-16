from decimal import Decimal
from typing import List, Optional

import databases
from pydantic import BaseModel, condecimal

from app.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)

PositiveDecimal = condecimal(ge=Decimal(0), max_digits=30, decimal_places=7)


class StateTax(BaseModel):
    state_code: str
    tax_rate: PositiveDecimal

    @classmethod
    async def get_all_state_codes(cls) -> List[str]:
        codes = [
            row["state_code"]
            for row in await database.fetch_all(
                "SELECT state_code FROM state_tax"
            )
        ]
        return codes

    @classmethod
    async def get_by_state(cls, state_code: str) -> Optional["StateTax"]:
        row = await database.fetch_one(
            """
                SELECT state_code, tax_rate
                FROM state_tax
                WHERE state_code=:state_code
            """,
            dict(state_code=state_code),
        )
        if row is None:
            return None
        return StateTax(**row)


class Discount(BaseModel):
    min_price: PositiveDecimal
    discount: PositiveDecimal

    @classmethod
    async def get_by_price(cls, price: Decimal) -> Optional["Discount"]:
        row = await database.fetch_one(
            """
                SELECT min_price, discount
                FROM discount
                WHERE min_price<:price
                ORDER BY min_price DESC
                LIMIT 1
            """,
            dict(price=price),
        )
        if row is None:
            return None
        return Discount(**row)
