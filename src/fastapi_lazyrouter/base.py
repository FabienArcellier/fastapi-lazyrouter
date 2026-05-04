"""LazyApiRouter implementation for FastAPI.

This module provides a drop-in replacement for ``fastapi.APIRouter`` that defers
the registration of its routes into a ``FastAPI`` application until the first
HTTP request whose path matches the router's prefix is received.

Usage:
    Replace ``from fastapi import APIRouter`` with
    ``from app3.router.base import LazyApiRouter`` in your route modules.

    ``LazyApiRouter`` is instantiated with ``prefix`` (required).  The
    router is created immediately but its routes are *not* mounted into the
    application.  A middleware detects incoming requests and performs the
    ``app.include_router()`` call on first match.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Set, Union, Type, Sequence
from enum import Enum

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute, BaseRoute
from fastapi.types import IncEx
from fastapi import params
from fastapi.datastructures import DefaultPlaceholder, Default
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_ALL_LAZY_ROUTERS: List['LazyApiRouter'] = []


def autoconfigure(app: FastAPI) -> None:
    """
    Configure the FastAPI application to support lazy routers.

    This is called automatically by patch_apirouter() but can be called
    directly if you prefer to patch APIRouter manually.
    """
    # Add middleware if not already present
    middleware_classes = [m.cls for m in app.user_middleware]
    if LazyApiRouterMiddleware not in middleware_classes:
        app.add_middleware(LazyApiRouterMiddleware)

    _original_include_router = app.include_router

    def _patched_include_router(
        router: APIRouter,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if isinstance(router, APIRouter) and not isinstance(router, LazyApiRouter):
            lazy_router = LazyApiRouter(
                prefix=router.prefix,
                tags=router.tags,
                dependencies=router.dependencies,
                default_response_class=router.default_response_class,
                responses=router.responses,
                callbacks=router.callbacks,
                routes=router.routes,
                redirect_slashes=router.redirect_slashes,
                default=router.default,
                dependency_overrides_provider=router.dependency_overrides_provider,
                route_class=router.route_class,
                on_startup=router.on_startup,
                on_shutdown=router.on_shutdown,
                deprecated=router.deprecated,
                include_in_schema=router.include_in_schema,
                generate_unique_id_function=router.generate_unique_id_function,
            )
            router = lazy_router

        _original_include_router(router, *args, **kwargs)

    setattr(app, 'include_router', _patched_include_router)


class LazyApiRouter(APIRouter):
    """
    Router whose routes are mounted lazily on first matching request.

    ``LazyApiRouter`` inherits from ``APIRouter`` so it can be used as a
    drop-in replacement in every route module.  Routes are declared normally
    (``@router.get(...)`` etc.).

    When ``app.include_router(lazy_router)`` is
    called, the router stores a reference to the application and its own
    configuration but **does not register its routes yet**.

    The routes are
    mounted only when the global middleware sees a request whose path starts
    with the router's ``prefix``.
    """

    _all_lazy_routers: List['LazyApiRouter'] = []

    def __init__(self, prefix: str = '', **kwargs: Any) -> None:
        self._lazy_prefix: str = prefix
        self._lazy_app: Optional[FastAPI] = None
        self._lazy_loaded = False
        self._deferred_routes: list[dict] = []
        super().__init__(prefix=prefix, **kwargs)
        _ALL_LAZY_ROUTERS.append(self)

    # ------------------------------------------------------------------
    # Intercept route registration so that routes are stored instead of
    # being added to the internal router immediately.
    # ------------------------------------------------------------------

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = 'Successful Response',
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[IncEx] = None,
        response_model_exclude: Optional[IncEx] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
        name: Optional[str] = None,
        route_class_override: Optional[Type[APIRoute]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Optional[Union[Callable[[APIRoute], str], DefaultPlaceholder]] = Default(None),
    ) -> None:
        self._deferred_routes.append(
            {
                'path': path,
                'endpoint': endpoint,
                'response_model': response_model,
                'status_code': status_code,
                'tags': tags,
                'dependencies': dependencies,
                'summary': summary,
                'description': description,
                'response_description': response_description,
                'responses': responses,
                'deprecated': deprecated,
                'methods': methods,
                'operation_id': operation_id,
                'response_model_include': response_model_include,
                'response_model_exclude': response_model_exclude,
                'response_model_by_alias': response_model_by_alias,
                'response_model_exclude_unset': response_model_exclude_unset,
                'response_model_exclude_defaults': response_model_exclude_defaults,
                'response_model_exclude_none': response_model_exclude_none,
                'include_in_schema': include_in_schema,
                'response_class': response_class,
                'name': name,
                'callbacks': callbacks,
                'openapi_extra': openapi_extra,
                'generate_unique_id_function': generate_unique_id_function,
            }
        )

    def _apply_routes(self) -> None:
        """Actually register all deferred routes onto the internal APIRouter."""
        for kwargs in self._deferred_routes:
            super().add_api_route(**kwargs)
        self._deferred_routes.clear()

    # ------------------------------------------------------------------
    # Called by the middleware when it is time to really mount the routes
    # ------------------------------------------------------------------

    def _lazy_mount(self, app: FastAPI) -> bool:
        """Mount this router's routes into *app* if not already done.

        Returns ``True`` if the mount actually happened.
        """
        if self._lazy_loaded:
            return False
        logger.info('Lazy-mounting router with prefix %s', self._lazy_prefix)
        self._apply_routes()
        app.include_router(self)
        self._lazy_loaded = True
        return True

    @classmethod
    def reset_registry(cls) -> None:
        """Clear the global router registry (useful for testing)."""
        _ALL_LAZY_ROUTERS.clear()


class LazyApiRouterMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that lazily mounts ``LazyApiRouter`` routes on first use.

    Add it to the FastAPI application **before** any other middleware that may
    need routing information::

    >>> app.add_middleware(LazyApiRouterMiddleware)
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        # Keep a set of prefixes already loaded to avoid repeated work
        self._loaded_prefixes: Set[str] = set()

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        path = request.url.path
        for router in _ALL_LAZY_ROUTERS:
            if router._lazy_loaded:
                continue
            if path.startswith(router._lazy_prefix):
                # Ensure the FastAPI app is available on the router
                if router._lazy_app is None:
                    # Walk up to the FastAPI app from the request
                    router._lazy_app = request.app
                router._lazy_mount(router._lazy_app)
                break  # only one router per request can trigger first load
        return await call_next(request)
