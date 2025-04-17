import os
import secrets
from flask import current_app as app
from PIL import Image

def save_picture(form_picture):
    filename_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    hex_filename = filename_hex + file_ext
    full_hex_filename = os.path.join(app.root_path, 'static/profile_pics', hex_filename)

    image_size = (125, 125)
    image = Image.open(form_picture)
    image.thumbnail(image_size)
    image.save(full_hex_filename)

    return hex_filename