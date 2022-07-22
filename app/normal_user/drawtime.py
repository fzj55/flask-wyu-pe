from flask import Blueprint

from app.model import DrawTime

drawtime_bp = Blueprint('drawtime', __name__, url_prefix='/drawtime')


