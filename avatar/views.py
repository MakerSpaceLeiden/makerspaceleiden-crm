import logging
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse
from django.views.decorators.cache import cache_control
from robohash import Robohash

logger = logging.getLogger(__name__)


@cache_control(max_age=86400)  # Cache for 24 hours in browser
def index(request, pk=None):
    if not pk:
        pk = uuid.uuid4().hex[:16]

    # Get avatar settings
    avatar_settings = getattr(settings, "AVATAR", {})

    # Define the file path for caching
    cache_dir = avatar_settings.get("CACHE_DIR", "avatar_cache")
    filename = f"mugshot-{pk}.png"
    file_path = os.path.join(cache_dir, filename)

    # Check if the image already exists in storage
    print(file_path)
    if default_storage.exists(file_path):
        logger.info(f"Cached robohash image: {file_path}")
        try:
            # Serve the cached image
            with default_storage.open(file_path, "rb") as cached_file:
                response = HttpResponse(cached_file.read(), content_type="image/png")
                response["Content-Disposition"] = f'inline; filename="{filename}"'
                return response
        except Exception as e:
            logger.warning(f"Failed to read cached robohash {file_path}: {e}")
            # If reading fails, we'll regenerate below

    # Generate new robohash image
    try:
        rh = Robohash(str(pk))
        rh.assemble(
            roboset=avatar_settings.get("ROBOHASH_SET", "set1"),
            format="png",
            color=avatar_settings.get("ROBOHASH_COLOUR", None),
            bgset=None,
        )

        # Save image to BytesIO buffer
        img_buffer = BytesIO()
        rh.img.save(img_buffer, "PNG")
        img_buffer.seek(0)

        # Cache the image in storage
        try:
            default_storage.save(file_path, ContentFile(img_buffer.getvalue()))
            logger.info(f"Cached new robohash image: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cache robohash image {file_path}: {e}")

        # Return the response
        img_buffer.seek(0)
        response = HttpResponse(img_buffer.getvalue(), content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Failed to generate robohash for pk {pk}: {e}")
        raise Http404("Unable to generate robohash image")
