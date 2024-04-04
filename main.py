# Standard library imports
import base64
import os
import io

# Third-party imports
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import unquote
import torch

# Local application imports
from diffusers import StableDiffusionPipeline
from renderhtml import database_failure_error, not_found_error, process_img_to_full_pixel, render_html_block, render_main_display, render_specific_image_html



#####################
# SETUP STARTS HERE #
#####################

# While it's not exactly good practice to throw this all into a big pile, it's more readable for review if I can walk you through it step by step. So I will.
print("Starting the Flask app...")
print("Warning!! On first startup, this may be slow as the model is loaded into memory. Subsequent startups will be faster.")
app = Flask(__name__) # The core of things! Never delete this!





# Here, we'll connect to the DB! However, connecting to the DB is optional, or at least gracefully handled -- but we should alert the user!
try:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('LUCRA_AI_QUERIES_DATABASE_URI') # Make sure this is set in your environment!
    if app.config['SQLALCHEMY_DATABASE_URI'] is not None:
        db = SQLAlchemy(app) # Ideal state. We have a DB!
        dbexists = True
    else:
        print("Your environment doesn't have LUCRA_AI_QUERIES_DATABASE_URI set! Please set that to point it at the database.") # Informing the user...
except Exception as e:
    print("Database not found. Running without database.") # The user has a URI but no database here, most likely.
    print(f"Error: {e}")
    print("Is your URI correct, and MySQL started?")
    dbexists = False

# This is the model for the database. It's a simple key-value store, with the key being the text and the value being the image.
class AIImageQueryRecord(db.Model):
    text = db.Column(db.String(500), primary_key=True) # The text is unique!
    image = db.Column(db.LargeBinary(length=2**24-1), nullable=False)
    # Wouldn't it be nice to have timestamps and voting? Future feature.

# Here, we'll configure the DB, if it's not already configured.
if dbexists:
    with app.app_context():
        try:
            db.create_all()
        except:
            print("Database was precluded in some way.")
            print("\033[91mThe database may have become corrupted, or you may be pointing at a database that has another application's data!\033[0m")
            print("Defaulting to no database.")
            dbexists = False

# And that's it for Flask and the DB.
        



# Now we need to set up the model.

messages = [] # HTML strings of images and their color palettes
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

# And that's the model set up.

###################
# SETUP ENDS HERE #
###################


# Set up the frontend. This is the chat-like interface, even though it's not really a chat. And yes, it reloads the page when you submit, technically.
# We don't need a distinct post frontend. I could make this not refresh using react and such, but this is primarily a flask/AI/DB take-home project.
# So if the stakeholders don't want it too fancy, I should keep in mind the unspoken interest they might have in simplicity or maintainability.
# If that's not the case, it wouldn't be too hard to reactify it later.
@app.route('/', methods=['GET', 'POST'])
def render_chat():
    if request.method == 'POST':
        text = request.form.get('text')
        
        image = create_image(text)
        messages.append(image)
    return render_main_display(messages, cudawarning)

# This is the endpoint for the cached images. Permalinks, and more details for the image!
@app.route('/cachedimages/<string:text>', methods=['GET'])
def render_cached_image(text):
    text = unquote(text) # The text was formatted for the URL earlier.
    if dbexists:
        image_record = AIImageQueryRecord.query.get(text) # Retrieve the old data.
        if image_record is not None:
            return render_specific_image_html(image_record) # Render it to the client
        else:
            return not_found_error(), 404 # Uh oh! Nothing there. Make a 404 page.
    else:
        return database_failure_error(), 500 # Database failure! Make a 500 page.






def create_image(text: str): # Doesn't just create, it also retrieves from the cahce -- if able.
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

def create_or_retrieve_cached_image(text):
    old_query = None
    if (dbexists):
        old_query = AIImageQueryRecord.query.get(text)
    if old_query is not None:
        image = Image.open(io.BytesIO(old_query.image))
    else:
        image = generate_image_from_text(text)
        new_entry_arr = io.BytesIO()
        image.save(new_entry_arr, format='PNG')
        new_entry_arr.seek(0)
        db.session.add(AIImageQueryRecord(text=text, image=new_entry_arr.read()))
        db.session.commit()
    return image

def generate_image_from_text(text):
    return pipe(text).images[0]

if __name__ == '__main__':
    app.run(debug=True)