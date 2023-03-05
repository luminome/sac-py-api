from flask import Flask, jsonify
import os

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({"json": "hello-world python."})


@app.route('/env')
def environment():
    return jsonify(dict(os.environ))


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
