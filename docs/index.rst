fastapi-lazyrouter
==================

**fastapi-lazyrouter** improves the cold start of a FastAPI application that has hundreds of Pydantic models.

FastAPI scans all models at startup and Pydantic must generate a schema for each of them. This operation takes time, especially on nested and complex models. At some point, the loading time exceeds the allowed time for the host to start the application. For example, on AWS Lambda, the application must be able to start in less than 10 seconds.

fastapi-lazyrouter prevents FastAPI from scanning routes at startup by dynamically mounting routers as requests come in.

Key benefits:

* startup time reduced by up to 3x
* minimal overhead on the first requests since only the used routers are loaded
* import strategy is preserved
* minimally intrusive
* API documentation loading is preserved: the first request to ``/docs`` or ``/openapi.json`` will take longer because all routers need to be loaded


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   usage
   api
   architecture

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
