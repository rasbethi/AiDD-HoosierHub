from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.models.models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# -------------------------
# LOGIN ROUTE
# -------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.status != "active":
            flash("Your account is currently inactive. Please contact the administrator.", "warning")
            return redirect(url_for("auth.login"))
        elif user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")

            # Role-based redirect
            if user.role == "admin":
                flash("Welcome, Admin!", "info")
                return redirect(url_for("resource_bp.list_resources"))
            elif user.role == "staff":
                return redirect(url_for("resource_bp.list_resources"))
            else:  # student
                return redirect(url_for("resource_bp.list_resources"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


# -------------------------
# REGISTER ROUTE
# -------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "warning")
            return redirect(url_for("auth.register"))

        # ✅ FIXED: Email-based role assignment
        if email == "admin@campushub.edu":
            role = "admin"
        elif email.endswith("@faculty.iu.edu"):
            role = "staff"
        elif email.endswith("@iu.edu"):
            role = "student"
        else:
            flash("Invalid email domain. Use @iu.edu for students or @faculty.iu.edu for staff.", "danger")
            return redirect(url_for("auth.register"))

        # Create new user
        new_user = User(name=name, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"Account created successfully as {role.capitalize()}!", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# -------------------------
# LOGOUT
# -------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("resource_bp.preview_resources"))


# -------------------------
# PROFILE
# -------------------------
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            name = (request.form.get("name") or "").strip()
            department = (request.form.get("department") or "").strip()
            profile_image = (request.form.get("profile_image") or "").strip()

            if not name:
                flash("Name is required.", "danger")
                return redirect(url_for("auth.profile"))

            current_user.name = name
            current_user.department = department or None
            if profile_image:
                current_user.profile_image = profile_image
            else:
                current_user.profile_image = "https://ui-avatars.com/api/?background=990000&color=fff&name=" + name.replace(" ", "+")

            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("auth.profile"))

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_user.check_password(current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("auth.profile"))

            if len(new_password) < 8:
                flash("New password must be at least 8 characters long.", "warning")
                return redirect(url_for("auth.profile"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("auth.profile"))

            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=current_user)