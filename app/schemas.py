from decimal import Decimal
from typing import Optional, Union

from pydantic import BaseModel, validator


class BaseResponse(BaseModel):
    success: bool
    errors: Optional[list]
    result: Optional[dict]


def greater_then_zero(value: Union[int, Decimal]):
    if value <= 0:
        raise ValueError("value should be greater then zero")
    return value


class PriceRequest(BaseModel):
    amount: int  # TODO positive
    price_for_one: Decimal
    state_code: str

    _amount_validator = validator("amount", allow_reuse=True)(
        greater_then_zero
    )
    _price_for_one_validator = validator("price_for_one", allow_reuse=True)(
        greater_then_zero
    )
