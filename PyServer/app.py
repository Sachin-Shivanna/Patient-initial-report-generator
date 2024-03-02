from flask import Flask
from app.Routes.routes import routes_bp

app = Flask(__name__)
app.register_blueprint(routes_bp)

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port=8001)