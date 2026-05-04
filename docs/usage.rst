Usage
#####

Auto configuration (recommended)
================================

The automatic configuration is the simplest way to enable lazy routing. It patches ``app.include_router`` so that every standard ``APIRouter`` is transparently converted into a ``LazyApiRouter``.

Step 1: defer Pydantic schema generation
----------------------------------------

Set ``defer_build=True`` in your Pydantic base model configuration. Without this step the schemas are still built eagerly and the cold-start improvement is lost.

.. code-block:: python

   from pydantic import BaseModel, ConfigDict

   class CustomBaseModel(BaseModel):
       model_config = ConfigDict(defer_build=True)

Step 2: enable lazy routers
---------------------------

Call :func:`fastapi_lazyrouter.autoconfigure` **before** you include any routers:

.. code-block:: python

   import fastapi
   import fastapi_lazyrouter

   app = fastapi.FastAPI()
   fastapi_lazyrouter.autoconfigure(app)

   # Continue with your normal router imports and app.include_router(...)

Manual configuration
====================

If you prefer to be explicit about which routers are lazy, you can use the manual setup.

Step 1: defer Pydantic schema generation
----------------------------------------

Same as in the auto configuration:

.. code-block:: python

   from pydantic import BaseModel, ConfigDict

   class CustomBaseModel(BaseModel):
       model_config = ConfigDict(defer_build=True)

Step 2: replace ``APIRouter`` with ``LazyApiRouter``
----------------------------------------------------

Import ``LazyApiRouter`` instead of ``APIRouter`` in your route modules:

.. code-block:: python

   from fastapi_lazyrouter import LazyApiRouter

   router = LazyApiRouter(prefix="/items")

   @router.get("/")
   def list_items():
       return []

Step 3: add the middleware
--------------------------

Register :class:`LazyApiRouterMiddleware` on your FastAPI application. The middleware must be added **before** any other middleware that relies on routing information.

.. code-block:: python

   from fastapi import FastAPI
   from fastapi_lazyrouter import LazyApiRouterMiddleware

   app = FastAPI()
   app.add_middleware(LazyApiRouterMiddleware)

   app.include_router(router)

What to expect at runtime
=========================

* **Cold start** – the application boots without scanning any lazy-router routes, so startup time is dramatically reduced.
* **First request** – when a request arrives whose path matches a lazy router prefix, the middleware triggers the mount. That request incurs a small one-time overhead for building the Pydantic schemas of that router only.
* **Subsequent requests** – the router is now a normal FastAPI router; all later requests are processed at full speed.
* **OpenAPI / docs** – the first call to ``/docs`` or ``/openapi.json`` may take longer because FastAPI needs to force-load every lazy router in order to generate the complete schema.
