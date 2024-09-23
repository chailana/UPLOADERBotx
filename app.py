from flask import Flask

app = Flask(__name__)  # Use __name__ instead of name

@app.route('/')
def hello():
    return 'Hello, World!'  # Ensure no non-printable characters are present

if __name__ == '__main__':  # Use __name__ instead of name
    # Run the Flask app on port 8000
    app.run(host='0.0.0.0', port=8000)
