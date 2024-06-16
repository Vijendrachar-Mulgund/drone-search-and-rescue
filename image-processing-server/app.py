from flask import Flask, Response, render_template
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from requests import get

# Load the environment variables
load_dotenv()

# Init Flask app
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


# Routes
@app.route("/health-check", methods=["GET"])
def health_check():
    response = {
        "status": "success",
        "message": "The Image processing server is working",
        "current": f"{datetime.now()}"
    }
    return response


@app.route('/video_feed', methods=["GET"])
def video_feed():
    def generate():
        with get('http://localhost:8001/video_stream', stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Launch the server
if __name__ == "__main__":
    print("The Image Processing - Video Stream server has started 🚀")
    port = int(getenv("PORT", 8000))
    host = getenv("HOST", "0.0.0.0")
    app.run(debug=True, port=port, host=host)
