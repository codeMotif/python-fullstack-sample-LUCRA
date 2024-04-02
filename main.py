import os
from flask import Flask, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from transformers import pipeline
from diffusers import StableDiffusionPipeline
import torch
import io
import base64
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('LUCRA_AI_QUERIES_DATABASE_URI')
db = SQLAlchemy(app)

class AIImageQueryRecord(db.Model):
    text = db.Column(db.String(500), primary_key=True)
    image = db.Column(db.LargeBinary(length=2**24-1), nullable=False)

with app.app_context():
    db.create_all()

messages = [] 
model_id = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

def get_head():
    with open('head.html', 'r') as file:
        return file.read()

@app.route('/', methods=['GET', 'POST'])
def render_chat():
    if request.method == 'POST':
        text = request.form.get('text')
        image = create_image(text)
        messages.append(image)
    return f'''
        {get_head()}
        <body>
        <h1>PIXEL INSPIRATIONS</h1>
            <div class="pastMessages">
                {"<br>".join(messages)}
            </div>
            <div id="spinner" style="display: none;">
                <div class="loader"></div>
            </div>
            <form id="myForm" method="POST" action="/">
                <textarea id="myTextarea" name="text" maxlength="500"></textarea>
            </form>
        </body>
    '''


def create_image(text: str):
    text = text.strip().lower()    
    try:
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
    except SQLAlchemyError as e:
        # This should have real logging in production. Which is to say in a real project.
        print(f"Database error: {e}")
        image = generate_image_from_text(text)
    except Exception as e:
        raise e
    byte_arr = io.BytesIO()
    image = image.convert("P", palette=Image.ADAPTIVE, colors=16).resize((128, 128)).resize((512, 512))
    image.save(byte_arr, format='PNG')
    encoded_image = base64.encodebytes(byte_arr.getvalue()).decode('ascii')
    image_html = f'<details><summary>{text.upper()}</summary><img src="data:image/png;base64,{encoded_image}"/></details>'

    return image_html

def generate_image_from_text(text):
    return pipe(text).images[0]

if __name__ == '__main__':
    app.run(debug=True)