## fastapi-lazyrouter

[![ci](https://github.com/FabienArcellier/fastapi-lazyrouter/actions/workflows/main.yml/badge.svg)](https://github.com/FabienArcellier/fastapi-lazyrouter/actions/workflows/main.yml)

fastapi-lazyrouter improves the cold start of a FastAPI application that has hundreds of Pydantic models. FastAPI scans all models at startup and Pydantic must generate a schema for each of them. This operation takes time, especially on nested and complex models.

At some point, the loading time exceeds the allowed time for the host to start the application. For example, on AWS Lambda, the application must be able to start in less than 10 seconds.

fastapi-lazyrouter prevents FastAPI from scanning routes at startup by dynamically mounting routers as requests come in.

* startup time reduced by up to 3x
* minimal overhead on the first requests since only the used routers are loaded
* import strategy is preserved
* minimally intrusive
* API documentation loading is preserved: the first request to `/docs` or `/openapi.json` will take longer because all routers need to be loaded **(not implemented yet)**


## Getting started

```bash
pip install fastapi-lazyrouter
```

## The latest version

You can find the latest version to ...

```bash
git clone https://github.com/FabienArcellier/fastapi-lazyrouter.git
```

## Usage

### Auto (Recommended)

#### Configure Pydantic model

```python
from pydantic import BaseModel, ConfigDict

class CustomBaseModel(BaseModel):
    model_config = ConfigDict(defer_build=True)  # enable defer_build, otherwise there is no effect
```

#### Enable FastAPI router

```python
import fastapi
import fastapi_lazyrouter

app = fastapi.FastAPI()
fastapi_lazyrouter.autoconfigure(app)
```

### Manual usage

If you want to understand what is happening under the hood.

#### Configure Pydantic model

```python
from pydantic import BaseModel, ConfigDict

class CustomBaseModel(BaseModel):
    model_config = ConfigDict(defer_build=True)  # enable defer_build, otherwise there is no effect
```

#### Replace ApiRouter with LazyApiRouter

```python
from fastapi_lazyrouter import LazyApiRouter

router = LazyApiRouter(prefix="/items")

@router.get("/")
def list_items():
    return []
```

#### Add middleware to FastAPI

```python
from fastapi import FastAPI
from fastapi_lazyrouter import LazyApiRouterMiddleware

app = FastAPI()
app.add_middleware(LazyApiRouterMiddleware)
```

### Publish the library on pypi

The publication use a tag-based workflow to run the publication on github action. First, a developper tag a commit using `alfred publish`, then github action publish the library on pypi.

The `alfred publish` take the version number from pyproject.toml. The command will raise an error if the current branch is not master, if changes are in progress, or if the tag already exists, if the branch is not synchronized with remote branch

```bash
alfred publish
```

### Run in gitpod

[gitpod](https://www.gitpod.io/) can be used as an IDE. You can load the code inside to try the code.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/FabienArcellier/fastapi-lazyrouter)

## Developper guideline

### Add a dependency

``bash
poetry add requests
``
### Install development environment

Use make to instanciate a python virtual environment in ./venv and install the
python dependencies.

```bash
poetry install
```

### Update release dependencies

Use make to instanciate a python virtual environment in ./venv and freeze
dependencies version

```bash
poetry update update
```

### Activate the python environment

When you setup the requirements, a `venv` directory on python 3 is created.
To activate the venv, you have to execute :

```bash
source .venv/bin/activate
```

### Run the continuous integration process

Before commit or send a pull request, you have to execute `pylint` to check the syntax
of your code and run the unit tests to validate the behavior.

```bash
$ poetry run alfred ci
```

## Contributors

* Fabien Arcellier

## License

MIT License

Copyright (c) 2026-2026 Fabien Arcellier

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
