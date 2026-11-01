# FastAPI Basics

FastAPI is a Python web framework for building APIs. It is based on standard Python type hints and supports automatic interactive API documentation. A FastAPI application is commonly created with `app = FastAPI()`. Routes are declared using decorators such as `@app.get("/items")` and `@app.post("/items")`.

Path operation functions can be synchronous (`def`) or asynchronous (`async def`). Use `async def` when calling awaitable libraries. FastAPI uses Pydantic models to validate request bodies and serialize response data. A model derived from `BaseModel` can define fields and constraints.

FastAPI exposes OpenAPI documentation by default. The Swagger UI is normally available at `/docs`, and ReDoc is normally available at `/redoc`. Run an application during development with Uvicorn, for example `uvicorn main:app --reload`.
