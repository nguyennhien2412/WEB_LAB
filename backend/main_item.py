from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Response, status, Request, Cookie, Depends, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import time
from typing import Generator
from starlette.middleware.sessions import SessionMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

# Mount thư mục static
# app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
        CORSMiddleware,
            allow_origins=["http://127.0.0.1:5500"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True
)

app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
    return response

@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        print(f"Unhandled error on { request.url.path}: {exc}")
        return JSONResponse( status_code=500,
                            content={"detail: " "Internal server error"}) 

def pagination(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return {"skip": skip, "limit": limit}

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "expected-secret":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return x_api_key

def get_session() -> Generator:
    print("--> [DB Session Setup]: Open database connection")
    session = {"db_connected": True}
    try:
        yield session
    finally:
        print("--> [DB Session Cleanup]: Close database connection")

def get_item_or_404(item_id: int) -> "ItemPublic":
    item = _find(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Item not found"})
    return item


class ItemCreate(BaseModel):
    name: str
    price: float


class ItemPublic(BaseModel):
    name: str
    id: int
    price: float

class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None

class ItemListResponse(BaseModel):
    items: list[ItemPublic]
    total: int
    skip: int
    limit: int

# PART E:
class HousePriceRequest(BaseModel):
    area_sqm: float = Field(..., gt=0, description="Diện tích (m2), phải > 0")
    bedrooms: int = Field(..., ge=0, description="Số phòng ngủ, phải >= 0")
    distance_to_center_km: float = Field(..., ge=0, description="Khoảng cách đến trung tâm (km)")

class HousePricePrediction(BaseModel):
    predicted_price: float
    currency: str = "VND"

_items: list[ItemPublic] = []
_next_id: int = 1
_cart = []

# Route trả về giao diện trang chủ khi truy cập http://127.0.0.1:8000/
@app.get("/")
def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/visits")
def count_visits(response: Response, visits: str | None = Cookie(default=None)):
    count = int(visits) if visits else 0
    count += 1
    response.set_cookie(key="visits", value=str(count), httponly=True, samesite="lax")
    return {"visits": count}

def _find(item_id: int) -> ItemPublic | None:
    for it in _items:
        if it.id == item_id:
            return it
    return None


#app = FastAPI()
#app.mount("/static", StaticFiles(directory="../frontend"), name="static")


@app.get("/items/me")
def read_me():
    return "Welcome!"


# GET AN ITEM
@app.get("/items/{item_id}", response_model=ItemPublic)
def read_item(item_id: int):
    item = _find(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Item not found"})

    return item

# GET ITEMS
@app.get("/items", response_model=ItemListResponse)
def read_items(
    page: dict = Depends(pagination),
    db: dict = Depends(get_session)
):
    skip = page["skip"]
    limit = page["limit"]
    paginated_items = _items[skip : skip + limit]
    return ItemListResponse(
        items=paginated_items,
        total=len(_items),
        skip=skip,
        limit=limit
    )

# GET ITEMS WITH FILTERING,SEARCHING AND SORTING
@app.get("/items/search", response_model=ItemListResponse)
def search_items(
    page: dict = Depends(pagination),
    q: str | None = Query(None, min_length=2),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    sort_by: str = Query("id", pattern="^(id|name|price)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$")
):
    filtered_items = _items.copy()

    if min_price is not None:
        filtered_items = [it for it in filtered_items if it.price >= min_price]
    if max_price is not None:
        filtered_items = [it for it in filtered_items if it.price <= max_price]
    if q is not None:
        filtered_items = [it for it in filtered_items if q.lower() in it.name.lower()]

    filtered_items.sort(key=lambda x: getattr(x, sort_by), reverse=(sort_order == "desc"))

    skip = page["skip"]
    limit = page["limit"]
    paginated_items = filtered_items[skip : skip + limit]

    return ItemListResponse(
        items=paginated_items,
        total=len(filtered_items),
        skip=skip,
        limit=limit
    )

# CREATE AN ITEM WITH VALIDATION
@app.post("/items", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate):
    global _next_id
    for it in _items:
        if it.name.lower() == data.name.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Item name already exists"})

    newItem = ItemPublic(name=data.name, id=_next_id, price=data.price)
    _items.append(newItem)
    _next_id += 1
    return newItem

# UPDATE AN ITEM 
@app.put("/items/{item_id}", response_model=ItemPublic)
def update_item(data: ItemCreate, item: ItemPublic = Depends(get_item_or_404)):
    if data.name.lower() != item.name.lower():
        for eit in _items:
            if eit.name.lower() == data.name.lower() and eit.id != item.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Item name already exists"})

    updateValue = ItemPublic(name=data.name, price=data.price, id=item.id)
    index = _items.index(item)
    _items[index] = updateValue
    return updateValue

#UPDATE AN ITEM PARTIALLY (PATCH)
@app.patch("/items/{item_id}", response_model=ItemPublic)
def patch_item(data: ItemUpdate, item: ItemPublic = Depends(get_item_or_404)):
    if data.name is not None and data.name.lower() != item.name.lower():
        for eit in _items:
            if eit.name.lower() == data.name.lower() and eit.id != item.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Item name already exists"})

    update_data = data.model_dump(exclude_unset=True)
    item_dict = item.model_dump()
    item_dict.update(update_data)

    updated_item = ItemPublic(**item_dict)
    index = _items.index(item)
    _items[index] = updated_item
    return updated_item

# DELETE AN ITEM
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item: ItemPublic = Depends(get_item_or_404)):
    _items.remove(item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/card/add")
def addCartItem(item: str):
    _cart.append(item)
    return item

@app.get("/card")
def getCart():
    print("--> Get card")
    return _cart

@app.get("/secure-data", dependencies=[Depends(verify_api_key)])
def secure_data():
    return {"ok": True, "message": "You accessed secure data using a valid API key!"}

@app.get("/set-session")
def set_session(request: Request):
    request.session["user_id"] = 42
    return {"status": "session set"}

# PART E: HOUSE PRICE PREDICTION ENDPOINT
@app.post("/predict/house-price", response_model=HousePricePrediction)
def predict_house_price(request: HousePriceRequest):
    price = (
        request.area_sqm * 15_000_000
        - request.distance_to_center_km * 5_000_000
        + request.bedrooms * 20_000_000
    )

    final_price = max(0.0, float(price))

    return HousePricePrediction(predicted_price=final_price, currency="VND")