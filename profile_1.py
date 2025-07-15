from flask import Blueprint, render_template, request, redirect, url_for # type: ignore

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
def profile():
    return render_template('profile.html')

@profile_bp.route('/change-password', methods=['POST'])
def change_password():
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    if new_password != confirm_password:
        return "Passwords do not match", 400
    return redirect(url_for('profile.profile'))

@profile_bp.route('/logout')
def logout():
    return redirect(url_for('login.login'))
