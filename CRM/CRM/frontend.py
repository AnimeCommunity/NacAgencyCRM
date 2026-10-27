import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404


def serve_frontend(request, path=""):
    root = Path(settings.FRONTEND_DIST_DIR).resolve()
    candidate = (root / path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise Http404("Ruta de frontend no válida.") from exc

    if candidate.is_dir() or not candidate.suffix:
        candidate = candidate / "index.html"

    if not candidate.is_file():
        requested = Path(path)
        page_payload_suffix = ".__PAGE__.txt"
        if (
            requested.name.startswith("__next.")
            and requested.name.endswith(page_payload_suffix)
        ):
            payload_dir_name = requested.name[: -len(page_payload_suffix)]
            payload_candidate = (
                root / requested.parent / payload_dir_name / "__PAGE__.txt"
            ).resolve()
            try:
                payload_candidate.relative_to(root)
            except ValueError as exc:
                raise Http404("Ruta de frontend no válida.") from exc
            if payload_candidate.is_file():
                candidate = payload_candidate

    if not candidate.is_file():
        raise Http404("Recurso de frontend no encontrado.")

    content_type, encoding = mimetypes.guess_type(candidate.name)
    response = FileResponse(
        candidate.open("rb"),
        content_type=content_type or "application/octet-stream",
    )
    if encoding:
        response.headers["Content-Encoding"] = encoding
    return response
