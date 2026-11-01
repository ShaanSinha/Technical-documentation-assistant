# FastAPI Request Validation

FastAPI uses Pydantic to parse and validate request data. Define a request body as a class inheriting from `pydantic.BaseModel`. Type annotations describe expected values. Pydantic can reject invalid values and return structured validation errors.

Use `Field` to configure constraints such as minimum length, maximum length, numeric bounds, descriptions, and regular-expression patterns. Query parameters and path parameters can also be validated using type annotations and validation helpers.

When request data fails validation, FastAPI returns an HTTP 422 Unprocessable Entity response by default. You can define exception handlers to customize error responses. Use `HTTPException` to return an intentional HTTP error from a path operation.
