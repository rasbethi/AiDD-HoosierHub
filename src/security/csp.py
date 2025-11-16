from flask_talisman import Talisman

def apply_csp(app):
    """Apply Content Security Policy to the Flask app"""
    csp = {
        'default-src': "'self' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
        'font-src': "'self' https://fonts.gstatic.com",
        'img-src': "'self' data: https:",
    }
    Talisman(app, content_security_policy=csp, force_https=False)
