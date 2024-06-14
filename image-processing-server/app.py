from flask import Flask
from dotenv import load_dotenv
from os import getenv
from datetime import datetime

# Load the environment variables
load_dotenv()

# Init Flask app
app = Flask(__name__)


# Routes
@app.route("/health-check", methods=["GET"])
def health_check():
    response = {
        "status": "success",
        "message": "The Image processing server is working",
        "current": f"{datetime.now()}"
    }
    return response


# Launch the server
if __name__ == "__main__":
    port = int(getenv("PORT", 5000))
    host = getenv("HOST", "0.0.0.0")
    app.run(debug=True, port=port, host=host)
