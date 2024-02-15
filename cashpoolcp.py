from flask import Blueprint, render_template

cashpoolcp_blueprint = Blueprint('cashpoolcp', __name__, template_folder='dashboard')

@cashpoolcp_blueprint.route('/cashpoolcp')
def cashpoolcp():
    return render_template('cashpoolcp.html')
