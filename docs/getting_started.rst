Getting started
###############

Installation
============

Install ``fastapi-lazyrouter`` from PyPI:

.. code-block:: bash

   pip install fastapi-lazyrouter

Prerequisites
=============

* Python 3.10 or higher
* FastAPI 0.119.0 or higher (first version that supports Pydantic v2)

Quick start
===========

The fastest way to get started is to use the **auto** configuration.

1. Configure your Pydantic base model to defer schema building:

.. code-block:: python

   from pydantic import BaseModel, ConfigDict

   class CustomBaseModel(BaseModel):
       model_config = ConfigDict(defer_build=True)

2. Enable lazy routing on your FastAPI application:

.. code-block:: python

   import fastapi
   import fastapi_lazyrouter

   app = fastapi.FastAPI()
   fastapi_lazyrouter.autoconfigure(app)

That's it! Your routes will now be mounted lazily on the first matching request.

Development version
===================

If you want to work with the latest development version, clone the repository:

.. code-block:: bash

   git clone https://github.com/FabienArcellier/fastapi-lazyrouter.git
   cd fastapi-lazyrouter
   poetry install
