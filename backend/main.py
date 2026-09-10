from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "House Price Prediction API"}


# Task 1: 
def predict_price(area: float, bedrooms: int, location: str) -> float:
    base_price = 500_000_000
    total = base_price + (15_000_000 * area) + (50_000_000 * bedrooms)
    
    loc_lower = location.lower()
    if loc_lower == "hanoi":
        total *= 1.3
    elif loc_lower == "hcmc":
        total *= 1.25
    
    # Làm tròn đến triệu VND gần nhất
    return round(total, -6)

# Task 2: 
@app.get("/predict")
def predict(area: float, bedrooms: int, location: str = "other"):
    price = predict_price(area, bedrooms, location)
    return {
        "area": area,
        "bedrooms": bedrooms,
        "location": location,
        "predicted_price": price
    }

# Task 6
class HouseInput(BaseModel):
    area: float
    bedrooms: int
    location: str = "other"

@app.post("/predict")
def predict_post(data: HouseInput):
    price = predict_price(data.area, data.bedrooms, data.location)
    return {
        "area": data.area,
        "bedrooms": data.bedrooms,
        "location": data.location,
        "predicted_price": price
    }

# Task 4: 
app.mount("/static", StaticFiles(directory="../frontend"), name="static")