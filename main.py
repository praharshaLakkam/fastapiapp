from fastapi import FastAPI
from routers import intent, status,fix_order

app = FastAPI()

app.include_router(intent.router, prefix="/intent", tags=["Intent Detection"])
app.include_router(status.router, prefix="/status", tags=["Order Status"])
app.include_router(fix_order.router,tags=["order_fix"])
