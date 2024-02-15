from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, session, current_app
import os
import pandas as pd
import calendar
import numpy as np

app5_blueprint = Blueprint('app5', __name__, template_folder='fileupname')

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app5_blueprint.route('/', methods=['GET', 'POST'])
def upload_singlefile():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            session['singlefile_path'] = filename
            return redirect(url_for('app5.upload_fxfile'))  # Notice the 'app5.' prefix to the route
    return render_template('upload_singlefile.html')

@app5_blueprint.route('/upload_fxfile', methods=['GET', 'POST'])
def upload_fxfile():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            session['fxfile_path'] = filename
            return redirect(url_for('app5.select_header'))
    return render_template('upload_fxfile.html')

@app5_blueprint.route('/select_header', methods=['GET', 'POST'])
def select_header():
    if request.method == 'POST':
        header = request.form.get('header')

        single_tab_df = pd.read_csv(session['singlefile_path'])

        # Define a dictionary mapping current column names to new column names
        rename_dict = {
            'SOURCE_ENTITY': 'Entity x',
            'SOURCE_ACCOUNT': 'Account x',
            'ACCOUNT': 'Prime Code x', 
            'SOURCE_UD1': 'CC', 
            'SOURCE_UD2': 'Div x', 
            'SOURCE_UD3': 'Product x', 
            'CURKEY': 'Base Currency Type', 
            'AMOUNT': 'Base Currency Amount',
            # ... add other mappings as needed
        }

        # Apply the renaming
        single_tab_df = single_tab_df.rename(columns=rename_dict)

        # Find the columns to drop
        cols_to_drop = set(single_tab_df.columns) - set(rename_dict.values())

        # Drop the columns
        single_tab_df = single_tab_df.drop(columns=cols_to_drop)

        # For the multi-tab spreadsheet, load from the uploaded path
        multi_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'multi.xlsx')
        product_df = pd.read_excel(multi_file_path, sheet_name='Product')
        coa_ac_df = pd.read_excel(multi_file_path, sheet_name='COA ac')
        cashflow_categories_df = pd.read_excel(multi_file_path, sheet_name='CASHFLOW Categories')
        ar_bucket_df = pd.read_excel(multi_file_path, sheet_name='AR Buckets')

        # 2. Perform the mapping operations

        # Mapping for PRODUCT NAME
        single_tab_df['Product x'] = single_tab_df['Product x'].astype(str).str.strip()
        product_df['Name'] = product_df['Name'].astype(str).str.strip()
        single_tab_df = pd.merge(single_tab_df, product_df[['Name', 'Description']], left_on='Product x', right_on='Name', how='left')
        single_tab_df['Product name x'] = single_tab_df['Description']
        single_tab_df.drop(['Name', 'Description'], axis=1, inplace=True)


        # Mapping for 'COA(AC)'
        single_tab_df['Account x'] = single_tab_df['Account x'].astype(str).str.strip()
        coa_ac_df['Name'] = coa_ac_df['Name'].astype(str).str.strip()
        single_tab_df = pd.merge(single_tab_df, coa_ac_df[['Name', 'Description']], left_on='Account x', right_on='Name', how='left')
        single_tab_df['Account Name x'] = single_tab_df['Description']
        single_tab_df.drop(['Name', 'Description'], axis=1, inplace=True)


        # Mapping for 'CASHFLOW AREA' and 'SUB AREA1'
        single_tab_df = pd.merge(single_tab_df, cashflow_categories_df[['Prime Code', 'Cash Flow Area (Per Group Cashflow Report)', 'Prime Code Description']], left_on='Prime Code x', right_on='Prime Code', how='left')
        single_tab_df['Cash Flow Area'] = single_tab_df['Cash Flow Area (Per Group Cashflow Report)']
        single_tab_df['Sub Area 1'] = single_tab_df['Prime Code Description']
        single_tab_df.drop(['Prime Code', 'Cash Flow Area (Per Group Cashflow Report)', 'Prime Code Description'], axis=1, inplace=True)

        # Mapping for 'SUB AREA2'
        single_tab_df['Account x'] = single_tab_df['Account x'].astype(str).str.strip()
        ar_bucket_df['BUCKETID'] = ar_bucket_df['BUCKETID'].astype(str).str.strip()
        trade_receivables_condition = single_tab_df['Cash Flow Area'].str.lower() == "trade receivables".lower()
        mapped_sub_area2 = pd.merge(single_tab_df[trade_receivables_condition], ar_bucket_df[['BUCKETID', 'DESC2']], 
                                    left_on='Account x', right_on='BUCKETID', how='left')
        single_tab_df['Sub Area 2'] = single_tab_df.get('Sub Area 2', '')  # This gets the 'SUB AREA2' column if it exists, else creates one with empty strings
        single_tab_df['Sub Area 2'] = single_tab_df['Account x'].map(ar_bucket_df.set_index('BUCKETID')['DESC2'])


        def get_last_day(date_str):
            # Extract month and year from the input string
            month_str = date_str.split('_')[1]
            year_str = "20" + date_str.split('_')[2]
            
            # Mapping of month abbreviations to their respective numbers
            month_dict = {
                "Jan": 1,
                "Feb": 2,
                "Mar": 3,
                "Apr": 4,
                "May": 5,
                "Jun": 6,
                "Jul": 7,
                "Aug": 8,
                "Sep": 9,
                "Oct": 10,
                "Nov": 11,
                "Dec": 12
            }
            
            # Get the last day of the month
            last_day = calendar.monthrange(int(year_str), month_dict[month_str])[1]
            
            # Construct the date string
            return f"{last_day:02}-{'-'.join(date_str.split('_')[1:])}"


        fx_file_df = pd.read_csv(session['fxfile_path'])
        date_column = header
        fx_mapped = pd.merge(single_tab_df, fx_file_df[['CCY', date_column]], left_on='Base Currency Type', right_on='CCY', how='left')
        single_tab_df['Base Currency Amount'] = pd.to_numeric(single_tab_df['Base Currency Amount'], errors='coerce')
        fx_mapped[date_column] = pd.to_numeric(fx_mapped[date_column], errors='coerce')
        single_tab_df['GBP'] = single_tab_df['Base Currency Amount'] / fx_mapped[date_column]
        single_tab_df['GBP'].fillna(0, inplace=True)  
        single_tab_df['GBP'] = np.floor(single_tab_df['GBP']).astype(int)


        # 4. Populate 'PERIOD' column with the refined format
        single_tab_df['Period'] = get_last_day(header)
        
        # Save to a new Excel file within the uploads folder
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'final_output.csv')
        single_tab_df.to_csv(output_path, index=False)

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], 'final_output.csv', as_attachment=True)

    # Logic to read headers from 'fxfiles.xlsx'
    fx_file_df = pd.read_csv(session['fxfile_path'])
    headers = fx_file_df.columns.tolist()

    return render_template('select_header.html', headers=headers)



