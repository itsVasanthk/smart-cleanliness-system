from flask import Blueprint, render_template, session, redirect, url_for

awareness_bp = Blueprint('awareness', __name__)

def login_required():
    if 'user_id' not in session:
        return False
    return True

@awareness_bp.route("/awareness")
def awareness_home():
    if not login_required():
        return redirect(url_for('auth.login'))
    return render_template("awareness/awareness_home.html")

@awareness_bp.route("/awareness/tourism")
def tourism():
    if not login_required():
        return redirect(url_for('auth.login'))
    return render_template("awareness/tourism.html")

@awareness_bp.route("/awareness/temples")
def temples():
    if not login_required():
        return redirect(url_for('auth.login'))
    return render_template("awareness/temples.html")

@awareness_bp.route("/awareness/food")
def food():
    if not login_required():
        return redirect(url_for('auth.login'))
    return render_template("awareness/food.html")

@awareness_bp.route("/awareness/guidelines")
def guidelines():
    if not login_required():
        return redirect(url_for('auth.login'))
    return render_template("awareness/guidelines.html")
