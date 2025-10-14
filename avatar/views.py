import logging
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.signing import SignatureExpired, TimestampSigner
from django.http import Http404, HttpResponse
from django.views.decorators.cache import cache_control
from robohash import Robohash

from makerspaceleiden.decorators import login_or_bearer_required

logger = logging.getLogger(__name__)

DEFAULT_ROBOHASH_SET = "set1"
DEFAULT_ROBOHASH_COLOR = "red"
DEFAULT_CACHE_DIR = "avatar_cache"

# Get avatar settings
avatar_settings = getattr(settings, "AVATAR", {})

# Define the file path for caching
cache_dir = avatar_settings.get("CACHE_DIR", DEFAULT_CACHE_DIR)


def handleImage(pk):
    filename = f"mugshot-{pk}.png"
    file_path = os.path.join(cache_dir, filename)

    # Check if the image already exists in storage
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
            roboset=avatar_settings.get("ROBOHASH_SET", DEFAULT_ROBOHASH_SET),
            format="png",
            color=avatar_settings.get("ROBOHASH_COLOUR", DEFAULT_ROBOHASH_COLOR),
            bgset=None,
        )

        # Save image to BytesIO buffer
        img_buffer = BytesIO()
        rh.img.save(img_buffer, "PNG")
        img_bytes = img_buffer.getvalue()  # Get bytes once

        # Cache the image in storage
        try:
            default_storage.save(file_path, ContentFile(img_bytes))
            logger.info(f"Cached new robohash image: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cache robohash image {file_path}: {e}")

        # Return the response
        response = HttpResponse(img_bytes, content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Failed to generate robohash for pk {pk}: {e}")
        raise Http404("Unable to generate robohash image")


@login_or_bearer_required
@cache_control(max_age=86400)  # Cache for 24 hours in browser
def index(request, pk=None):
    if not pk:
        pk = uuid.uuid4().hex[:16]

    return handleImage(pk)


@login_or_bearer_required
def handle_signed_url(request, slug):
    ## Make this more generic
    signer = TimestampSigner()
    ## Signed URLs always have access
    try:
        unsigned = signer.unsign(request.path, max_age=3600)  # 1hr expiry
        ## Passing the unsigned URL to the function
        pk = unsigned
        return handleImage(pk)
    except SignatureExpired:
        raise Http404("Invalid or expired signed URL")
