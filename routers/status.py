from fastapi import APIRouter
from services.sfdc_status import check_sfdc_order
from services.external_status import check_external_order_status
router = APIRouter()
@router.get("/orders/{vendor_order_code}")
def check_order_status(vendor_order_code: str):
    vendor_order_code=vendor_order_code.strip()
    if vendor_order_code.upper().startswith("SFDC"):
        result = check_sfdc_order(vendor_order_code)
        order_type = "sfdc"
    else:
        result = check_external_order_status(vendor_order_code)
        order_type = "external"

    return {
        "order_type": order_type,
        "order_id": vendor_order_code,
        "result": result
    }
