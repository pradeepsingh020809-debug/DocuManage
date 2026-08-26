import random
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.models import db, User
from app.utils.decorators import login_required, log_activity

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

AVATAR_COLORS = [
    '#6366f1', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6'
]

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not identifier or not password:
            flash('Please provide both username/email and password.', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter(
            (db.func.lower(User.username) == identifier.lower()) | (db.func.lower(User.email) == identifier.lower())
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid username/email or password.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('This account is currently deactivated.', 'danger')
            return render_template('auth/login.html')

        # Successful login
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['full_name'] = user.full_name
        session.permanent = remember

        log_activity('LOGIN', details=f"User {user.username} logged in.", user_id=user.id)

        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not full_name or not password:
            flash('All fields are required.', 'warning')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        # Check if this is the first user (make them Admin)
        is_first_user = User.query.count() == 0
        role = 'admin' if is_first_user else 'editor'
        avatar_color = random.choice(AVATAR_COLORS)

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            avatar_color=avatar_color
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        log_activity('REGISTER', details=f"New user registered: {username} ({role})", user_id=new_user.id)

        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = new_user.role
        session['full_name'] = new_user.full_name

        flash(f'Welcome to DocuVault, {full_name}!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    uid = session.get('user_id')
    if uid:
        log_activity('LOGOUT', details="User logged out.", user_id=uid)
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = g.current_user
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            user.full_name = request.form.get('full_name', user.full_name).strip()
            user.avatar_color = request.form.get('avatar_color', user.avatar_color)
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_new_password', '')

            if not user.check_password(current_pw):
                flash('Current password is incorrect.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'warning')
            else:
                user.set_password(new_pw)
                db.session.commit()
                flash('Password changed successfully!', 'success')

        return redirect(url_for('auth.profile'))

    recent_logs = user.activity_logs.order_by(db.desc('created_at')).limit(15).all()
    return render_template('settings/profile.html', user=user, recent_logs=recent_logs)
