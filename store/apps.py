from django.apps import AppConfig
import os
import shutil
from PIL import Image

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from django.conf import settings
        
        # Create directories
        media_root = settings.MEDIA_ROOT
        product_images = os.path.join(media_root, 'product_images')
        os.makedirs(product_images, exist_ok=True)
        
        # Create default image
        default_image_path = os.path.join(media_root, 'default_image.jpg')
        if not os.path.exists(default_image_path):
            img = Image.new('RGB', (200, 200), color='gray')
            img.save(default_image_path)
