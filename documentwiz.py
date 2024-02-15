from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify, get_flashed_messages, flash, session
import pandas as pd
from functools import wraps
from fpdf import FPDF
from datetime import datetime
import re
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import json

documentwiz_blueprint = Blueprint('documentwiz', __name__, template_folder='documentgen')


# Global variable to store user responses
user_responses = {}
excel_data = {}
# Create a list to store the report content
report_content = []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in session:
            # Redirect to the login page if user_info not in session
            return redirect(url_for('documentwiz.dwizapplogin'))
        return f(*args, **kwargs)
    return decorated_function

@documentwiz_blueprint.route('/logout')
def logout():
    session.pop('user_info', None)  # This removes the user_info from the session
    return redirect(url_for('documentwiz.dwizapplogin'))


@documentwiz_blueprint.route('/signin-side1')
def dwizapp():
    user_info = session.get('user_info', {})
    return render_template('signin-side1.html', user_info=user_info)

@documentwiz_blueprint.route('/signin', methods=['POST'])
def signin():
    # Read the form data
    username = request.form.get('username', '').strip().lower()  # Trim and convert to lowercase
    password = request.form.get('password', '').strip()  # Trim spaces

    # Read the user data from the Excel file
    df = pd.read_excel(os.path.join('static', 'excel', 'userlog.xlsx'))
    df['username'] = df['username'].str.strip().str.lower()  # Normalize username data
    df['password'] = df['password'].str.strip()  # Normalize password data

    # Check if the user exists and the password matches
    user = df.loc[(df['username'] == username) & (df['password'] == password)]

    if not user.empty:
        # User found and password matches
        # Store user information in session
        session['user_info'] = {
            'username': username,
            'first_name': user['FirstName'].values[0],
            'last_name': user['LastName'].values[0],
            'role': user['Role'].values[0],
            'shortname': user['NameShort'].values[0]
        }
        return redirect(url_for('documentwiz.dwizapp'))
    else:
        # User not found or password does not match
        flash('Invalid credentials or user does not exist', 'error')
        return redirect(url_for('documentwiz.dwizapplogin'))

@documentwiz_blueprint.route('/signin-document')
def dwizapplogin():
    # Check for flash messages
    messages = get_flashed_messages(with_categories=True)
    return render_template('signin-document.html', messages=messages)

@documentwiz_blueprint.route('/get_excel_data')
def get_excel_data():
    df = pd.read_excel('static/excel/TC.xlsx')
    excel_data = df.set_index('Short description')[['Control Frequency', 'Description', 'Control']].to_dict('index')
    return jsonify(excel_data)

@documentwiz_blueprint.route('/signin-side2', methods=['GET', 'POST'])
def signin_side2():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['document_title'] = request.form.get('document_title')
        session['dropdown_selection'] = request.form.get('dropdown')

    # Read data from Excel file for dropdown and related fields
    df = pd.read_excel('static/excel/TC.xlsx')
    global excel_data
    excel_data = df.set_index('Short description')[['Control Frequency', 'Description', 'Control']].to_dict('index')
    dropdown_options = list(excel_data.keys())
    json_data = json.dumps(excel_data).encode('utf-8').decode('unicode-escape')
    return render_template('signin-side2.html', dropdown_options=dropdown_options, excel_data=json.dumps(excel_data), user_info=user_info)

@documentwiz_blueprint.route('/signin-side3', methods=['GET', 'POST'])
def signin_side3():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        # Save selections from signin-side2
        user_responses['dropdown_selection'] = request.form.get('dropdown')
        user_responses['control_description'] = excel_data[user_responses['dropdown_selection']]['Description']
        user_responses['control_frequency'] = excel_data[user_responses['dropdown_selection']]['Control Frequency']
        user_responses['control_code'] = excel_data[user_responses['dropdown_selection']]['Control']
        user_responses['radio_selection'] = request.form.get('radio22')
        user_responses['other_input'] = request.form.get('other_input') if user_responses['radio_selection'] == 'Others' else None

        # New form data from signin-side3
        user_responses['control_operated'] = request.form.get('groupVerticalRadioExample111')
        user_responses['no_explanation'] = request.form.get('NoInput2') if user_responses['control_operated'] == 'No' else None
        user_responses['support_schedules'] = request.form.get('numberOfSchedules')
        
        dropdown_selection = user_responses['dropdown_selection']

       # Check if the specific form item was visible based on dropdown criteria
        if dropdown_selection in ['ETC user access', 'Finastra access control', 'Access to 360T', 'Bank systems admin']:
            # Extract additional data from the form item only if it was visible
            additional_info = request.form.get('groupVerticalRadioExample44')
        else:
            # Set additional_info to None or an empty value if the form item was not visible
            additional_info = None

        # Store the additional_info in user_responses
        user_responses['additional_info'] = additional_info
        user_responses['control_operated'] = request.form.get('groupVerticalRadioExample111')


        # Safely get the number of schedules and convert to integer
        support_schedules = request.form.get('numberOfSchedules') or '0'  # Default to '0' if None or empty
        num_schedules = int(support_schedules)
        for i in range(num_schedules):
            user_responses[f'schedule_{i}_selection'] = request.form.get(f'groupVerticalRadioExample{i + 1}')
    
        user_responses['calc_re_performed'] = request.form.get('groupVerticalRadioExample4')
        user_responses['control_effectiveness'] = request.form.get('groupVerticalRadioExample5')
        user_responses['small_issues_explanation'] = request.form.get('Yes1') if user_responses['control_effectiveness'] == 'Yes having resolved small issues' else None
        user_responses['major_issues_explanation'] = request.form.get('Yes2') if user_responses['control_effectiveness'] == 'Yes having resolved major issues' else None

    # Render signin-side3.html for GET request
    return render_template('signin-side3.html', user_info=user_info, dropdown_selection=dropdown_selection)


