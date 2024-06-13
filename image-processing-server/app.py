from flask import Flask

app = Flask(__name__)


@app.route("/health-check", methods=["GET"])
def health_check():
    response = {"status": "success", "message": "The flask app is working"}
    return response


if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')
