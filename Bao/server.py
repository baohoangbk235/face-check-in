from flask import Flask, request, redirect, url_for
import os
import re
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'video' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['video']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'uploaded success'
    return 'a'



# @app.route('/', methods = ['GET', 'POST'])
# def upload_file():
#     print(request.body)
if __name__ == '__main__':
    app.run(debug = True, port = 3500)
