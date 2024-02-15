from flask import Blueprint, render_template

app6_blueprint = Blueprint('app6', __name__, template_folder='templates4')

@app6_blueprint.route('/chartpool')
def application6():
    return render_template('chartpool.html')
