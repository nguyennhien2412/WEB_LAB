# Mini-House-Price-Prediction-API

## How to Run

1. Open the terminal inside the `backend/` directory and activate the virtual environment: `.venv\Scripts\Activate.ps1`.
2. Start the FastAPI application with the command: `uvicorn main:app --reload`.
3. Open your browser and navigate to: `http://127.0.0.1:8000/static/house_form.html`.

## Task Answers (Task 3 & 5)

- **Why calling `/predict` without `location` still works:** Because the `location` parameter is defined with a default value of `"other"` in the endpoint, FastAPI automatically uses this default value when it is missing.
- **Why calling `/predict` without `area` gives a 422 error:** Because `area` is a required parameter. When it is not provided, FastAPI validation fails and returns a `422 Unprocessable Entity` status code.
- **Why a relative URL works in Task 5:** Because both the frontend and the backend API run on the same origin (`127.0.0.1:8000`) thanks to the StaticFiles mount, allowing the relative URL (`/predict`) to target the correct endpoint without triggering CORS policy blocks.
