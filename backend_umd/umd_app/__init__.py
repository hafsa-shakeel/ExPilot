from dotenv import load_dotenv
from flask import Flask
from datetime import timedelta
from flask_cors import CORS
from flask import session
# from flask_session import Session
import os
from flask import send_from_directory
from umd_app.routes.alert_routes import alert_bp
from umd_app.routes.utilityroutes import utility_bp
from umd_app.routes.budget_routes import budget_bp
from umd_app.routes.branch_routes import branch_bp
from umd_app.routes.dashboard import dashboard_bp
from umd_app.routes.business_routes import business_bp
from umd_app.routes.auth_routes import auth_bp

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads', 'media')

    app.secret_key = 'c1nn@m0n!@#'
    app.PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = './flask_sessions'
    app.config['SESSION_FILE_THRESHOLD'] = 100
    app.config['SESSION_PERMANENT'] = True
    # must be False unless you explicitly sign
    app.config['SESSION_USE_SIGNER'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True

  # Session(app)
    # jwt = JWTManager(app)

    # CORS Setup -allows frontend to send JWT, cookies, headers
    CORS(app, supports_credentials=True, origins=['http://localhost:3000'])

    @app.after_request
    def apply_cors_headers(response):
        # response.headers.add("Access-Control-Allow-Origin","http://localhost:3000")
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type")
        response.headers.add(
            "Access-Control-Allow-Methods", "GET, POST, OPTIONS, PATCH, DELETE, PUT")
        # response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(business_bp, url_prefix='/api/business')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(branch_bp, url_prefix='/api/branch')
    app.register_blueprint(budget_bp, url_prefix='/api/budget')
    app.register_blueprint(utility_bp, url_prefix='/api/utility')
    app.register_blueprint(alert_bp, url_prefix='/api/alert')

    return app
