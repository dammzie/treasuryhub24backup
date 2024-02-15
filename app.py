from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from flask_session import Session
from urllib.parse import quote as url_quote
from app2 import app2_blueprint  # Import the Blueprint for application2
from app3 import app3_blueprint  # Import the Blueprint for application3
from app4 import app4_blueprint  # Import the Blueprint for application4
from app5 import app5_blueprint  # Import the Blueprint for application4
from app6 import app6_blueprint  # Import the Blueprint for application6
from documentwiz import documentwiz_blueprint 
from dashboard import dashboard_blueprint  # Import the Blueprint for dashboard landing
from cashpoolcp import cashpoolcp_blueprint  # Import the Blueprint for cashpool dashboard
from goingconcern import goingconcern_blueprint
from datetime import datetime
import pandas as pd
import io

app = Flask(__name__)
app.register_blueprint(app2_blueprint, url_prefix='/app2')  # Registering Application2
app.register_blueprint(app3_blueprint, url_prefix='/app3')  # Registering Application3
app.register_blueprint(app4_blueprint, url_prefix='/app4')  # Registering Application4
app.register_blueprint(app5_blueprint, url_prefix='/app5')  # Registering Application5
app.register_blueprint(app6_blueprint, url_prefix='/app6')  # Registering Application6
app.register_blueprint(documentwiz_blueprint, url_prefix='/documentwiz')  # Registering Application6
app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')  # Registering Dashboard landing
app.register_blueprint(cashpoolcp_blueprint, url_prefix='/dashboard')  # Registering Cashpool Dashboard
app.register_blueprint(goingconcern_blueprint, url_prefix='/goingconcern') 

# App secret key
app.secret_key = "supersecretkey"  # for flash messages

# Set the session type to the filesystem (server-side)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['UPLOAD_FOLDER'] = 'fileupnew'

Session(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/application1/')
def application1():
    return render_template('application1.html')

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('application1'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('application1'))

    # Save the file's content in session for later access
    file_content = file.read()
    session['file_content'] = file_content

    return redirect(url_for('download'))

@app.route('/download', methods=['GET'])
def download():

    # Read the CSV file from session
    file_content = session.get('file_content', None)
    if not file_content:
        flash('No file found in session.')
        return redirect(url_for('home'))
    df_a = pd.read_csv(io.BytesIO(file_content))

    # Assume 'corporate' conversion type and use the date from the date column
    conversion_type = 'Corporate'  # Adjust this as needed for the correct value
    df_a['CONVERSION_DATE'] = pd.to_datetime(df_a['CONVERSION_DATE'])

    # Filter rows based on the assumed conversion type
    df_filtered = df_a[df_a['USER_CONVERSION_TYPE'] == conversion_type].copy()

    # Convert and filter date
    df_filtered['CONVERSION_DATE'] = df_filtered['CONVERSION_DATE'].dt.strftime('%Y%m%d')

    
    # Use the first (or any specific) date from the 'CONVERSION_DATE' column for the filename
    if not df_filtered.empty:
        file_date = pd.to_datetime(df_filtered['CONVERSION_DATE'].iloc[0]).strftime("%d%m%Y")  # Format the date
    else:
        flash('No data after filtering.')
        return redirect(url_for('application1'))


    # Transformation
    df_transformed = df_filtered[['CONVERSION_DATE', 'FROM_CURRENCY', 'TO_CURRENCY', 'USER_CONVERSION_TYPE', 'SHOW_CONVERSION_RATE']].copy()
    df_transformed.columns = ['date', 'currency_from', 'currency_to', 'source', 'rate']
    df_transformed['rate'] = df_transformed['rate'].apply(lambda x: '{:.5f}'.format(x))
    df_transformed['combined'] = df_transformed['date'] + '|' + df_transformed['currency_from'] + '|' + df_transformed['currency_to'] + '|' + df_transformed['source'] + '|' + df_transformed['rate'].astype(str)

    # Get the current date in the desired format
    current_date = datetime.now().strftime("%d%m%Y")
    
    # Save to an in-memory BytesIO object
    output = io.BytesIO()
    df_transformed[['combined']].to_csv(output, index=False, header=['date|currency_from|currency_to|source|rate'], line_terminator='\n', encoding='utf-8')
    output.seek(0)

    # Use the current date in the filename
    output_filename = f"FXFile{file_date}.csv"

    return send_file(output, attachment_filename=output_filename, as_attachment=True, mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True)
