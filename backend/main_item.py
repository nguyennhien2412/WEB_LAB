from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

# Mount thư mục static
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# Route trả về giao diện trang chủ khi truy cập http://127.0.0.1:8000/
@app.get("/")
def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")

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


# GET ITEMS WITH FILTERING,SEARCHING AND SORTING
@app.get("/items", response_model=ItemListResponse)
def read_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, min_length=2),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    sort_by: str = Query("id", pattern="^(id|name|price)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
):
    # Filter items based on query parameters
    filtered_items = _items.copy()

    if min_price is not None:
        filtered_items = [it for it in filtered_items if it.price >= min_price]
    if max_price is not None:
        filtered_items = [it for it in filtered_items if it.price <= max_price]

    if q is not None:
        filtered_items = [it for it in filtered_items if q.lower() in it.name.lower()]
    # Sort items
    filtered_items.sort(key=lambda x: getattr(x, sort_by), reverse=(sort_order == "desc"))

    total_count = len(filtered_items)

    paginated_items = filtered_items[skip : skip + limit]

    return ItemListResponse(
        items=paginated_items,
        total=total_count,
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
def update_item(item_id: int, data: ItemCreate):
    item = _find(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Item not found"})

    if data.name.lower() != item.name.lower():
        for eit in _items:
            if eit.name.lower() == data.name.lower() and eit.id != item_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Item name already exists"})
    # update
    updateValue = ItemPublic(name=data.name, price=data.price, id=item.id)
    index = _items.index(item)
    _items[index] = updateValue

    return updateValue

#UPDATE AN ITEM PARTIALLY (PATCH)
@app.patch("/items/{item_id}", response_model=ItemPublic)
def patch_item(item_id: int, data: ItemUpdate):
    item = _find(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Item not found"})

    if data.name is not None and data.name.lower() != item.name.lower():
        for eit in _items:
            if eit.name.lower() == data.name.lower() and eit.id != item_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Item name already exists"})

    # update
    update_data = data.model_dump(exclude_unset=True)
    item_dict = item.model_dump()
    item_dict.update(update_data)

    updated_item = ItemPublic(**item_dict)
    index = _items.index(item)
    _items[index] = updated_item

    return updated_item

# DELETE AN ITEM
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    item = _find(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Item not found"})

    _items.remove(item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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