@documentwiz_blueprint.route('/signin-side4', methods=['GET', 'POST'])
def signin_side4():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['control_operated'] = request.form.get('groupVerticalRadioExample111')
        dropdown_selection = user_responses['dropdown_selection']

       # Check if the specific form item was visible based on dropdown criteria
        if dropdown_selection in ['ETC user access', 'Finastra access control', 'Access to 360T', 'Bank systems admin']:
            # Extract additional data from the form item only if it was visible
            additional_info = request.form.get('groupVerticalRadioExample44')
        else:
            # Set additional_info to None or an empty value if the form item was not visible
            additional_info = ''
        user_responses['additional_info'] = additional_info
        print(additional_info)
        user_responses['no_explanation'] = request.form.get('NoInput2') if user_responses['control_operated'] == 'No' else None
        user_responses['support_schedules'] = request.form.get('numberOfSchedules')

        num_schedules = int(request.form.get('numberOfSchedules', 0))
        
        # Clear previous selections if they exist
        for key in list(user_responses.keys()):
            if key.startswith('schedule_'):
                del user_responses[key]

        for i in range(num_schedules):
            selections = []

            # Assuming 5 checkbox options and 1 text input for "Others"
            num_options = 5  # Update this number based on the actual number of checkbox options
            for j in range(num_options):
                option_name = f'schedule{i}_option{j}'
                if request.form.getlist(option_name):
                    selections.extend(request.form.getlist(option_name))

            # Capture the "Others" input for this schedule
            other_input_name = f'schedule{i}_option5'  # Assuming 'scheduleX_option5' is the "Others" text input
            other_input_value = request.form.get(other_input_name, '').strip()
            if other_input_value:  # Only add to selections if something was entered
                selections.append(f"Others: {other_input_value}")

            user_responses[f'schedule_{i}_selections'] = selections
    
        user_responses['calc_re_performed'] = request.form.get('groupVerticalRadioExample4')
        user_responses['control_effectiveness'] = request.form.get('groupVerticalRadioExample5')
        user_responses['small_issues_explanation'] = request.form.get('Yes1') if user_responses['control_effectiveness'] == 'Yes having resolved small issues' else None
        user_responses['major_issues_explanation'] = request.form.get('Yes2') if user_responses['control_effectiveness'] == 'Yes having resolved major issues' else None

        pass
 
    # Pass the saved responses to the template
    today = datetime.now().strftime("%dth %b %Y")
    return render_template('signin-side4.html', responses=user_responses, today=today, user_info=user_info)


