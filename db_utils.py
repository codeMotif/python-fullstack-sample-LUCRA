import io
import os
from flask_sqlalchemy import SQLAlchemy
from PIL import Image

from image_utils import generate_image_from_text


def init(app):
    global AIImageQueryRecord, dbexists, db

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
    # This is the model for the records. It used to be a simple key-value store, with the key being the text and the value being the image. Keep that core.
    # It's also got votes and such.
    class AIImageQueryRecord(db.Model):
        text = db.Column(db.String(500), primary_key=True) # The text is unique!
        image = db.Column(db.LargeBinary(length=2**24-1), nullable=False)
        votes = db.Column(db.Integer, default=0)
        votetotal = db.Column(db.Integer, default=0)
    # Setup the DB with the table we need.
    if dbexists:
        with app.app_context():
            try:
                db.create_all()
            except:
                print("Database was precluded in some way.")
                print("\033[91mThe database may have become corrupted, or you may be pointing at a database that has another application's data!\033[0m")
                print("Defaulting to no database.")
                dbexists = False
        
        
def create_or_retrieve_cached_image(text):
    rating = 0
    if (dbexists):
        old_query = AIImageQueryRecord.query.get(text)
    if old_query is not None:
        # Retrieve the old data.
        image = Image.open(io.BytesIO(old_query.image))
        rating = old_query.votes
    else:
        # If nothing was found, generate something new.
        image = generate_image_from_text(text)
        new_entry_arr = io.BytesIO()
        # PNGs are a better approach here. Losslessness is key.
        image.save(new_entry_arr, format='PNG')
        new_entry_arr.seek(0)
        # Cache the new data for the next time.
        db.session.add(AIImageQueryRecord(text=text, image=new_entry_arr.read()))
        db.session.commit()
    return image, rating

def vote(text, vote):
    if dbexists:
        image_record = AIImageQueryRecord.query.get(text)
        if image_record is not None:
            image_record.votes += vote
            image_record.votetotal += 1
            db.session.commit()
            return "OK"
        else:
            return "NOT FOUND", 404
    else:
        return "NO DATABASE", 500