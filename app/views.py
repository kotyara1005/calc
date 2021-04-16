from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from app.models import Discount, StateTax
from app.schemas import BaseResponse, PriceRequest
from app.settings import DEFAULT_DISCOUNT

router = APIRouter()


@router.get("/states")
async def get_states():
    state_codes = await StateTax.get_all_state_codes()
    return BaseResponse(
        success=True, errors=[], result={"state_codes": state_codes}
    )


@router.post("/total_price")
async def compute_total_price(request: PriceRequest):
    state_tax = await StateTax.get_by_state(request.state_code)
    if state_tax is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid state code",
        )

    price = request.amount * request.price_for_one
    discount = await Discount.get_by_price(price)
    if discount:
        discount_value = price * discount.discount
    else:
        discount_value = price * DEFAULT_DISCOUNT

    price_with_discount = price - discount_value
    taxes = price_with_discount * state_tax.tax_rate
    total = price_with_discount + taxes

    return BaseResponse(
        success=True,
        errors=[],
        result={
            "price_info": {
                "price": price,
                "discount_value": discount_value,
                "price_with_discount": price_with_discount,
                "taxes": taxes,
                "total_price": total,
            },
            "discount": discount,
            "state_tax": state_tax,
        },
    )
