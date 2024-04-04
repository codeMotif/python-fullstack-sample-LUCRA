import base64
import io
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import torch

from renderhtml import process_img_to_full_pixel, render_html_block
from diffusers import StableDiffusionPipeline


pipe = None
cudawarning = False
app = None


def init(main_app: Flask):
    global pipe, cudawarning, app, create_or_retrieve_cached_image
    app = main_app
    
    # Not the best model, but that's easier to change later.
    cudawarning = False
    if torch.cuda.is_available(): # If we're on CUDA, we go faster.
        pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16) # This loads a stable diffusion model.
        pipe = pipe.to("cuda") # It's a big model! Please use this.
    else:
        cudawarning = True
        print("CUDA not available. Running on CPU.")
        print("\033[91mIt's strongly recommended that you quit this program and re-run it on a machine with a GPU and CUDA drivers.\033[0m")
        pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
        pipe = pipe.to("cpu") # Please don't run this on a conventional laptop. Please.
        # This is the model for the database. It's a simple key-value store, with the key being the text and the value being the image.
    from db_utils import create_or_retrieve_cached_image

def create_image(text: str, dbexists: bool): # Doesn't just create, it also retrieves from the cahce -- if able.
    text = text.strip().lower()    
    try:
        image = create_or_retrieve_cached_image(text) # Here's where it tries. This will throw an SQL error if the DB is down or otherwise a problem.
    except SQLAlchemyError as e:
        # This should have real logging in production.
        print(f"Database error: {e}")
        image = generate_image_from_text(text) # Default to more basic functionality.
    except Exception as e:
        raise e
    byte_arr = io.BytesIO()
    image = process_img_to_full_pixel(image) # This logic turns it from a basic AI-gen image to something that's more pixel-inspiration.
    image.save(byte_arr, format='PNG') # Need a byte array if I'm going to base64 it for HTML.
    encoded_image = base64.encodebytes(byte_arr.getvalue()).decode('ascii')
    image_html = render_html_block(text, encoded_image, image, dbexists) # Render the HTML that it'll use. It's a whole summary/details block.
    return image_html



def generate_image_from_text(text):
    return pipe(text).images[0]
