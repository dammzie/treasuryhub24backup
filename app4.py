from flask import Blueprint, render_template

app4_blueprint = Blueprint('app4', __name__, template_folder='templates4')

@app4_blueprint.route('/chart')
def application4():
    return render_template('chart.html')
