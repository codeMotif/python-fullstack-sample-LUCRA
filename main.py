from flask import Flask, request
from urllib.parse import unquote


#####################
# SETUP STARTS HERE #
#####################

# While it's not exactly good practice to throw this all into a big pile, it's more readable for review if I can walk you through it step by step. So I will.
print("Starting the Flask app...")
print("Warning!! On first startup, this may be slow as the model is loaded into memory. Subsequent startups will be faster.")
app = Flask(__name__) # The core of things! Never delete this!

# Gotta set up the utils. This is the model and the database.
import db_utils
db_utils.init(app)
from db_utils import AIImageQueryRecord, dbexists

# And the image utils. This is the image generation and processing.
import image_utils
image_utils.init(app)

# And the HTML rendering utils. This is the frontend.
import html_rendering_utils

# And that's everything set up.

###################
# SETUP ENDS HERE #
###################


messages = [] # HTML strings of images and their color palettes

# Set up the frontend. This is the chat-like interface, even though it's not really a chat. And yes, it reloads the page when you submit, technically.
# We don't need a distinct post frontend. I could make this not refresh using react and such, but this is primarily a flask/AI/DB take-home project.
# So if the stakeholders don't want it too fancy, I should keep in mind the unspoken interest they might have in simplicity or maintainability.
# If that's not the case, it wouldn't be too hard to reactify it later.
@app.route('/', methods=['GET', 'POST'])
def render_chat():
    if request.method == 'POST':
        text = request.form.get('text')
        image = image_utils.create_image(text, dbexists)
        messages.append(image)
    return html_rendering_utils.render_main_display(messages, image_utils.cudawarning)

# This is the endpoint for the cached images. Permalinks, and more details for the image!
@app.route('/cachedimages/<string:text>', methods=['GET'])
def render_cached_image(text):
    text = unquote(text)
    if dbexists:
        image_record = AIImageQueryRecord.query.get(text) # Retrieve the old data.
        if image_record is not None:
            return html_rendering_utils.render_specific_image_html(image_record) # Render it to the client
        else:
            return html_rendering_utils.not_found_error(), 404 # Uh oh! Nothing there. Make a 404 page.
    else:
        return html_rendering_utils.database_failure_error(), 500 # Database failure! Make a 500 page.

# User feedback! I wasn't sure if this part of things meant that the user should give feedback or feedback should be given to the user.
# So I implemented them both! The user can vote on the images, and the images will show their past rating.
# It doesn't do anything for mass repeat voting. Something for later!
@app.route('/voteup/<string:text>', methods=['POST'])
def vote_up(text):
    text = unquote(text)
    return db_utils.vote(text, 1)

@app.route('/votedown/<string:text>', methods=['POST'])
def vote_down(text):
    text = unquote(text)
    return db_utils.vote(text, -1)


if __name__ == '__main__':
    app.run()