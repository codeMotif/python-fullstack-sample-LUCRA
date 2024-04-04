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
    if dbexists:
        with app.app_context():
            try:
                db.create_all()
            except:
                print("Database was precluded in some way.")
                print("\033[91mThe database may have become corrupted, or you may be pointing at a database that has another application's data!\033[0m")
                print("Defaulting to no database.")
                dbexists = False
        
    class AIImageQueryRecord(db.Model):
        text = db.Column(db.String(500), primary_key=True) # The text is unique!
        image = db.Column(db.LargeBinary(length=2**24-1), nullable=False)
        # Wouldn't it be nice to have timestamps and voting? Future feature.
        # Here, we'll configure the DB, if it's not already configured.
        
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