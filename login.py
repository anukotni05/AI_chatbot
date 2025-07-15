from flask import Blueprint, render_template, request, redirect, url_for # type: ignore

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Add login logic here
        return redirect(url_for('dashboard.dashboard'))
    return render_template('login.html')
