Architecture
############

This page explains how ``fastapi-lazyrouter`` works under the hood.

The cold-start problem
======================

FastAPI builds an OpenAPI schema for every route at import time. When a route declares Pydantic response models, Pydantic must generate the JSON schema for those models. If your application contains hundreds of nested models, this process can take several seconds.

On serverless platforms such as AWS Lambda the runtime kills the container if it does not respond to health checks within ~10 seconds. A large FastAPI application can therefore fail to cold-start.

Lazy router principle
=====================

``fastapi-lazyrouter`` splits the work into two phases:

1. **Declaration phase** (import time) – route decorators such as ``@router.get(...)`` are intercepted. The arguments are stored in an internal list instead of being registered on the underlying ``APIRouter`` immediately. Because the routes are never added to the router, FastAPI has no models to scan and Pydantic does no work.

2. **Mount phase** (first request) – the :class:`LazyApiRouterMiddleware` inspects every incoming request. When the request path starts with a lazy router's prefix, the middleware calls :meth:`LazyApiRouter._lazy_mount`, which:

   * iterates over the stored route declarations,
   * calls the real ``APIRouter.add_api_route`` for each one,
   * calls ``app.include_router(self)`` so that FastAPI finally sees the routes,
   * marks the router as loaded so that the operation happens only once.

Global registry
===============

Every ``LazyApiRouter`` instance appends itself to the module-level list ``_ALL_LAZY_ROUTERS``. The middleware loops over this list on each request to find routers whose prefix matches the current path. The registry can be cleared with :meth:`LazyApiRouter.reset_registry`, which is useful in test suites that create many application instances.

Auto-configuration
==================

:func:`autoconfigure` makes the library almost transparent:

1. It adds :class:`LazyApiRouterMiddleware` to the FastAPI app if it is not already present.
2. It monkey-patches ``app.include_router`` with a wrapper that converts plain ``APIRouter`` instances into ``LazyApiRouter`` instances before delegating to the original method.

After this patch you can keep using ``APIRouter`` in your code and still benefit from lazy loading.

Limitations and trade-offs
==========================

* **First-request latency** – the very first request that hits a lazy router pays the cost of schema generation. In practice this is usually acceptable because only the router that is actually used is loaded.
* **OpenAPI completeness** – ``/docs`` and ``/openapi.json`` force FastAPI to enumerate all routes. The first request to those endpoints therefore triggers the mount of *every* lazy router, negating the cold-start benefit for that specific request.
* **Middleware ordering** – :class:`LazyApiRouterMiddleware` should be the outermost middleware so that routing-dependent middlewares (e.g. authentication, CORS) operate on fully-mounted routes.
