from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet

app3_blueprint = Blueprint('app3', __name__, template_folder='templates3')

@app3_blueprint.route('/application3', methods=['GET', 'POST'])
def application3():
    return render_template('application3.html')

@app3_blueprint.route('/process_file_3', methods=['POST'])
def process_file_3():
    file = request.files['file']
    if file:
        file.stream.seek(0) 
        buffer = io.BytesIO(file.stream.read())  
        df = pd.read_excel(buffer) 
        df['TradeDate'] = pd.to_datetime(df['TradeDate'])
        session['uploaded_df'] = df.to_dict()  
        return redirect(url_for('app3.app3success'))  
    else:
        flash("No file uploaded")
        return redirect(url_for('app3.application3'))  

@app3_blueprint.route('/app3success', methods=['GET', 'POST'])
def app3success():
    if 'uploaded_df' not in session:
        flash("No data available.")
        return redirect(url_for('app3.application3'))
    
    uploaded_df = pd.DataFrame(session['uploaded_df'])
    
    if request.method == 'POST':
        start_date_input = request.form.get('start_date')
        end_date_input = request.form.get('end_date')
        
        # Convert user input to datetime objects
        start_date_object = datetime.strptime(start_date_input, '%Y-%m-%d')
        end_date_object = datetime.strptime(end_date_input, '%Y-%m-%d')
        
        # Filter based on user-selected date range and transaction types
        filtered_date_data = uploaded_df[(uploaded_df['TradeDate'] >= start_date_object) & (uploaded_df['TradeDate'] <= end_date_object)]
        filtered_data = filtered_date_data[filtered_date_data['Reason'].isin(['FX Swap NIH', 'FX Spot NIH', 'FX Forward NIH'])]
        
        # Generate PDF
        report_content = []
        styles = getSampleStyleSheet()

        # Add the image header
        logo_path = 'static/pearsonreport.png'  # Replace with the actual path to your logo image
        logo = Image(logo_path, width=170, height=100)
        report_content.append(logo)  # Add the logo to the beginning of the report
        
        # Iterate through the filtered data and add the report content
        for index, row in filtered_data.iterrows():
            # Extract the required information from the row
            internal_reference = row['InternalRef']
            counterparty = row['CounterParty']
            trans_type = row['Reason']
            start_date = row['ValueDate'].strftime("%dth of %B %Y")
            original_start_date = row['ValueDate'].strftime("%dth of %B %Y")
            trade_date = row['TradeDate'].strftime("%dth of %b. %Y")
            In_rate= row['InitialRate']
            In_rate2 = round(In_rate, 4)

            maturity_date = row['MaturityDate']
            if not pd.isnull(maturity_date):
                maturity_date = maturity_date.strftime("%dth of %b. %Y")
            else:
                maturity_date = ""

            trade_date = row['TradeDate'].strftime("%dth of %b. %Y")

            # Logic to determine start and maturity dates based on transaction type
            if trans_type in ["FX Spot NIH", "FX Forward NIH"]:
                start_date = trade_date
                maturity_date = original_start_date
            else:  # Assuming "FX Swap NIH" as the default
                start_date = original_start_date

            # Determine the appropriate currency based on the condition (USD)
            if row['Currency1'] == 'USD':
                currency = row['Currency1']
            elif row['Currency2'] == 'USD':
                currency = row['Currency2']
            else:
                currency = row['Currency1']  # You can choose either currency1 or currency2 as default
                
                # Determine the appropriate currency based on the condition (USD)
            if row['Currency1'] == 'USD':
                Notional = row['Principal1']
                Notionalabs = Notional/1000000
                Notional_value = abs( Notional/ 1000000)  # Convert to millions and ensure positive value
            elif row['Currency2'] == 'USD':
                Notional = row['Principal2']
                Notionalabs = Notional/1000000
                Notional_value = abs( Notional/ 1000000)  # Convert to millions and ensure positive value
            else:
                Notional = row['Currency1']  # You can choose either currency1 or currency2 as default

            if row['Currency1'] == 'USD':
                Notional = row['Principal1']
                Notional_value = abs( Notional/ 1000000)  # Convert to millions and ensure positive value
                answer1 = abs( Notional_value/ 1.2)
                answerr1 = round(answer1, 1)
            elif row['Currency2'] == 'USD':
                Notional = row['Principal2']
                Notional_value = abs( Notional/ 1000000)  # Convert to millions and ensure positive value
                answer1 = abs( Notional_value/ 1.2)
                answerr1 = round(answer1, 1)
            else:
                Notional = row['Currency1']
                
            if row['Currency1'] == 'USD':
                Notional = row['Principal1']
                Notional_value = abs(Notional/ 1000000)  # Convert to millions and ensure positive value
                answer2 =  abs(Notional_value/ 1.3)
                answerr2 = round(answer2, 1)
            elif row['Currency2'] == 'USD':
                Notional = row['Principal2']
                Notional_value = abs(Notional/ 1000000)  # Convert to millions and ensure positive value
                answer2 = abs(Notional_value/ 1.3)
                answerr2 = round(answer2, 1)
            else:
                Notional = row['Currency1']

            if answer1 is not None and answer2 is not None:
                finalresult = answer2 - answer1
                finall = abs(round(finalresult, 1))
            else:
                finalresult = None      
                
            # Add the File Note content
            file_note = f"""<b>Internal Reference:</b>&nbsp {internal_reference}<br/>
        <b>Counterparty:</b>&nbsp {counterparty}<br/>
        <b>Transaction Type:</b>&nbsp {trans_type}<br/>
        <b>Start Date:</b>&nbsp {start_date}<br/>
        <b>Maturity Date:</b>&nbsp {maturity_date}<br/>
        <b>Hedging Instrument Value:</b>&nbsp {Notional_value}M<br/>
        <b>FX Rate:</b>&nbsp {In_rate2}<br/>
        <br/>
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp<b>Date:</b>&nbsp {trade_date}<br/>
        <br/>

        <b><font size="11">Subject: Designation of {currency} {Notional_value}M FX Forward Contract as Net Investment Hedge</font></b><br/>
        <br/>

        &nbsp This file note serves to document the designation of a <font color="#007da5"> {currency} {Notional_value}M</font> foreign exchange (FX) forward contract as a net investment hedge of the first<font color="#007da5"> {currency} {Notional_value}M</font> of net assets held in subsidiaries, in accordance with the requirements under International Financial Reporting Standards (IFRS7 and IFRS9).<br/><br/>

        <b>Objective and Background:</b> <br/>
        The objective of this designation is to mitigate the currency exchange risk arising from the translation of the net assets of our subsidiaries. By designating this FX forward contract as a hedge, we aim to protect the value of our net investment in these subsidiaries from adverse foreign exchange movements.<br/><br/>

        <b>Hedge Relationship:</b> <br/>
        The FX forward contract is designated as a hedge of the first<font color="#007da5"> {currency} {Notional_value}M</font> million of net assets held in subsidiaries. The fair value changes of the FX forward contract will offset the translation gains or losses on the net investment in the subsidiaries attributable to changes in foreign exchange rates.<br/><br/>

        <b>Hedged Item:</b><br/> 
        The hedged item in this designation is the net investment in subsidiaries, representing the cumulative balance of the carrying amounts of the investments in the subsidiaries, including both equity and non-equity items, as translated at the applicable exchange rates.<br/><br/>

        <b>Hedging Instrument:</b><br/> 
        The designated hedging instrument is a<font color="#007da5"> {currency} {Notional_value}M</font> FX forward contract entered into with <font color="#007da5">{counterparty}</font>. The contract has a start date of <font color="#007da5">{start_date}</font> and a maturity date of <font color="#007da5">{maturity_date}</font>.<br/><br/>

        <b>Risk Management Objective and Strategy:</b><br/>
        The risk management objective is to reduce the volatility in the consolidated financial statements resulting from changes in foreign exchange rates. This strategy involves using the FX forward contract to mitigate the potential adverse impact of currency fluctuations on the value of our net investment in subsidiaries.<br/><br/>

        <b>Prospective Hedge Effectiveness Test:</b><br/>

        To demonstrate the prospective hedge effectiveness, let's consider an opening GBP/USD exchange rate of 1.2 and a maturity rate of 1.3.

        <br/>Change in Hedging Instrument Value: The designated hedging instrument value is<font color="#007da5"> {Notional_value}M</font>. As the GBP/USD exchange rate moves from 1.2 to 1.3, the change in the value of the FX forward contract denominated in GBP would be: 
        <br/><font color="#007da5">Variable 1 =( {currency} -{Notional_value}M /1.2) - ( {currency} -{Notional_value}M /1.3) 
        <br/>= -{answerr1}M - (-{answerr2})M = -{finall}M</font>

        <br/>Change in Valuation of Hedged Item: The change in the valuation of the hedged item, which represents the net investment in subsidiaries, would be calculated as follows:  
        <br/><font color="#007da5">Variable 2 =( {currency} {Notional_value}M /1.2) - ( {currency} {Notional_value}M /1.3) 
        <br/>= {answerr1}M - {answerr2}M = {finall}M</font>


        <br/>The prospective hedge effectiveness test shows that the change in the spot valuation of the hedging instrument variable1 is equal and opposite to the change in valuation of the hedged item variable2, thereby achieving a highly effective hedge.

        <br/>Documentation and Hedge Accounting: Comprehensive documentation will be maintained to support the hedge designation, including the risk management objective, the hedging strategy, and the effectiveness assessment results. Hedge accounting will be applied in accordance with the relevant provisions of IFRS 9 Financial Instruments and other applicable accounting standards.<br/><br/>

        <b>Disclosures:</b><br/>
        Appropriate disclosures will be made in our financial statements, as required by IFRS 7. These disclosures will cover the nature and extent of the risks arising from the net investment hedge, the risk management objectives and strategies, and the impact of the hedging activities on the financial statements.

        Unless any material changes occur, this document will not be updated until the maturity of the hedging instrument. However, ongoing monitoring of the hedge's effectiveness will be performed, as described above.<br/><br/>

        Please feel free to reach out if you have any questions or require further information.<br/><br/><br/>

        James Kelly<br/>
        SVP Treasury, Risk and Insurance<br/>
        Treasury<br/>
        Email: james.kelly1@pearson.com<br/>
        GB-London-80 Strand
        """
            report_content.append(Paragraph(file_note, styles['Normal']))
            report_content.append(Spacer(1, 24))
            report_content.append(PageBreak())
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        doc.build(report_content)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='NIH_FX_Report.pdf',
            mimetype='application/pdf'
        )
        
    return render_template('app3success.html')
