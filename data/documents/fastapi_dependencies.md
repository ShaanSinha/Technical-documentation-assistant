# FastAPI Dependencies and Error Handling

Dependency injection in FastAPI is declared with `Depends`. A dependency is a callable whose result is provided to a path operation or another dependency. Dependencies can be used for shared logic such as authentication, database sessions, and common query parameters.

Raise `fastapi.HTTPException` when an endpoint needs to stop processing and return an HTTP error. The exception accepts a status code and detail value. FastAPI converts it into an HTTP response. For application-wide custom behavior, register exception handlers with the application.

Middleware runs for requests and responses. Middleware can be used for cross-cutting concerns such as request timing, CORS, and logging. CORS middleware can be configured with allowed origins, methods, and headers.
