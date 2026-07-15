from flask import Blueprint, render_template


public_bp = Blueprint(
    "public",
    __name__
)


@public_bp.route("/")
def index():
    """
    Render the public landing page.
    """

    return render_template("index.html")