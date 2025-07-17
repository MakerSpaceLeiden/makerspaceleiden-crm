from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status


class AvatarIndexViewTests(TestCase):
    @patch("avatar.views.Robohash")
    def test_index_view_returns_png_response(self, mock_robohash):
        # Mock Robohash so we don't generate real images
        mock_img = MagicMock()
        mock_robohash.return_value.img = mock_img
        mock_robohash.return_value.assemble.return_value = None
        mock_img.save = MagicMock()

        response = self.client.get("/avatar/123")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("mugshot-123.png", response["Content-Disposition"])
        mock_robohash.assert_called_with("123")
        mock_img.save.assert_called_once()