@documentwiz_blueprint.route('/download_pdf', methods=['GET'])
def download_pdf():
    user_info = session.get('user_info', {})
    # Retrieve user responses
    document_title = user_responses.get('document_title', 'default_document')
    sanitized_title = re.sub(r'\W+', '', document_title.replace(' ', '_'))

    # Format the current date
    today = datetime.now().strftime("%dth_%b_%Y")
    todaynew = datetime.now().strftime("%dth %b %Y")

    # Combine the title and date for the file name
    pdf_file_name = f"{sanitized_title}_{today}.pdf"
    pdf_file_path = f'static/excel/{pdf_file_name}'

    # Create a PDF document
    doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
    report_content = []

    # Add the image header
    logo_path = 'static/img/logo/pearsonreport.png'  # Ensure this path is correct
    logo = Image(logo_path, width=170, height=100)
    report_content.append(logo)
    report_content.append(Spacer(1, 24))
    # Define custom styles for the report
    styles = getSampleStyleSheet()
    subject_style = ParagraphStyle(name='SubjectStyle', parent=styles['Normal'])
    subject_style.fontSize = 12  # Increase the font size for the Subject line

    # Define custom styles for the report
    styles = getSampleStyleSheet()
    # subject_style = ParagraphStyle(name='SubjectStyle', parent=styles['Normal'], fontSize=13)

    # Retrieve user responses
    document_title = user_responses.get('document_title', 'N/A')
    dropdown_selection = user_responses.get('dropdown_selection', 'N/A')
    control_description = user_responses.get('control_description', 'N/A')
    control_code = user_responses.get('control_code', 'N/A')
    control_frequency = user_responses.get('control_frequency', 'N/A')
    control_operated = user_responses.get('control_operated', 'N/A')
    control_operated_no = user_responses.get('no_explanation', '')
    support_schedules = user_responses.get('support_schedules', 'N/A')
    calc_re_performed = user_responses.get('calc_re_performed', 'N/A')
    control_effectiveness = user_responses.get('control_effectiveness', 'N/A')
    control_effectiveness_small = user_responses.get('small_issues_explanation')
    control_effectiveness_big = user_responses.get('major_issues_explanation')
    doc_type = user_responses.get('radio_selection', 'N/A') 
    doc_typeo = user_responses.get('other_input', '')
    additional_info = user_responses.get('additional_info', '')

    # Start Custom File Note Content
    file_note = f"""
    <b>Document Title:</b> {document_title}<br/><br/>
    """
    # Conditionally include the 'Document Type' based on the selection
    if doc_type == 'Others':
        # Include only if 'Others' is selected and there's a custom input
        if doc_typeo:
            file_note += f"<b>Document Type - Others:</b> {doc_typeo}<br/><br/>"
    else:
        # Include the 'Document Type' when it's not 'Others'
        file_note += f"<b>Document Type:</b> {doc_type}<br/><br/>"

    # Continue building the file note
    file_note += f"""
    <b>Relates to which control:</b> {dropdown_selection}<br/><br/>
    <b>Control Code:</b> {control_code}<br/><br/>
    <b>Control Frequency:</b> {control_frequency}<br/><br/>
    <b>Control Description:</b> {control_description}<br/><br/>
    """
    
            # Conditionally include the 'Document Type' based on the selection
    if control_operated == 'No':
        # Include only if 'Others' is selected and there's a custom input
        if control_operated_no:
            file_note += f"<b>Has the control operated as described during the period under assessment?</b><br/> No: {control_operated_no}<br/><br/>"
    else:
        # Include the 'Document Type' when it's not 'Others'
        file_note += f"<b>Has the control operated as described during the period under assessment?</b><br/> {control_operated}<br/><br/><br/>"
    

    file_note += f"""
    <b>How many supporting schedules have been prepared by Pearson?</b> {support_schedules}<br/><br/>
    """
    
    # Add schedules and their selections to the file note
    num_schedules = int(support_schedules)
    for i in range(num_schedules):
        schedule_selections = user_responses.get(f'schedule_{i}_selections', [])
        schedule_info = f"<b>What is the underlying source of the supporting schedule (schedule {i + 1})?</b><br/>"
        for selection in schedule_selections:
            schedule_info += f" - {selection}<br/>"
        file_note += schedule_info + "<br/>"

        # Final part of the file note
    file_note += f"""
    <b>Have any calculations been re-performed to ensure that totals have been properly calculated?</b><br/> {calc_re_performed}<br/><br/>
    """
            # Conditionally include the 'Document Type' based on the selection
    if additional_info == '':
        # Include only if 'Others' is selected and there's a custom input
        if additional_info:
            file_note += f""
    else:
        # Include the 'Document Type' when it's not 'Others'
        file_note += f"<b>I have reviewed the user entitlements report and confirm that all access is appropriate and needs to be retained </b><br/> {additional_info}<br/><br/>"

    
            # Conditionally include the 'Document Type' based on the selection
    if control_effectiveness == 'Yes having resolved small issues':
        # Include only if 'Others' is selected and there's a custom input
        if control_effectiveness_small:
            file_note += f"<b>Based on the work performed, are you comfortable that the control is working effectively?</b><br/> Yes having resolved small issues: {control_effectiveness_small}<br/><br/>"
    elif control_effectiveness == 'Yes having resolved major issues':
        # Include only if 'Others' is selected and there's a custom input
        if control_effectiveness_big:
            file_note += f"<b>Based on the work performed, are you comfortable that the control is working effectively?</b><br/> Yes having resolved major issues: {control_effectiveness_big}<br/><br/>"
    else:
        # Include the 'Document Type' when it's not 'Others'
        file_note += f"<b>Based on the work performed, are you comfortable that the control is working effectively?</b> {control_effectiveness}<br/><br/>"
    
    file_note += f"""
    <b>Completed By:</b><br/>
    {user_info.get('first_name', 'N/A')} {user_info.get('last_name', 'N/A')}<br/>
    {user_info.get('role', 'N/A')}<br/>
    Email: {user_info.get('username', 'N/A')}<br/>
    <b>Date: {todaynew}</b>
    """

    # Append the file note to the report content
    report_content.append(Paragraph(file_note, styles['Normal']))
    report_content.append(PageBreak())

    # Create the PDF
    doc.build(report_content)

    return send_file(pdf_file_path, as_attachment=True)


@documentwiz_blueprint.route('/signin-side5')
def signin_side5():
    user_info = session.get('user_info', {})
    return render_template('signin-side5.html', user_info=user_info)

