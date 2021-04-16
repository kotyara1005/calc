from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, condecimal, conint, constr


class BaseResponse(BaseModel):
    success: bool
    errors: Optional[list]
    result: Optional[dict]


class PriceRequest(BaseModel):
    amount: conint(gt=0, strict=True)
    price_for_one: condecimal(gt=Decimal(0), max_digits=30, decimal_places=2)
    state_code: constr(min_length=1)
