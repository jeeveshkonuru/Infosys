from flask import Flask

from ner.apis import api

app = Flask(__name__)
api.init_app(app)

# app.run(debug=True, threaded=True, host='10.188.49.101', port=7893)
app.run(debug=True, threaded=True)