from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.api import router

app = FastAPI(
    title="Technical Documentation Assistant",
    description="A self-corrective RAG assistant powered by LangGraph, ChromaDB, Groq and FastAPI.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
def root():
    return {"message": "Technical Documentation Assistant API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["openapi"] = "3.0.3"

    components = schema.get("components", {}).get("schemas", {})

    for component in components.values():
        properties = component.get("properties", {})

        for prop in properties.values():

            if prop.get("type") == "array":
                items = prop.get("items", {})

                if items.get("contentMediaType"):
                    items.pop("contentMediaType", None)
                    items["format"] = "binary"

            if prop.get("contentMediaType"):
                prop.pop("contentMediaType", None)
                prop["format"] = "binary"

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
