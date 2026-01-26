from django.test import TestCase, override_settings
from products.data_warehouse.backend.models.util import get_s3_url_pattern


class TestDataWarehouseUtil(TestCase):
    def test_get_s3_url_pattern_https_default(self):
        """Test that normal S3 domains default to HTTPS"""
        domain = "s3.amazonaws.com"
        path = "my-bucket/data"
        expected = "https://s3.amazonaws.com/my-bucket/data"
        
        with override_settings(USE_LOCAL_SETUP=False):
            self.assertEqual(get_s3_url_pattern(domain, path), expected)

    def test_get_s3_url_pattern_http_for_minio_keywords(self):
        """Test that domains containing minio/objectstorage use HTTP"""
        test_cases = [
            ("objectstorage:19000", "http://objectstorage:19000/bucket/data"),
            ("minio:9000", "http://minio:9000/bucket/data"),
            ("localhost:9000", "http://localhost:9000/bucket/data"),
            ("127.0.0.1:9000", "http://127.0.0.1:9000/bucket/data"),
        ]
        
        path = "bucket/data"
        with override_settings(USE_LOCAL_SETUP=False):
            for domain, expected in test_cases:
                self.assertEqual(get_s3_url_pattern(domain, path), expected)

    def test_get_s3_url_pattern_force_http_local_setup(self):
        """Test that USE_LOCAL_SETUP forces HTTP regardless of domain"""
        domain = "s3.amazonaws.com"
        path = "bucket/data"
        expected = "http://s3.amazonaws.com/bucket/data"
        
        with override_settings(USE_LOCAL_SETUP=True):
            self.assertEqual(get_s3_url_pattern(domain, path), expected)

    def test_get_s3_url_pattern_path_handling(self):
        """Test that leading slashes in path are handled correctly"""
        domain = "s3.amazonaws.com"
        path = "/bucket/data"  # Leading slash
        expected = "https://s3.amazonaws.com/bucket/data"
        
        with override_settings(USE_LOCAL_SETUP=False):
            self.assertEqual(get_s3_url_pattern(domain, path), expected)

    def test_get_s3_url_pattern_case_insensitive(self):
        """Test that domain keyword detection is case-insensitive"""
        test_cases = [
            ("ObjectStorage:19000", "http://ObjectStorage:19000/bucket/data"),
            ("MiNiO:9000", "http://MiNiO:9000/bucket/data"),
        ]
        
        path = "bucket/data"
        with override_settings(USE_LOCAL_SETUP=False):
            for domain, expected in test_cases:
                self.assertEqual(get_s3_url_pattern(domain, path), expected)
