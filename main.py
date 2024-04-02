import os
from flask import Flask, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from transformers import pipeline

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
# db = SQLAlchemy(app)

messages = [] 
summarizer = pipeline('summarization')


@app.route('/', methods=['GET', 'POST'])
def render_chat():
    if request.method == 'POST':
        text = request.form.get('text')
        summary = create_summary(text)
        messages.append(summary)
    return '''
        <head>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="pastMessages">
                {}
            </div>
            <form method="POST" action="/">
                Enter text: <br>
                <textarea name="text"></textarea><br>
                <input type="submit" value="Submit"><br>
            </form>
        </body>
    '''.format('<br>'.join(messages))

def create_summary(text: str):
    text_summary=summarizer(text, max_length=15, min_length=5, do_sample=False)[0]['summary_text'] # 
    return f'<details><summary>{text_summary}</summary>{text}</details>'

if __name__ == '__main__':
    app.run(debug=True)