from fastapi import APIRouter
from services.fix_order_details import fix_order_dates

router = APIRouter()

@router.post("/orders/{vendor_order_code}/fix-dates")
def fix_order_item_dates(vendor_order_code: str):
    vendor_order_code = vendor_order_code.strip()
    result = fix_order_dates(vendor_order_code, current_user="boulder\\lpraharsha")

    return {
        "order_id": vendor_order_code,
        "result": result
    }
