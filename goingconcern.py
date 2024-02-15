from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify, get_flashed_messages, flash, session
import pandas as pd
from functools import wraps
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
import math
import re
import ast
import os
import calendar
import inspect
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import plotly.graph_objects as go

goingconcern_blueprint = Blueprint('goingconcern', __name__, template_folder='templates5')


@goingconcern_blueprint.route('/netdebt', methods=['GET', 'POST'])
def netdebt():
    
    #Import the weightings to dataframe dfw
    dfw = pd.read_csv('modelfiles/goingconcern22weightings.csv', header=0)
    #Add cumulative calcs for Amortisation and Depreciation, profit and interest for the covenant calcs
    dfw['Cum_Sales_wt']=dfw['Sales wt'].cumsum()
    dfw['Cum_A&D_wt']=dfw['A&D_Weight'].cumsum()
    dfw["Cum_profit_wt"]=dfw["Profit wt"].cumsum()
    dfw["Cum_op_cash_wt"]=dfw["Op cash wt"].cumsum()
    dfw["Cum_op_cash_risk_wt"] = dfw["Op Cash Risk wt"].cumsum()
    dfw["Cum_interest_wt"]=dfw["Interest cash wt"].cumsum()
    #Extract the 6th row from each (representing the H1 weighting)
    H1_Sales_wt = dfw.loc[5,'Cum_Sales_wt']
    H1_AD_wt = dfw.loc[5,'Cum_A&D_wt']
    H1_profit_wt = dfw.loc[5,'Cum_profit_wt']
    H1_op_cash_wt = dfw.loc[5,'Cum_op_cash_wt']
    H1_op_cash_risk_wt = dfw.loc[5,'Cum_op_cash_risk_wt']
    H1_interest_cash_wt = dfw.loc[5,'Cum_interest_wt']
    
     
    
    #Create mini table for Half year weightings
    dfHYweights=pd.DataFrame()
    dfHYweights['Period']=["H1","H2"]
    dfHYweights['Sales']=[H1_Sales_wt,(1-H1_Sales_wt)]
    dfHYweights['Profit']=[H1_profit_wt,(1-H1_profit_wt)]
    dfHYweights['Op_cash']=[H1_op_cash_wt,(1-H1_op_cash_wt)]
    dfHYweights['Op_cash_risk']=[H1_op_cash_risk_wt,(1-H1_op_cash_risk_wt)]
    dfHYweights['A&D']=[H1_AD_wt,(1-H1_AD_wt)]
    dfHYweights['Interest']=[H1_interest_cash_wt,(1-H1_interest_cash_wt)]
    
     
    
    # Create blank dataframe
    df=pd.DataFrame()
    
     
    
    #Set exchange rate
    GBPUSD=1.22
    
     
    
    #Input P&L data
    df = pd.read_csv('modelfiles/TestuploadforPython20Dec.csv', header=0)
    
     
    
    #Create calculated fields
    df["Op cash post res"] = df["Op cash pre res"] + df["Restruct"]
    df["Free cash flow"] = df["Op cash post res"] + df["InterestCash"] + df["TaxCash"]
    df['Net debt change'] = df["Free cash flow"] + df["Dividends"] + df["Acqs&disps"] + df["New equity"] + df["Other"]
    df = df.round(decimals = 1)
    #Calculate net debt change (cumulative)
    df['Cum Net debt change'] = df['Net debt change'].cumsum()
    
        # Create the dataframe for the new phased cashflow dfp
    dfa=pd.DataFrame()
    dfb=pd.DataFrame()
    dftots=pd.DataFrame()
    #Import risks
    dfrisks = pd.read_csv('modelfiles/Risksuploadforgoingconcernmodel.csv', header=0)

    dfProfit = df[["Years","Sales","Profit","A&D","ETR","InterestP&L"]]



    #Insert 2022 opening net debt as x
    x=-350



    #Show number of risk scenarios
    Number = dfrisks.loc[0,"Number of scenarios"]
    dfa_list = []
    dfb_list = []
    dftots_list = []
    #Create scenario name list
    n=1
    while n<=Number: 
        if n==1:
            Scenlist=[dfrisks.loc[0,f"Scenario {n}"]]
        else:
            Scenlist.append(dfrisks.loc[0,f"Scenario {n}"])
        n=n+1
    #Create the iterative solution
    i=1
    while i<=Number:
        f=dfrisks.loc[0,f"Scenario {i}"]
        #Create variables to recall the names from the dataframe
        s = f + " sales impact"
        p = f + " profit impact"
        oc= f +" operating cashflow"
        int = f+ " Interest rate"
        tr = f + " Tax rate"
        tax = f +" Tax P&L"
        Tcash = f + " Tax cash"
        MA = f + " M&A"
        SBB = f + " share buyback"
        Predebt= f + " Debt pre interest"
        Intch = f + " Interest change"
        ND = f + " net debt upload"
        #Create new variable names to store the outputs
        sales = f + " sales final"
        profit = f + " profit final"
        amortdep = f + " amort/dep final"
        amort = f + " amort final"
        int_chg = f + " interest chg"
        op_cash = f + " oper cash"
        op_profit = f + " oper profit"
        op_sales = f + " oper sales"
        restr = f + " restructuring"
        restrp = f + " restructuring profit"
        restrs = f + " restructuring sales"
        intcash = f + " interest cash"
        txcash = f + " tax cash"
        dividends = f + " dividends"
        acqsdisps = f + " acqsdisps"
        newequity = f + " new equity"
        other = f + " other"
        opcashpostrestruc = f + " op cash pst"
        opprofitrestruc = f + " op profit pst"
        opsalesrestruc = f + " op sales pst"
        freecash = f + " free cash flow"
        othercash = f + " Shares,M&A,Other"
        netdebtch = f + " net debt change"
        ytdnetdebtch = f + " ytd net debt change"
        cumnetdebtch = f + " cumulative net debt"
        scennetdebt = f + " net debt"
        covebitda = f + " cov EBITDA"
        covnetdebt = f + " cov net debt"
        covleverage = f + " cov lev ratio"
        covdebthr = f + " cov debt headrm"
        covebitdahr = f + " cov EBITDA headrm"
        #Create the new columns storing the variables
        df[sales] = dfrisks[s] + df["Sales"]
        df[profit] = dfrisks[p] + df["Profit"]
        df[amortdep] = df["A&D"]
        df[amort] = df["Amort"]
        df[int_chg] = df["InterestP&L"] + dfrisks[Intch]
        df[op_cash] = df["Op cash pre res"] + dfrisks[oc]
        df[restr] = df["Restruct"]
        df[op_profit] = df["Profit"] + dfrisks[p]
        df[restrp] = df["Restruct"]
        df[op_sales] = df["Sales"] + dfrisks[s]
        df[restrs] = df["Restruct"]
        df[intcash] = df["InterestCash"] + dfrisks[Intch]
        df[txcash] = df["TaxCash"] + dfrisks[Tcash]
        df[dividends] = df["Dividends"]
        df[acqsdisps] = df["Acqs&disps"] + dfrisks[MA]
        df[newequity] = df["New equity"] + dfrisks[SBB]
        df[other] = df["Other"]
        df[opcashpostrestruc] = df[op_cash] + df[restr]
        df[opprofitrestruc] = df[op_profit] + df[restrp]
        df[opsalesrestruc] = df[op_sales] + df[restrs]
        df[freecash] = df[opcashpostrestruc] + df[intcash] + df[txcash]
        df[netdebtch] = df[freecash] + df[dividends] + df[acqsdisps] + df[newequity] + df[other]
        df[cumnetdebtch] = df[netdebtch].cumsum()
        df[scennetdebt] = df[cumnetdebtch] + x
        df[covebitda] = df[profit] - df[amortdep]
        df[covnetdebt] = df[scennetdebt] + df["Leases"]
        df[covleverage] = df[covnetdebt] / df[covebitda]
        df[covdebthr] = 4 * df[covebitda] + df[covnetdebt]
        df[covebitdahr] = ((df[covebitda]*4 + (df[covnetdebt]))/5)
        df = df.round(decimals = 2)
        #Create new phasings
        #dfb contains the elements of op cash flow for the downside scenarios (phased)
        #dfa contains the other elements below 
        yrs=str(dfProfit.loc[i,"Years"])
        Totyrs = len(df)
        j=0
        temp_dfa = pd.DataFrame()
        temp_dfb = pd.DataFrame()
        temp_dftots = pd.DataFrame()
        while j<Totyrs:
            yrs=str(dfProfit.loc[j,"Years"])
            temp_dftots[op_cash+f" {yrs}"]= df.loc[j,op_cash]*dfw['Op Cash Risk wt']
            temp_dfb[restr+f" {yrs}"]= df.loc[j,restr]*dfw['Restruct wt']
            temp_dfb[opcashpostrestruc+f" {yrs}"]=temp_dftots[op_cash+f" {yrs}"]+temp_dfb[restr+f" {yrs}"]
            temp_dfa[intcash+f" {yrs}"]=df.loc[j,intcash]*dfw['Interest cash wt']
            temp_dfa[txcash+f" {yrs}"]=df.loc[j,txcash]*dfw['Tax cash wt']
            temp_dfa[dividends+f" {yrs}"]=df.loc[j,dividends]*dfw['Dividends wt']
            temp_dfa[acqsdisps+f" {yrs}"]=df.loc[j,acqsdisps]*dfw['M&A wt']
            temp_dfa[newequity+f" {yrs}"]=df.loc[j,newequity]*dfw['Equity wt']
            temp_dfa[other+f" {yrs}"]=df.loc[j,other]*dfw['Other wt']
            temp_dftots[freecash+f" {yrs}"]= temp_dfb[opcashpostrestruc+f" {yrs}"]+temp_dfa[intcash+f" {yrs}"]+temp_dfa[txcash+f" {yrs}"]
            temp_dftots[othercash+f" {yrs}"]=+temp_dfa[dividends+f" {yrs}"]+temp_dfa[acqsdisps+f" {yrs}"]+temp_dfa[newequity+f" {yrs}"]+temp_dfa[other+f" {yrs}"]
            temp_dftots[netdebtch+f" {yrs}"]= temp_dftots[freecash+f" {yrs}"]+temp_dfa[dividends+f" {yrs}"]+temp_dfa[acqsdisps+f" {yrs}"]+temp_dfa[newequity+f" {yrs}"]+temp_dfa[other+f" {yrs}"]
            temp_dftots[ytdnetdebtch+f" {yrs}"]=temp_dftots[netdebtch+f" {yrs}"].cumsum()
            j=j+1
        i=i+1
        dfa_list.append(temp_dfa)
        dfb_list.append(temp_dfb)
        dftots_list.append(temp_dftots)

    # Concatenate all temporary DataFrames
    dfa = pd.concat(dfa_list, axis=1)
    dfb = pd.concat(dfb_list, axis=1)
    dftots = pd.concat(dftots_list, axis=1)

    # Create a dictionary to hold data for each scenario
    data_for_scenarios = {}

    # Iterate through each scenario
    for i in range(1, Number + 1):
        scenario_name = dfrisks.loc[0, f"Scenario {i}"]
        netdebtch_scenario = scenario_name + " net debt change"

        # Create a list for each year for this scenario
        data_for_scenarios[netdebtch_scenario] = []
        for year_index in range(len(dfProfit)):
            year = str(dfProfit.loc[year_index, "Years"])
            data_for_scenarios[netdebtch_scenario] += dftots[netdebtch_scenario + ' ' + year].tolist()


    #-------------------------------------------------------------------------------
    # liquidity RSS calculations LIQUID STARTS
    #------------------------------------------------------------------------------

    # Create the DataFrame for cashflows
    dfflowsrss = pd.DataFrame(data_for_scenarios)

    # Correct way to create column names dynamically and concatenate lists
    listrss = (dftots[netdebtch + ' ' + str(dfProfit.loc[0, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[1, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[2, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[3, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[4, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[5, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[6, "Years"])].tolist())

    #Insert the month and year !! THIS IS ONLY SET UP FOR 5 YEARS!!!! If more or less are used it won't work
    list2rss = dfw['Month'].tolist()*7
    list4rss = [str(dfProfit.loc[0,"Years"]),str(dfProfit.loc[0,"Years"])]
    list5rss = [str(dfProfit.loc[1,"Years"]),str(dfProfit.loc[1,"Years"])]
    list6rss = [str(dfProfit.loc[2,"Years"]),str(dfProfit.loc[2,"Years"])]
    list7rss = [str(dfProfit.loc[3,"Years"]),str(dfProfit.loc[3,"Years"])]
    list8rss = [str(dfProfit.loc[4,"Years"]),str(dfProfit.loc[4,"Years"])]
    list8arss = [str(dfProfit.loc[5,"Years"]),str(dfProfit.loc[5,"Years"])]
    list8brss = [str(dfProfit.loc[6,"Years"]),str(dfProfit.loc[6,"Years"])]
    list9rss = (list4rss*6)+(list5rss*6)+(list6rss*6)+(list7rss*6)+(list8rss*6)+(list8arss*6)+(list8brss*6)

    #Join annual free cashflows to create a single series
    list3rss = (dftots[freecash + ' ' + str(dfProfit.loc[0,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[1,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[2,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[3,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[4,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[5,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[6,"Years"])].tolist())

    dfflowsrss["Month"] = list2rss
    dfflowsrss["Years"] = list9rss
    dfflowsrss["Netcashchange"] = listrss

    # Function to convert full month name to abbreviated month name
    def abbreviate_month(full_month_name):
        # Create a dictionary mapping full month names to their abbreviations
        month_abbr_dict = {month: abbr for month, abbr in zip(calendar.month_name[1:], calendar.month_abbr[1:])}
        # Return the abbreviated month name
        return month_abbr_dict.get(full_month_name, full_month_name)  # Return original if not found

    # Read the bond repayment data from the spreadsheet
    bond_repayment_data = pd.read_csv('modelfiles/bonds.csv')

    # Convert full month names to abbreviated month names in dfflows
    dfflowsrss['Month'] = dfflowsrss['Month'].apply(abbreviate_month)

    # Create the 'Bond repayment' column in dfflows with default zero values
    dfflowsrss['Bond repayment'] = 0

    # Update 'Bond repayment' in dfflows based on the spreadsheet data
    for index, row in bond_repayment_data.iterrows():
        month_year_filter = (dfflowsrss['Month'] == row['Month']) & (dfflowsrss['Years'] == str(row['Year']))
        bond_repayment_value = pd.to_numeric(row['Bond Repayment'], errors='coerce')
        dfflowsrss.loc[month_year_filter, 'Bond repayment'] = bond_repayment_value

    # Read the RCF data from the spreadsheet
    RCF_data = pd.read_csv('modelfiles/RCF DATA.csv')

    # Convert full month names to abbreviated month names in dfflows
    dfflowsrss['Month'] = dfflowsrss['Month'].apply(abbreviate_month)

    # Create the 'RCF' column in dfflows with default zero values
    dfflowsrss['RCF'] = 0

    # First, set the 'RCF' for each year where the 'Month' is not specified
    for index, row in RCF_data[pd.isnull(RCF_data['Month'])].iterrows():
        year_filter = dfflowsrss['Years'] == str(row['Year'])
        RCF_value = pd.to_numeric(row['RCF'], errors='coerce')
        dfflowsrss.loc[year_filter, 'RCF'] = RCF_value

    # Then, update the 'RCF' for specific months
    for index, row in RCF_data[pd.notnull(RCF_data['Month'])].iterrows():
        month_year_filter = (dfflowsrss['Month'] == row['Month']) & (dfflowsrss['Years'] == str(row['Year']))
        RCF_value = pd.to_numeric(row['RCF'], errors='coerce')
        dfflowsrss.loc[month_year_filter, 'RCF'] = RCF_value

    # Function to calculate 'cash movement overtime'
    def calculate_cash_movement_overtime(df):
        df['cash movement overtime'] = [728] + [np.nan] * (len(df) - 1)
        for i in range(1, len(df)):
            cash_movement = df.loc[i - 1, 'cash movement overtime']
            net_cash_change = df.loc[i, 'Netcashchange']
            bond_repayment = df.loc[i, 'Bond repayment']
            df.loc[i, 'cash movement overtime'] = cash_movement + net_cash_change - bond_repayment
        df['cash movement overtime'].fillna(method='ffill', inplace=True)
        return df

    # Assuming Scenlist[0] contains the name of your first scenario
    scenario_name = Scenlist[0]
    netdebtch_scenario = scenario_name + " net debt change"
    liquidity_scenario = scenario_name + " Liquidity"

    # Copy relevant columns from dfflowsrss DataFrame
    temp_df = dfflowsrss[['Month', 'Years', netdebtch_scenario, 'Bond repayment']].copy()

    # Rename the scenario column to 'Netcashchange'
    temp_df.rename(columns={netdebtch_scenario: 'Netcashchange'}, inplace=True)

    # Calculate 'cash movement overtime' for the temporary DataFrame
    temp_df = calculate_cash_movement_overtime(temp_df)

    # Calculate liquidity for the scenario
    temp_df['Liquidity'] = temp_df['cash movement overtime'] + dfflowsrss['RCF']

    temp_df["MonthYears"] = temp_df["Month"] + temp_df["Years"]
    temp_df["MonthYears"] = pd.to_datetime(temp_df["MonthYears"], format='%b%Y')
    # Store the liquidity DataFrame for this scenario in a variable
    globals()[liquidity_scenario] = temp_df[['Month', 'Years', 'MonthYears', 'Liquidity']]

    # Optionally, add the liquidity values to dfflowsrss if needed
    dfflowsrss['liquidity_scenario'] = temp_df['Liquidity']

    # Now you have the DataFrame for the first scenario's liquidity
    dfflowsrss["MonthYears"] = dfflowsrss["Month"] + dfflowsrss["Years"]
    dfflowsrss["MonthYears"] = pd.to_datetime(dfflowsrss["MonthYears"], format='%b%Y')

    #-------------------------------------------------------------------------------
    # liquidity RSS calculations ENDS
    #--------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------
    # liquidity SBP calculations LIQUID STARTS
    #------------------------------------------------------------------------------

    # Create the DataFrame for cashflows
    dfflowssbp = pd.DataFrame(data_for_scenarios)

    # Correct way to create column names dynamically and concatenate lists
    listsbp = (dftots[netdebtch + ' ' + str(dfProfit.loc[0, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[1, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[2, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[3, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[4, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[5, "Years"])].tolist() +
            dftots[netdebtch + ' ' + str(dfProfit.loc[6, "Years"])].tolist())

    #Insert the month and year !! THIS IS ONLY SET UP FOR 5 YEARS!!!! If more or less are used it won't work
    list2sbp = dfw['Month'].tolist()*7
    list4sbp = [str(dfProfit.loc[0,"Years"]),str(dfProfit.loc[0,"Years"])]
    list5sbp = [str(dfProfit.loc[1,"Years"]),str(dfProfit.loc[1,"Years"])]
    list6sbp = [str(dfProfit.loc[2,"Years"]),str(dfProfit.loc[2,"Years"])]
    list7sbp = [str(dfProfit.loc[3,"Years"]),str(dfProfit.loc[3,"Years"])]
    list8sbp = [str(dfProfit.loc[4,"Years"]),str(dfProfit.loc[4,"Years"])]
    list8asbp = [str(dfProfit.loc[5,"Years"]),str(dfProfit.loc[5,"Years"])]
    list8bsbp = [str(dfProfit.loc[6,"Years"]),str(dfProfit.loc[6,"Years"])]
    list9sbp = (list4sbp*6)+(list5sbp*6)+(list6sbp*6)+(list7sbp*6)+(list8sbp*6)+(list8asbp*6)+(list8bsbp*6)

    #Join annual free cashflows to create a single series
    list3sbp = (dftots[freecash + ' ' + str(dfProfit.loc[0,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[1,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[2,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[3,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[4,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[5,"Years"])].tolist()+
                dftots[freecash + ' ' + str(dfProfit.loc[6,"Years"])].tolist())

    dfflowssbp["Month"] = list2rss
    dfflowssbp["Years"] = list9rss
    dfflowssbp["Netcashchange"] = listrss

    # Function to convert full month name to abbreviated month name
    def abbreviate_month(full_month_name):
        # Create a dictionary mapping full month names to their abbreviations
        month_abbr_dict = {month: abbr for month, abbr in zip(calendar.month_name[1:], calendar.month_abbr[1:])}
        # Return the abbreviated month name
        return month_abbr_dict.get(full_month_name, full_month_name)  # Return original if not found

    # Read the bond repayment data from the spreadsheet
    bond_repayment_data = pd.read_csv('modelfiles/bonds.csv')

    # Convert full month names to abbreviated month names in dfflows
    dfflowssbp['Month'] = dfflowssbp['Month'].apply(abbreviate_month)

    # Create the 'Bond repayment' column in dfflows with default zero values
    dfflowssbp['Bond repayment'] = 0

    # Update 'Bond repayment' in dfflows based on the spreadsheet data
    for index, row in bond_repayment_data.iterrows():
        month_year_filter = (dfflowssbp['Month'] == row['Month']) & (dfflowssbp['Years'] == str(row['Year']))
        bond_repayment_value = pd.to_numeric(row['Bond Repayment'], errors='coerce')
        dfflowssbp.loc[month_year_filter, 'Bond repayment'] = bond_repayment_value

    # Read the RCF data from the spreadsheet
    RCF_data = pd.read_csv('modelfiles/RCF DATA.csv')

    # Convert full month names to abbreviated month names in dfflows
    dfflowssbp['Month'] = dfflowssbp['Month'].apply(abbreviate_month)

    # Create the 'RCF' column in dfflows with default zero values
    dfflowssbp['RCF'] = 0

    # First, set the 'RCF' for each year where the 'Month' is not specified
    for index, row in RCF_data[pd.isnull(RCF_data['Month'])].iterrows():
        year_filter = dfflowssbp['Years'] == str(row['Year'])
        RCF_value = pd.to_numeric(row['RCF'], errors='coerce')
        dfflowssbp.loc[year_filter, 'RCF'] = RCF_value

    # Then, update the 'RCF' for specific months
    for index, row in RCF_data[pd.notnull(RCF_data['Month'])].iterrows():
        month_year_filter = (dfflowssbp['Month'] == row['Month']) & (dfflowssbp['Years'] == str(row['Year']))
        RCF_value = pd.to_numeric(row['RCF'], errors='coerce')
        dfflowssbp.loc[month_year_filter, 'RCF'] = RCF_value

    # Function to calculate 'cash movement overtime'
    def calculate_cash_movement_overtime(df):
        df['cash movement overtime'] = [728] + [np.nan] * (len(df) - 1)
        for i in range(1, len(df)):
            cash_movement = df.loc[i - 1, 'cash movement overtime']
            net_cash_change = df.loc[i, 'Netcashchange']
            bond_repayment = df.loc[i, 'Bond repayment']
            df.loc[i, 'cash movement overtime'] = cash_movement + net_cash_change - bond_repayment
        df['cash movement overtime'].fillna(method='ffill', inplace=True)
        return df

    # Assuming Scenlist[0] contains the name of your first scenario
    scenario_name = Scenlist[1]
    netdebtch_scenario = scenario_name + " net debt change"
    liquidity_scenario = scenario_name + " Liquidity"

    # Copy relevant columns from dfflowssbp DataFrame
    tempsbp_df = dfflowssbp[['Month', 'Years', netdebtch_scenario, 'Bond repayment']].copy()

    # Rename the scenario column to 'Netcashchange'
    tempsbp_df.rename(columns={netdebtch_scenario: 'Netcashchange'}, inplace=True)

    # Calculate 'cash movement overtime' for the temporary DataFrame
    tempsbp_df = calculate_cash_movement_overtime(tempsbp_df)

    # Calculate liquidity for the scenario
    tempsbp_df['Liquidity'] = tempsbp_df['cash movement overtime'] + dfflowssbp['RCF']

    tempsbp_df["MonthYears"] = tempsbp_df["Month"] + tempsbp_df["Years"]
    tempsbp_df["MonthYears"] = pd.to_datetime(tempsbp_df["MonthYears"], format='%b%Y')
    # Store the liquidity DataFrame for this scenario in a variable
    globals()[liquidity_scenario] = tempsbp_df[['Month', 'Years', 'MonthYears', 'Liquidity']]

    # Optionally, add the liquidity values to dfflowssbp if needed
    dfflowssbp['liquidity_scenario'] = tempsbp_df['Liquidity']

    # Now you have the DataFrame for the first scenario's liquidity
    dfflowssbp["MonthYears"] = dfflowssbp["Month"] + dfflowssbp["Years"]
    dfflowssbp["MonthYears"] = pd.to_datetime(dfflowssbp["MonthYears"], format='%b%Y')

    #-------------------------------------------------------------------------------
    # liquidity SBP calculations ENDS
    #--------------------------------------------------------------------------------
         
    
    df["Net debt"] = df['Cum Net debt change'] + x
    df["GBPRCF"] = df["RCF"]/GBPUSD
    dfNetdebt = df[["Years",'Net debt',f"{Scenlist[0]} net debt",f"{Scenlist[1]} net debt",f"{Scenlist[2]} net debt"]]
    # Round the table here
    dfNetdebt = dfNetdebt.round(decimals = 1)
    
    
     
    
    dfOpcashpostrestruc = df[["Years","Op cash post res",f"{Scenlist[0]} op cash pst",f"{Scenlist[1]} op cash pst",f"{Scenlist[2]} op cash pst"]]
    pd.set_option("display.max_columns",None)
    
    
    dfOpprofitrestruc = df[["Years","Profit",f"{Scenlist[0]} op profit pst",f"{Scenlist[1]} op profit pst",f"{Scenlist[2]} op profit pst"]]
    pd.set_option("display.max_columns",None)
    
    
    dfOpsalesrestruc = df[["Years","Sales",f"{Scenlist[0]} op sales pst",f"{Scenlist[1]} op sales pst",f"{Scenlist[2]} op sales pst"]]
    pd.set_option("display.max_columns",None)
    
    #----------------------------------------------------------------------------------------
    # Begining of 5+7 calculations
    #----------------------------------------------------------------------------------------
    #Import the weightings to dataframe dfw
    fsdfw = pd.read_csv('modelfiles/5+7 goingconcern22weightings.csv', header=0)
    #Add cumulative calcs for Amortisation and Depreciation, profit and interest for the covenant calcs
    fsdfw['Cum_Sales_wt']=fsdfw['Sales wt'].cumsum()
    fsdfw['Cum_A&D_wt']=fsdfw['A&D_Weight'].cumsum()
    fsdfw["Cum_profit_wt"]=fsdfw["Profit wt"].cumsum()
    fsdfw["Cum_op_cash_wt"]=fsdfw["Op cash wt"].cumsum()
    fsdfw["Cum_interest_wt"]=fsdfw["Interest cash wt"].cumsum()
    #Extract the 6th row from each (representing the H1 weighting)
    fsH1_Sales_wt = fsdfw.loc[5,'Cum_Sales_wt']
    fsH1_AD_wt = fsdfw.loc[5,'Cum_A&D_wt']
    fsH1_profit_wt = fsdfw.loc[5,'Cum_profit_wt']
    fsH1_op_cash_wt = fsdfw.loc[5,'Cum_op_cash_wt']
    fsH1_interest_cash_wt = fsdfw.loc[5,'Cum_interest_wt']
    
    
    #Create mini table for Half year weightings
    fsdfHYweights=pd.DataFrame()
    fsdfHYweights['Period']=["H1","H2"]
    fsdfHYweights['Sales']=[fsH1_Sales_wt,(1-fsH1_Sales_wt)]
    fsdfHYweights['Profit']=[fsH1_profit_wt,(1-fsH1_profit_wt)]
    fsdfHYweights['Op_cash']=[fsH1_op_cash_wt,(1-fsH1_op_cash_wt)]
    fsdfHYweights['A&D']=[fsH1_AD_wt,(1-fsH1_AD_wt)]
    fsdfHYweights['Interest']=[fsH1_interest_cash_wt,(1-fsH1_interest_cash_wt)]
    
    
    # Create blank dataframe
    fsdf=pd.DataFrame()
    
    
    #Set exchange rate
    GBPUSD=1.22
    
    #Input P&L data
    fsdf = pd.read_csv('modelfiles/5+7TestuploadforPython20Dec.csv', header=0)
    
    #Create calculated fields
    fsdf["Op cash post res"] = fsdf["Op cash pre res"] + fsdf["Restruct"]
    fsdf["Free cash flow"] = fsdf["Op cash post res"] + fsdf["InterestCash"] + fsdf["TaxCash"]
    fsdf['Net debt change'] = fsdf["Free cash flow"] + fsdf["Dividends"] + fsdf["Acqs&disps"] + fsdf["New equity"] + fsdf["Other"]
    fsdf = fsdf.round(decimals = 1)
    #Calculate net debt change (cumulative)
    fsdf['Cum Net debt change'] = fsdf['Net debt change'].cumsum()
    
     
    
    # Create the dataframe for the new phased cashflow dfp
    fsdfa=pd.DataFrame()
    fsdfb=pd.DataFrame()
    fsdftots=pd.DataFrame()
    #Import risks
    fsdfrisks = pd.read_csv('modelfiles/5+7Risksuploadforgoingconcernmodel.csv', header=0)
    
    fsdfProfit = df[["Years","Sales","Profit","A&D","ETR","InterestP&L"]]
    
    
     
    
    #Insert 2022 opening net debt as x
    x=-350 
    
    #Create scenario name list
    n=1
    while n<=Number: 
      if n==1:
        fsScenlist=[fsdfrisks.loc[0,f"Scenario {n}"]]
      else:
        fsScenlist.append(fsdfrisks.loc[0,f"Scenario {n}"])
      n=n+1
    #Create the iterative solution
    i=1
    while i<=Number:
      f=fsdfrisks.loc[0,f"Scenario {i}"]
      #Create variables to recall the names from the dataframe
      s = f + " sales impact"
      p = f + " profit impact"
      oc= f +" operating cashflow"
      int = f+ " Interest rate"
      tr = f + " Tax rate"
      tax = f +" Tax P&L"
      Tcash = f + " Tax cash"
      MA = f + " M&A"
      SBB = f + " share buyback"
      Predebt= f + " Debt pre interest"
      Intch = f + " Interest change"
      ND = f + " net debt upload"
      #Create new variable names to store the outputs
      sales = f + " sales final"
      profit = f + " profit final"
      amortdep = f + " amort/dep final"
      amort = f + " amort final"
      int_chg = f + " interest chg"
      op_cash = f + " oper cash"
      op_profit = f + " oper profit"
      op_sales = f + " oper sales"
      restr = f + " restructuring"
      restrp = f + " restructuring profit"
      restrs = f + " restructuring sales"
      intcash = f + " interest cash"
      txcash = f + " tax cash"
      dividends = f + " dividends"
      acqsdisps = f + " acqsdisps"
      newequity = f + " new equity"
      other = f + " other"
      opcashpostrestruc = f + " op cash pst"
      opprofitrestruc = f + " op profit pst"
      opsalesrestruc = f + " op sales pst"
      freecash = f + " free cash flow"
      othercash = f + " Shares,M&A,Other"
      netdebtch = f + " net debt change"
      ytdnetdebtch = f + " ytd net debt change"
      cumnetdebtch = f + " cumulative net debt"
      scennetdebt = f + " net debt"
      covebitda = f + " cov EBITDA"
      covnetdebt = f + " cov net debt"
      covleverage = f + " cov lev ratio"
      covdebthr = f + " cov debt headrm"
      covebitdahr = f + " cov EBITDA headrm"
      #Create the new columns storing the variables
      fsdf[sales] = fsdfrisks[s] + fsdf["Sales"]
      fsdf[profit] = fsdfrisks[p] + fsdf["Profit"]
      fsdf[amortdep] = fsdf["A&D"]
      fsdf[amort] = fsdf["Amort"]
      df[int_chg] = fsdf["InterestP&L"] + fsdfrisks[Intch]
      fsdf[op_cash] = fsdf["Op cash pre res"] + fsdfrisks[oc]
      fsdf[restr] = fsdf["Restruct"]
      fsdf[op_profit] = fsdf["Profit"] + dfrisks[p]
      fsdf[restrp] = fsdf["Restruct"]
      fsdf[op_sales] = fsdf["Sales"] + fsdfrisks[s]
      fsdf[restrs] = fsdf["Restruct"]
      fsdf[intcash] = fsdf["InterestCash"] + fsdfrisks[Intch]
      fsdf[txcash] = fsdf["TaxCash"] + fsdfrisks[Tcash]
      fsdf[dividends] = fsdf["Dividends"]
      fsdf[acqsdisps] = fsdf["Acqs&disps"] + fsdfrisks[MA]
      fsdf[newequity] = fsdf["New equity"] + fsdfrisks[SBB]
      fsdf[other] = fsdf["Other"]
      fsdf[opcashpostrestruc] = fsdf[op_cash] + fsdf[restr]
      fsdf[opprofitrestruc] = fsdf[op_profit] + fsdf[restrp]
      fsdf[opsalesrestruc] = fsdf[op_sales] + fsdf[restrs]
      fsdf[freecash] = fsdf[opcashpostrestruc] + fsdf[intcash] + fsdf[txcash]
      fsdf[netdebtch] = fsdf[freecash] + fsdf[dividends] + fsdf[acqsdisps] + fsdf[newequity] + fsdf[other]
      fsdf[cumnetdebtch] = fsdf[netdebtch].cumsum()
      fsdf[scennetdebt] = fsdf[cumnetdebtch] + x
      fsdf[covebitda] = fsdf[profit] - fsdf[amortdep]
      fsdf[covnetdebt] = fsdf[scennetdebt] + fsdf["Leases"]
      fsdf[covleverage] = fsdf[covnetdebt] / fsdf[covebitda]
      fsdf[covdebthr] = 4 * fsdf[covebitda] + fsdf[covnetdebt]
      fsdf[covebitdahr] = ((fsdf[covebitda]*4 + (fsdf[covnetdebt]))/5)
      fsdf = fsdf.round(decimals = 2)
      #Create new phasings
      #dfb contains the elements of op cash flow for the downside scenarios (phased)
      #dfa contains the other elements below 
      yrs=str(fsdfProfit.loc[i,"Years"])
      Totyrs = len(fsdf)
      j=0
      while j<Totyrs:
        yrs=str(fsdfProfit.loc[j,"Years"])
        fsdftots[op_cash+f" {yrs}"]= fsdf.loc[j,op_cash]*fsdfw['Op cash wt']
        fsdfb[restr+f" {yrs}"]= fsdf.loc[j,restr]*fsdfw['Restruct wt']
        fsdfb[opcashpostrestruc+f" {yrs}"]=fsdftots[op_cash+f" {yrs}"]+fsdfb[restr+f" {yrs}"]
        fsdfa[intcash+f" {yrs}"]=fsdf.loc[j,intcash]*fsdfw['Interest cash wt']
        fsdfa[txcash+f" {yrs}"]=fsdf.loc[j,txcash]*fsdfw['Tax cash wt']
        fsdfa[dividends+f" {yrs}"]=fsdf.loc[j,dividends]*fsdfw['Dividends wt']
        fsdfa[acqsdisps+f" {yrs}"]=fsdf.loc[j,acqsdisps]*fsdfw['M&A wt']
        fsdfa[newequity+f" {yrs}"]=fsdf.loc[j,newequity]*fsdfw['Equity wt']
        fsdfa[other+f" {yrs}"]=fsdf.loc[j,other]*fsdfw['Other wt']
        fsdftots[freecash+f" {yrs}"]= fsdfb[opcashpostrestruc+f" {yrs}"]+fsdfa[intcash+f" {yrs}"]+fsdfa[txcash+f" {yrs}"]
        fsdftots[othercash+f" {yrs}"]=+fsdfa[dividends+f" {yrs}"]+fsdfa[acqsdisps+f" {yrs}"]+fsdfa[newequity+f" {yrs}"]+fsdfa[other+f" {yrs}"]
        fsdftots[netdebtch+f" {yrs}"]= fsdftots[freecash+f" {yrs}"]+fsdfa[dividends+f" {yrs}"]+fsdfa[acqsdisps+f" {yrs}"]+fsdfa[newequity+f" {yrs}"]+fsdfa[other+f" {yrs}"]
        fsdftots[ytdnetdebtch+f" {yrs}"]=fsdftots[netdebtch+f" {yrs}"].cumsum()
        #if j==0:
          #globals()[Scenlist[(i-1)]+"Netdebtchange"]=dftots[cumnetdebtch+" " +str(dfProfit.loc[j,"Years"])].tolist()
        #else:
          #globals()[Scenlist[(i-1)]+"Netdebtchange"].append(dftots[cumnetdebtch+" " +str(dfProfit.loc[j,"Years"])].tolist())
        j=j+1
      i=i+1
    
     
    
    
    fsdf["Net debt"] = fsdf['Cum Net debt change'] + x
    fsdf["GBPRCF"] = fsdf["RCF"]/GBPUSD
    fsdfNetdebt = fsdf[["Years",'Net debt',f"{Scenlist[0]} net debt",f"{Scenlist[1]} net debt",f"{Scenlist[2]} net debt"]]
    # Round the table here
    fsdfNetdebt = fsdfNetdebt.round(decimals = 1)
    
     
    
    fsdfOpcashpostrestruc = fsdf[["Years","Op cash post res",f"{Scenlist[0]} op cash pst",f"{Scenlist[1]} op cash pst",f"{Scenlist[2]} op cash pst"]]
    pd.set_option("display.max_columns",None)
    
    fsdfOpprofitrestruc = fsdf[["Years","Profit",f"{Scenlist[0]} op profit pst",f"{Scenlist[1]} op profit pst",f"{Scenlist[2]} op profit pst"]]
    pd.set_option("display.max_columns",None)
    
    
    fsdfOpsalesrestruc = fsdf[["Years","Sales",f"{Scenlist[0]} op sales pst",f"{Scenlist[1]} op sales pst",f"{Scenlist[2]} op sales pst"]]
    pd.set_option("display.max_columns",None)
    
    
    #----------------------------------------------------------------------------------------
    # Ending of 5+7 calculations.......
    #----------------------------------------------------------------------------------------
    
    
     # Calculate covenant headroom - Net debt to EBITDA
    df_covenant_calcs = pd.DataFrame({
        "Cov EBITDA": df['Profit'] - df['A&D'],
        "Cov Net Debt": df["Net debt"] + df["Leases"]
    })
    
    df_covenant_calcs["Cov Leverage ratio"] = df_covenant_calcs["Cov Net Debt"] / df_covenant_calcs["Cov EBITDA"]
    df_covenant_calcs["Cov debt headroom"] = 4 * df_covenant_calcs["Cov EBITDA"] + df_covenant_calcs["Cov Net Debt"]
    df_covenant_calcs["Cov EBITDA headroom"] = ((df_covenant_calcs["Cov EBITDA"] * 4 + df_covenant_calcs["Cov Net Debt"]) / 5)
    
    # Combine the calculations back into the main df
    df = pd.concat([df, df_covenant_calcs.round(decimals=1)], axis=1)
    
    # Calculate covenant headroom - Interest to EBITA
    df_covenant_interest_calcs = pd.DataFrame({
        "Cov EBITA": df["Profit"] - df["Amort"],
        "Cov Interest": df["InterestP&L"] - df["LeaseInterest"]
    })
    
    df_covenant_interest_calcs["Cov Interest cover"] = -df_covenant_interest_calcs["Cov EBITA"] / df_covenant_interest_calcs["Cov Interest"]
    df_covenant_interest_calcs["Cov profit headroom"] = df_covenant_interest_calcs["Cov EBITA"] + (3 * df_covenant_interest_calcs["Cov Interest"])
    
    # Combine the calculations back into the main df
    df = pd.concat([df, df_covenant_interest_calcs.round(decimals=1)], axis=1)
    
    
    #----------------------Phased cashflow--------------
    
     
    
    # Create the dataframe for the new phased cashflow dfp
    dfp=pd.DataFrame()
    
     
    
    #Apply the weightings to calculate the operating cashflow per month
    Totyrs = len(df)
    i=0
    while i<Totyrs:
      yrs=str(dfProfit.loc[i,"Years"])
      dfp['Op_cash '+yrs] = df.loc[i,"Op cash pre res"] * dfw['Op cash wt']
      dfp['Restruc '+yrs] = df.loc[i,"Restruct"] * dfw['Restruct wt']
      dfp['Net Operating CF '+yrs] = dfp[('Op_cash '+yrs)]+ dfp[('Restruc '+yrs)]
      dfp['InterestCash '+yrs] = df.loc[i,"InterestCash"] * dfw['Interest cash wt']
      dfp['TaxCash '+yrs] = df.loc[i,"TaxCash"] * dfw['Tax cash wt']
      dfp['Dividends '+yrs] = df.loc[i,"Dividends"] * dfw['Dividends wt']
      dfp['M&A '+yrs] = df.loc[i,"Acqs&disps"] * dfw['M&A wt']
      dfp['Equity '+yrs] = df.loc[i,"New equity"] * dfw['Equity wt']
      dfp['Otherflows '+yrs] = df.loc[i,"Other"] * dfw['Other wt']
      dfp['Free Cashflow '+yrs] = dfp[('Net Operating CF '+yrs)]+ dfp[('InterestCash '+yrs)]+ dfp[('TaxCash '+yrs)]
      dfp['Shares,M&A,Other '+yrs] = dfp[('Dividends '+yrs)]+ dfp[('M&A '+yrs)]+ dfp[('Otherflows '+yrs)]+ dfp[('Equity '+yrs)]
      dfp['Net Cashflow '+yrs] = dfp[('Free Cashflow '+yrs)]+ dfp[('Shares,M&A,Other '+yrs)]
      dfp['YTD Net Cashflow '+yrs] = dfp['Net Cashflow '+yrs].cumsum()
      i=i+1

   #------------------LiquidityBase Varianle ----------------------------------- 
    #Join annual net cashflows to create a single series
    list = dfp['Net Cashflow '+str(dfProfit.loc[0,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[1,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[2,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[3,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[4,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[5,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[6,"Years"])].tolist()
    
     
    
    #Print the dataframe
    #Insert the month and year !! THIS IS ONLY SET UP FOR 5 YEARS!!!! If more or less are used it won't work
    list2 = dfw['Month'].tolist()*7
    list4 = [str(dfProfit.loc[0,"Years"]),str(dfProfit.loc[0,"Years"])]
    list5 = [str(dfProfit.loc[1,"Years"]),str(dfProfit.loc[1,"Years"])]
    list6 = [str(dfProfit.loc[2,"Years"]),str(dfProfit.loc[2,"Years"])]
    list7 = [str(dfProfit.loc[3,"Years"]),str(dfProfit.loc[3,"Years"])]
    list8 = [str(dfProfit.loc[4,"Years"]),str(dfProfit.loc[4,"Years"])]
    list8a = [str(dfProfit.loc[5,"Years"]),str(dfProfit.loc[5,"Years"])]
    list8b = [str(dfProfit.loc[6,"Years"]),str(dfProfit.loc[6,"Years"])]
    list9 = (list4*6)+(list5*6)+(list6*6)+(list7*6)+(list8*6)+(list8a*6)+(list8b*6)
    #Join annual free cashflows to create a single series
    list3 = dfp['Free Cashflow '+str(dfProfit.loc[0,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[1,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[2,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[3,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[4,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[5,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[6,"Years"])].tolist()
    
     
    
    #Create dataframe to show each year's cashflows
    dfp['Month']=dfw["Month"]



    #Create a dataframe for cashflows
    dfflows=pd.DataFrame()
    dfflows["Month"] = list2
    dfflows["Years"] = list9
    dfflows["Netcashchange"] = list


    #-------------------------------------------------------------------------------
    # liquidity calculations starts
    #------------------------------------------------------------------------
    # Function to convert full month name to abbreviated month name
    def abbreviate_month(full_month_name):
        # Create a dictionary mapping full month names to their abbreviations
        month_abbr_dict = {month: abbr for month, abbr in zip(calendar.month_name[1:], calendar.month_abbr[1:])}
        # Return the abbreviated month name
        return month_abbr_dict.get(full_month_name, full_month_name)  # Return original if not found

    # Read the bond repayment data from the spreadsheet
    bond_repayment_data = pd.read_csv('modelfiles/bonds.csv')

    # Convert full month names to abbreviated month names in dfflows
    dfflows['Month'] = dfflows['Month'].apply(abbreviate_month)

    # Create the 'Bond repayment' column in dfflows with default zero values
    dfflows['Bond repayment'] = 0

    # Update 'Bond repayment' in dfflows based on the spreadsheet data
    for index, row in bond_repayment_data.iterrows():
        month_year_filter = (dfflows['Month'] == row['Month']) & (dfflows['Years'] == str(row['Year']))
        bond_repayment_value = pd.to_numeric(row['Bond Repayment'], errors='coerce')
        dfflows.loc[month_year_filter, 'Bond repayment'] = bond_repayment_value

    # Read the RCF data from the spreadsheet
    RCF_data = pd.read_csv('modelfiles/RCF DATA.csv')

    # Convert full month names to abbreviated month names in dfflows
    dfflows['Month'] = dfflows['Month'].apply(abbreviate_month)

    # Create the 'RCF' column in dfflows with default zero values
    dfflows['RCF'] = 0

    # First, set the 'RCF' for each year where the 'Month' is not specified
    for index, row in RCF_data[pd.isnull(RCF_data['Month'])].iterrows():
        year_filter = dfflows['Years'] == str(row['Year'])
        RCF_value = pd.to_numeric(row['RCF'], errors='coerce')
        dfflows.loc[year_filter, 'RCF'] = RCF_value

    # Then, update the 'RCF' for specific months
    for index, row in RCF_data[pd.notnull(RCF_data['Month'])].iterrows():
        month_year_filter = (dfflows['Month'] == row['Month']) & (dfflows['Years'] == str(row['Year']))
        RCF_value = pd.to_numeric(row['RCF'], errors='coerce')
        dfflows.loc[month_year_filter, 'RCF'] = RCF_value

    # Initialize 'cash movement overtime' with the first value as 728 and the rest as NaN
    dfflows['cash movement overtime'] = [728] + [np.nan] * (len(dfflows) - 1)

    # Calculate 'cash movement overtime' for each row
    for i in range(1, len(dfflows)):
        # Ensure all values are numeric for the calculation
        cash_movement = dfflows.loc[i - 1, 'cash movement overtime']
        net_cash_change = dfflows.loc[i, 'Netcashchange']
        bond_repayment = dfflows.loc[i, 'Bond repayment']
        dfflows.loc[i, 'cash movement overtime'] = cash_movement + net_cash_change - bond_repayment

    # Fill in the NaN values with the correct calculations
    dfflows['cash movement overtime'].fillna(method='ffill', inplace=True)

    # base liquidity calculations starts
    #------------------------------------------------------------------------
    dfflows['Liquidity Base scenairo'] = dfflows['cash movement overtime'] + dfflows['RCF']

    #-------------------------------------------------------------------------------
    # liquidity calculations ENDS
    #------------------------------------------------------------------------------

    dfflows["Freecashchange"] = list3
    dfflows['Cum Net debt change'] = dfflows['Netcashchange'].cumsum()
    dfflows["Net debt"] = dfflows['Cum Net debt change'] + x
    dfflows["MonthYears"] = dfflows["Month"] + dfflows["Years"]
    dfflows["MonthYears"] = pd.to_datetime(dfflows["MonthYears"], format='%b%Y')
    # Extracting June and December values for each year
    june_df = dfflows[dfflows["Month"] == "Jun"][["Years", "Net debt"]]
    december_df = dfflows[dfflows["Month"] == "Dec"][["Years", "Net debt"]]

    # Creating dictionaries for H1 and H2 values
    h1_dict = dict(zip(june_df["Years"], june_df["Net debt"]))
    h2_dict = dict(zip(december_df["Years"], december_df["Net debt"]))

    
        
        
    
    Scen_number=len(Scenlist)
    Years=df["Years"]
    #Section to create full phased model....
    a=0
    b=0
    while a<Scen_number:
      while b<Totyrs:
        if b==0:
          list=(dftots[Scenlist[a]+" net debt change "+str(Years[b])].tolist())
        else:
          list=list+(dftots[Scenlist[a]+" net debt change "+str(Years[b])].tolist())
        #print(list)
        b=b+1
      b=0
      dfflows[f"Scen{a+1}netdebtchange"]=list
      a=a+1
    
     
    
    #End of section on downside scenarios
    dfflows['Scen1cumnetdebt']=dfflows['Scen1netdebtchange'].cumsum()
    dfflows['Scen2cumnetdebt']=dfflows['Scen2netdebtchange'].cumsum()
    dfflows['Scen3cumnetdebt']=dfflows['Scen3netdebtchange'].cumsum()
    dfflows['Scen1netdebt']=dfflows['Scen1cumnetdebt']+x
    dfflows['Scen2netdebt']=dfflows['Scen2cumnetdebt']+x
    dfflows['Scen3netdebt']=dfflows['Scen3cumnetdebt']+x
    
    
    # Extract the month from 'MonthYears' column
    dfflows['Month'] = dfflows['MonthYears'].dt.month
    

    #----------------------------------------------------------------------------------------
    #start
    # Create a new dataframe where Month is June or December
    # Note: Month in datetime is represented by integers where January is 1 and December is 12
    #----------------------------------------------------------------------------------------

    df_filtered = dfflows[(dfflows['Month'] == 6) | (dfflows['Month'] == 12)][['Net debt', 'Scen1cumnetdebt', 'Scen2cumnetdebt', 'Scen3cumnetdebt']]


    # Create a new dataframe with only the specified columns and where Month is June or December
    df_filtered = dfflows[(dfflows['Month'] == 6) | (dfflows['Month'] == 12)][['MonthYears','Net debt', 'Scen1cumnetdebt', 'Scen2cumnetdebt', 'Scen3cumnetdebt']]

    # Extract year and month from 'MonthYears' column
    df_filtered['Year'] = df_filtered['MonthYears'].dt.year
    df_filtered['Month'] = df_filtered['MonthYears'].dt.month

    # Pivot the dataframe to have one row per year and columns for each scenario
    df_pivot = df_filtered.pivot_table(index='Year', columns='Month', values=['Net debt','Scen1cumnetdebt', 'Scen2cumnetdebt', 'Scen3cumnetdebt'], aggfunc='sum')

    #-----testing liquidity-----------------------------------------------

    df_filteredz = dfflows[(dfflows['Month'] == 5) | (dfflows['Month'] == 9)][['Liquidity Base scenairo']]


    # Create a new dataframe with only the specified columns and where Month is June or December
    df_filteredz = dfflows[(dfflows['Month'] == 5) | (dfflows['Month'] == 9)][['MonthYears','Liquidity Base scenairo']]

    # Extract year and month from 'MonthYears' column
    df_filteredz['Year'] = df_filteredz['MonthYears'].dt.year
    df_filteredz['Month'] = df_filteredz['MonthYears'].dt.month

    # Pivot the dataframe to have one row per year and columns for each scenario
    df_pivotz = df_filteredz.pivot_table(index='Year', columns='Month', values=['Liquidity Base scenairo'], aggfunc='sum')

    H1_liquid = df_pivotz.loc[:, ('Liquidity Base scenairo', 5)] 
    H2_liquid = df_pivotz.loc[:, ('Liquidity Base scenairo', 9)]

    BASEFYLIQUID = pd.DataFrame()

    BASEFYLIQUID['H1 LIQUID COMPARE'] = df["Years"].map(H1_liquid)
    BASEFYLIQUID['H2 LIQUID COMPARE'] = df["Years"].map(H2_liquid)

    BASEFYLIQUID['liquidity FY Base scenario'] = np.minimum(BASEFYLIQUID['H1 LIQUID COMPARE'], BASEFYLIQUID['H2 LIQUID COMPARE'])
    #--- testing ends-----------------------------------------

    #-----RSS-----------------LIQUIDITY----------------------

    df_filteredrss = temp_df[(temp_df['Month'] == 'May') | (temp_df['Month'] == 'Sep')][['Liquidity']]


    # Create a new dataframe with only the specified columns and where Month is June or December
    df_filteredz = temp_df[(temp_df['Month'] == 'May') | (temp_df['Month'] == 'Sep')][['MonthYears', 'Liquidity']]

    # Extract year and month from 'MonthYears' column
    df_filteredrss['Year'] = temp_df['MonthYears'].dt.year
    df_filteredrss['Month'] = temp_df['MonthYears'].dt.month


    # Pivot the dataframe to have one row per year and columns for each scenario
    df_pivotrss = df_filteredrss.pivot_table(index='Year', columns='Month', values=['Liquidity'], aggfunc='sum')


    H1_liquidrss = df_pivotrss.loc[:, ('Liquidity', 5)] 
    H2_liquidrss = df_pivotrss.loc[:, ('Liquidity', 9)]
    BASEFYLIQUIDrss = pd.DataFrame()

    BASEFYLIQUIDrss['H1 LIQUID COMPARE'] = df["Years"].map(H1_liquidrss)
    BASEFYLIQUIDrss['H2 LIQUID COMPARE'] = df["Years"].map(H2_liquidrss)

    BASEFYLIQUIDrss['liquidity FY RSS scenario'] = np.minimum(BASEFYLIQUIDrss['H1 LIQUID COMPARE'], BASEFYLIQUIDrss['H2 LIQUID COMPARE'])
    #-----RSS-----------------LIQUIDITY----------------------


    #-----SBP-----------------LIQUIDITY----------------------

    df_filteredsbp = tempsbp_df[(tempsbp_df['Month'] == 'May') | (tempsbp_df['Month'] == 'Sep')][['Liquidity']]


    # Create a new dataframe with only the specified columns and where Month is June or December
    df_filteredsbp = tempsbp_df[(temp_df['Month'] == 'May') | (tempsbp_df['Month'] == 'Sep')][['MonthYears', 'Liquidity']]

    # Extract year and month from 'MonthYears' column
    df_filteredsbp['Year'] = tempsbp_df['MonthYears'].dt.year
    df_filteredsbp['Month'] = tempsbp_df['MonthYears'].dt.month


    # Pivot the dataframe to have one row per year and columns for each scenario
    df_pivotsbp = df_filteredsbp.pivot_table(index='Year', columns='Month', values=['Liquidity'], aggfunc='sum')


    H1_liquidsbp = df_pivotsbp.loc[:, ('Liquidity', 5)] 
    H2_liquidsbp = df_pivotsbp.loc[:, ('Liquidity', 9)]
    BASEFYLIQUIDsbp = pd.DataFrame()

    BASEFYLIQUIDsbp['H1 LIQUID COMPARE'] = df["Years"].map(H1_liquidsbp)
    BASEFYLIQUIDsbp['H2 LIQUID COMPARE'] = df["Years"].map(H2_liquidsbp)

    BASEFYLIQUIDsbp['liquidity FY SBP scenario'] = np.minimum(BASEFYLIQUIDsbp['H1 LIQUID COMPARE'], BASEFYLIQUIDsbp['H2 LIQUID COMPARE'])
    #-----SBP-----------------LIQUIDITY----------------------

    # Extract H1 (June) and H2 (December) for each scenario
    H1_net = df_pivot.loc[:, ('Net debt', 6)] 
    H2_net = df_pivot.loc[:, ('Net debt', 12)]

    H1_Scen1 = df_pivot.loc[:, ('Scen1cumnetdebt', 6)] 
    H2_Scen1 = df_pivot.loc[:, ('Scen1cumnetdebt', 12)]

    H1_Scen2 = df_pivot.loc[:, ('Scen2cumnetdebt', 6)] 
    H2_Scen2 = df_pivot.loc[:, ('Scen2cumnetdebt', 12)]

    H1_Scen3 = df_pivot.loc[:, ('Scen3cumnetdebt', 6)] 
    H2_Scen3 = df_pivot.loc[:, ('Scen3cumnetdebt', 12)]

    #----------------------------------------------------------------------------------------
    # End
    #----------------------------------------------------------------------------------------
    
    #----------------------------------------------------------------------------------------
    # EBITDA CALCULATIONS START
    #----------------------------------------------------------------------------------------
    # BASE SCENAIRO
    #----------------------------------------------------------------------------------------
    #create a data frame to store all the data 
    dfCovenant_HY = pd.DataFrame()

    #generate data for Prorated Profit FY, H1 and H2
    dfCovenant_HY['Profit1'] = dfProfit['Profit']
    dfCovenant_HY['Profit2'] = dfProfit['Profit']
    dfCovenant_HY['Prorated Profit FY'] = (dfCovenant_HY['Profit1']*(1-H1_profit_wt))+(dfCovenant_HY['Profit2']*H1_profit_wt)
    dfCovenant_HY['Prorated Profit H1'] = dfCovenant_HY['Profit2']*H1_profit_wt
    dfCovenant_HY['Prorated Profit H2'] = dfCovenant_HY['Profit1']*(1-H1_profit_wt)

    #generate data for Prorated A&D FY, H1 and H2
    dfCovenant_HY['Amort&D1'] = df['A&D']
    dfCovenant_HY['Amort&D2'] = df['A&D']
    dfCovenant_HY['Prorated A&D FY'] = (dfCovenant_HY['Amort&D1']*(1-H1_AD_wt))+(dfCovenant_HY['Amort&D2']*H1_AD_wt)
    dfCovenant_HY['Prorated A&D H1'] = dfCovenant_HY['Amort&D2']*H1_AD_wt
    dfCovenant_HY['Prorated A&D H2'] = dfCovenant_HY['Amort&D1']*(1-H1_AD_wt)

    #Get Ebitda FY, H1 and H2
    dfCovenant_HY["Cov EBITDA FY"] = dfCovenant_HY['Prorated Profit FY'] - dfCovenant_HY['Prorated A&D FY']
    dfCovenant_HY["Cov EBITDA H1"] = dfCovenant_HY['Prorated Profit H1'] - dfCovenant_HY['Prorated A&D H1']
    dfCovenant_HY["Cov EBITDA H2"] = dfCovenant_HY['Prorated Profit H2'] - dfCovenant_HY['Prorated A&D H2']

    #GET NET DEBT FY, H1 and H2 
    dfCovenant_HY['FY net debt'] = df["Net debt"]
    dfCovenant_HY['H1 net debt'] = df["Years"].map(H1_net)
    dfCovenant_HY['H2 net debt'] = df["Years"].map(H2_net)

    # get lease FY, H1 and H2
    dfCovenant_HY['Leases FY'] = df['Leases']
    dfCovenant_HY['Leases H1'] = df['Leases']
    dfCovenant_HY['Leases H2'] = df['Leases']
    #-------CHECK THE H1 and H2 of the lease with james as it might not be correct------
    #dfCovenant_HY['Leases H1'] = df['Leases']*H1_interest_cash_wt
    #dfCovenant_HY['Leases H2'] = df['Leases']*(1-H1_interest_cash_wt)
    #---------------------------------------------------------------------------------

    #GET Net Cash for Covenants FY, H1 and H2
    dfCovenant_HY['Net Cash for Covenants FY'] = dfCovenant_HY['FY net debt'] + (dfCovenant_HY['Leases FY'])
    dfCovenant_HY['Net Cash for Covenants H1'] = dfCovenant_HY['H1 net debt'] + (dfCovenant_HY['Leases H1'])
    dfCovenant_HY['Net Cash for Covenants H2'] = dfCovenant_HY['H2 net debt'] + (dfCovenant_HY['Leases H2'])


    #GET EBITDA DATA
    #main EBITDA H1 and H2
    shifted_ebitda_h2 = dfCovenant_HY["Cov EBITDA H2"].shift(1)
    dfCovenant_HY.loc[1:, "Main EBITDA H1"] = dfCovenant_HY['Cov EBITDA H1'] + shifted_ebitda_h2
    dfCovenant_HY["Main EBITDA H1"].fillna(1049, inplace=True)
    dfCovenant_HY["Main EBITDA H2"] =  dfCovenant_HY['Cov EBITDA H1'] + dfCovenant_HY["Cov EBITDA H2"]


    dfCovenant_HY["EBITDA H1"] = ((((dfCovenant_HY["Main EBITDA H1"])*4) + (dfCovenant_HY['Net Cash for Covenants H1']))/5)


    dfCovenant_HY["EBITDA H2"] = ((((dfCovenant_HY["Main EBITDA H2"])*4) + (dfCovenant_HY['Net Cash for Covenants H2']))/5)

    # Set "EBITDA FY" to the minimum of "EBITDA H1" and "EBITDA H2"
    dfCovenant_HY["EBITDA FY"] = np.maximum(dfCovenant_HY["EBITDA H1"], dfCovenant_HY["EBITDA H2"])
    #----------------------------------------------------------------------------------------
    # BASE SCENAIRO End
    #----------------------------------------------------------------------------------------

    # RSS START
    #----------------------------------------------------------------------------------------
    #create a data frame to store all the data 
    dfRSSCovenant_HY = pd.DataFrame()

    #generate data for Prorated Profit FY, H1 and H2
    dfRSSCovenant_HY['Profit1'] = df[f"{Scenlist[2]} op profit pst"]
    dfRSSCovenant_HY['Profit2'] = df[f"{Scenlist[2]} op profit pst"] 
    dfRSSCovenant_HY['Prorated Profit FY'] = (dfRSSCovenant_HY['Profit1']*(1-H1_profit_wt))+(dfRSSCovenant_HY['Profit2']*H1_profit_wt)
    dfRSSCovenant_HY['Prorated Profit H1'] = dfRSSCovenant_HY['Profit2']*H1_profit_wt
    dfRSSCovenant_HY['Prorated Profit H2'] = dfRSSCovenant_HY['Profit1']*(1-H1_profit_wt)

    #generate data for Prorated A&D FY, H1 and H2
    dfRSSCovenant_HY['Amort&D1'] = df['A&D']
    dfRSSCovenant_HY['Amort&D2'] = df['A&D']
    dfRSSCovenant_HY['Prorated A&D FY'] = (dfRSSCovenant_HY['Amort&D1']*(1-H1_AD_wt))+(dfRSSCovenant_HY['Amort&D2']*H1_AD_wt)
    dfRSSCovenant_HY['Prorated A&D H1'] = dfRSSCovenant_HY['Amort&D2']*H1_AD_wt
    dfRSSCovenant_HY['Prorated A&D H2'] = dfRSSCovenant_HY['Amort&D1']*(1-H1_AD_wt)

    #Get Ebitda FY, H1 and H2
    dfRSSCovenant_HY["Cov EBITDA FY"] = dfRSSCovenant_HY['Prorated Profit FY'] - dfRSSCovenant_HY['Prorated A&D FY']
    dfRSSCovenant_HY["Cov EBITDA H1"] = dfRSSCovenant_HY['Prorated Profit H1'] - dfRSSCovenant_HY['Prorated A&D H1']
    dfRSSCovenant_HY["Cov EBITDA H2"] = dfRSSCovenant_HY['Prorated Profit H2'] - dfRSSCovenant_HY['Prorated A&D H2']

    #GET NET DEBT FY, H1 and H2 
    dfRSSCovenant_HY['FY net debt'] = df[f"{Scenlist[2]} net debt"]
    dfRSSCovenant_HY['H1 net debt'] = df["Years"].map(H1_Scen1)
    dfRSSCovenant_HY['H2 net debt'] = df["Years"].map(H2_Scen1)

    # get lease FY, H1 and H2
    dfRSSCovenant_HY['Leases FY'] = df['Leases']
    dfRSSCovenant_HY['Leases H1'] = df['Leases']
    dfRSSCovenant_HY['Leases H2'] = df['Leases']
    #-------CHECK THE H1 and H2 of the lease with james as it might not be correct------
    #dfCovenant_HY['Leases H1'] = df['Leases']*H1_interest_cash_wt
    #dfCovenant_HY['Leases H2'] = df['Leases']*(1-H1_interest_cash_wt)
    #---------------------------------------------------------------------------------

    #GET Net Cash for Covenants FY, H1 and H2
    dfRSSCovenant_HY['Net Cash for Covenants FY'] = dfRSSCovenant_HY['FY net debt'] + (dfRSSCovenant_HY['Leases FY'])
    dfRSSCovenant_HY['Net Cash for Covenants H1'] = dfRSSCovenant_HY['H1 net debt'] + (dfRSSCovenant_HY['Leases H1'])
    dfRSSCovenant_HY['Net Cash for Covenants H2'] = dfRSSCovenant_HY['H2 net debt'] + (dfRSSCovenant_HY['Leases H2'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    RSSshifted_ebitda_h2 = dfRSSCovenant_HY["Cov EBITDA H2"].shift(1)
    dfRSSCovenant_HY.loc[1:, "Main EBITDA H1"] = dfRSSCovenant_HY['Cov EBITDA H1'] + RSSshifted_ebitda_h2
    dfRSSCovenant_HY["Main EBITDA H1"].fillna(1049, inplace=True)
    dfRSSCovenant_HY["Main EBITDA H2"] =  dfRSSCovenant_HY['Cov EBITDA H1'] + dfRSSCovenant_HY["Cov EBITDA H2"]


    dfRSSCovenant_HY["EBITDA H1"] = ((((dfRSSCovenant_HY["Main EBITDA H1"])*4) + (dfRSSCovenant_HY['Net Cash for Covenants H1']))/5)


    dfRSSCovenant_HY["EBITDA H2"] = ((((dfRSSCovenant_HY["Main EBITDA H2"])*4) + (dfRSSCovenant_HY['Net Cash for Covenants H2']))/5)

    # Set "EBITDA FY" to the minimum of "EBITDA H1" and "EBITDA H2"
    dfRSSCovenant_HY["EBITDA FY"] = np.maximum(dfRSSCovenant_HY["EBITDA H1"], dfRSSCovenant_HY["EBITDA H2"])

    #----------------------------------------------------------------------------------------
    # RSS End
    #----------------------------------------------------------------------------------------

    # SBP START
    #----------------------------------------------------------------------------------------
    dfSBPCovenant_HY = pd.DataFrame()

    #generate data for Prorated Profit FY, H1 and H2
    dfSBPCovenant_HY['Profit1'] = df[f"{Scenlist[1]} op profit pst"]
    dfSBPCovenant_HY['Profit2'] = df[f"{Scenlist[1]} op profit pst"] 
    dfSBPCovenant_HY['Prorated Profit FY'] = (dfSBPCovenant_HY['Profit1']*(1-H1_profit_wt))+(dfSBPCovenant_HY['Profit2']*H1_profit_wt)
    dfSBPCovenant_HY['Prorated Profit H1'] = dfSBPCovenant_HY['Profit2']*H1_profit_wt
    dfSBPCovenant_HY['Prorated Profit H2'] = dfSBPCovenant_HY['Profit1']*(1-H1_profit_wt)

    #generate data for Prorated A&D FY, H1 and H2
    dfSBPCovenant_HY['Amort&D1'] = df['A&D']
    dfSBPCovenant_HY['Amort&D2'] = df['A&D']
    dfSBPCovenant_HY['Prorated A&D FY'] = (dfSBPCovenant_HY['Amort&D1']*(1-H1_AD_wt))+(dfSBPCovenant_HY['Amort&D2']*H1_AD_wt)
    dfSBPCovenant_HY['Prorated A&D H1'] = dfSBPCovenant_HY['Amort&D2']*H1_AD_wt
    dfSBPCovenant_HY['Prorated A&D H2'] = dfSBPCovenant_HY['Amort&D1']*(1-H1_AD_wt)


    #Get Ebitda FY, H1 and H2
    dfSBPCovenant_HY["Cov EBITDA FY"] = dfSBPCovenant_HY['Prorated Profit FY'] - dfSBPCovenant_HY['Prorated A&D FY']
    dfSBPCovenant_HY["Cov EBITDA H1"] = dfSBPCovenant_HY['Prorated Profit H1'] - dfSBPCovenant_HY['Prorated A&D H1']
    dfSBPCovenant_HY["Cov EBITDA H2"] = dfSBPCovenant_HY['Prorated Profit H2'] - dfSBPCovenant_HY['Prorated A&D H2']

    #GET NET DEBT FY, H1 and H2 
    dfSBPCovenant_HY['FY net debt'] = df[f"{Scenlist[1]} net debt"]
    dfSBPCovenant_HY['H1 net debt'] = df["Years"].map(H1_Scen2)
    dfSBPCovenant_HY['H2 net debt'] = df["Years"].map(H2_Scen2)

    # get lease FY, H1 and H2
    dfSBPCovenant_HY['Leases FY'] = df['Leases']
    dfSBPCovenant_HY['Leases H1'] = df['Leases']
    dfSBPCovenant_HY['Leases H2'] = df['Leases']
    #-------CHECK THE H1 and H2 of the lease with james as it might not be correct------
    #dfCovenant_HY['Leases H1'] = df['Leases']*H1_interest_cash_wt
    #dfCovenant_HY['Leases H2'] = df['Leases']*(1-H1_interest_cash_wt)
    #---------------------------------------------------------------------------------

    #GET Net Cash for Covenants FY, H1 and H2
    dfSBPCovenant_HY['Net Cash for Covenants FY'] = dfSBPCovenant_HY['FY net debt'] + (dfSBPCovenant_HY['Leases FY'])
    dfSBPCovenant_HY['Net Cash for Covenants H1'] = dfSBPCovenant_HY['H1 net debt'] + (dfSBPCovenant_HY['Leases H1'])
    dfSBPCovenant_HY['Net Cash for Covenants H2'] = dfSBPCovenant_HY['H2 net debt'] + (dfSBPCovenant_HY['Leases H2'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    SBPshifted_ebitda_h2 = dfSBPCovenant_HY["Cov EBITDA H2"].shift(1)
    dfSBPCovenant_HY.loc[1:, "Main EBITDA H1"] = dfSBPCovenant_HY['Cov EBITDA H1'] + SBPshifted_ebitda_h2
    dfSBPCovenant_HY["Main EBITDA H1"].fillna(1049, inplace=True)
    dfSBPCovenant_HY["Main EBITDA H2"] =  dfSBPCovenant_HY['Cov EBITDA H1'] + dfSBPCovenant_HY["Cov EBITDA H2"]


    dfSBPCovenant_HY["EBITDA H1"] = ((((dfSBPCovenant_HY["Main EBITDA H1"])*4) + (dfSBPCovenant_HY['Net Cash for Covenants H1']))/5)


    dfSBPCovenant_HY["EBITDA H2"] = ((((dfSBPCovenant_HY["Main EBITDA H2"])*4) + (dfSBPCovenant_HY['Net Cash for Covenants H2']))/5)

    # Set "EBITDA FY" to the minimum of "EBITDA H1" and "EBITDA H2"
    dfSBPCovenant_HY["EBITDA FY"] = np.maximum(dfSBPCovenant_HY["EBITDA H1"], dfSBPCovenant_HY["EBITDA H2"])

    #----------------------------------------------------------------------------------------
    # SBP End
    #----------------------------------------------------------------------------------------

    # SBP 5+7 START
    #----------------------------------------------------------------------------------------
    dfSBP57Covenant_HY = pd.DataFrame()

    #generate data for Prorated Profit FY, H1 and H2
    dfSBP57Covenant_HY['Profit1'] = fsdf[f"{Scenlist[1]} op profit pst"]
    dfSBP57Covenant_HY['Profit2'] = fsdf[f"{Scenlist[1]} op profit pst"] 
    dfSBP57Covenant_HY['Prorated Profit FY'] = (dfSBP57Covenant_HY['Profit1']*(1-fsH1_profit_wt))+(dfSBP57Covenant_HY['Profit2']*fsH1_profit_wt)
    dfSBP57Covenant_HY['Prorated Profit H1'] = dfSBP57Covenant_HY['Profit2']*fsH1_profit_wt
    dfSBP57Covenant_HY['Prorated Profit H2'] = dfSBP57Covenant_HY['Profit1']*(1-fsH1_profit_wt)

    #generate data for Prorated A&D FY, H1 and H2
    dfSBP57Covenant_HY['Amort&D1'] = fsdf['A&D']
    dfSBP57Covenant_HY['Amort&D2'] = fsdf['A&D']
    dfSBP57Covenant_HY['Prorated A&D FY'] = (dfSBP57Covenant_HY['Amort&D1']*(1-fsH1_AD_wt))+(dfSBP57Covenant_HY['Amort&D2']*fsH1_AD_wt)
    dfSBP57Covenant_HY['Prorated A&D H1'] = dfSBP57Covenant_HY['Amort&D2']*fsH1_AD_wt
    dfSBP57Covenant_HY['Prorated A&D H2'] = dfSBP57Covenant_HY['Amort&D1']*(1-fsH1_AD_wt)


    #Get Ebitda FY, H1 and H2
    dfSBP57Covenant_HY["Cov EBITDA FY"] = dfSBP57Covenant_HY['Prorated Profit FY'] - dfSBP57Covenant_HY['Prorated A&D FY']
    dfSBP57Covenant_HY["Cov EBITDA H1"] = dfSBP57Covenant_HY['Prorated Profit H1'] - dfSBP57Covenant_HY['Prorated A&D H1']
    dfSBP57Covenant_HY["Cov EBITDA H2"] = dfSBP57Covenant_HY['Prorated Profit H2'] - dfSBP57Covenant_HY['Prorated A&D H2']

    #GET NET DEBT FY, H1 and H2 
    dfSBP57Covenant_HY['FY net debt'] = fsdf[f"{Scenlist[1]} net debt"]
    dfSBP57Covenant_HY['H1 net debt'] = fsdf["Years"].map(H1_Scen3)
    dfSBP57Covenant_HY['H2 net debt'] = fsdf["Years"].map(H2_Scen3)

    # get lease FY, H1 and H2
    dfSBP57Covenant_HY['Leases FY'] = df['Leases']
    dfSBP57Covenant_HY['Leases H1'] = df['Leases']
    dfSBP57Covenant_HY['Leases H2'] = df['Leases']
    #-------CHECK THE H1 and H2 of the lease with james as it might not be correct------
    #dfCovenant_HY['Leases H1'] = df['Leases']*H1_interest_cash_wt
    #dfCovenant_HY['Leases H2'] = df['Leases']*(1-H1_interest_cash_wt)
    #---------------------------------------------------------------------------------

    #GET Net Cash for Covenants FY, H1 and H2
    dfSBP57Covenant_HY['Net Cash for Covenants FY'] = dfSBP57Covenant_HY['FY net debt'] + (dfSBP57Covenant_HY['Leases FY'])
    dfSBP57Covenant_HY['Net Cash for Covenants H1'] = dfSBP57Covenant_HY['H1 net debt'] + (dfSBP57Covenant_HY['Leases H1'])
    dfSBP57Covenant_HY['Net Cash for Covenants H2'] = dfSBP57Covenant_HY['H2 net debt'] + (dfSBP57Covenant_HY['Leases H2'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    SBP57shifted_ebitda_h2 = dfSBP57Covenant_HY["Cov EBITDA H2"].shift(1)
    dfSBP57Covenant_HY.loc[1:, "Main EBITDA H1"] = dfSBP57Covenant_HY['Cov EBITDA H1'] + SBP57shifted_ebitda_h2
    dfSBP57Covenant_HY["Main EBITDA H1"].fillna(1049, inplace=True)
    dfSBP57Covenant_HY["Main EBITDA H2"] =  dfSBP57Covenant_HY['Cov EBITDA H1'] + dfSBP57Covenant_HY["Cov EBITDA H2"]


    dfSBP57Covenant_HY["EBITDA H1"] = ((((dfSBP57Covenant_HY["Main EBITDA H1"])*4) + (dfSBP57Covenant_HY['Net Cash for Covenants H1']))/5)


    dfSBP57Covenant_HY["EBITDA H2"] = ((((dfSBP57Covenant_HY["Main EBITDA H2"])*4) + (dfSBP57Covenant_HY['Net Cash for Covenants H2']))/5)

    # Set "EBITDA FY" to the minimum of "EBITDA H1" and "EBITDA H2"
    dfSBP57Covenant_HY["EBITDA FY"] = np.maximum(dfSBP57Covenant_HY["EBITDA H1"], dfSBP57Covenant_HY["EBITDA H2"])

    #----------------------------------------------------------------------------------------
    # SBP 5+7 End
    #----------------------------------------------------------------------------------------



    #----------------------------------------------------------------------------------------
    # EBITDA END
    #----------------------------------------------------------------------------------------

    
    #----------------------------------------------------------------------------------------
    #  EBITDA Headroom Int Cover CALCULATIONS START
    #----------------------------------------------------------------------------------------
    # BASE SCENAIRO
    #----------------------------------------------------------------------------------------
    #create a data frame to store all the data 
    dfEBITDA_HIC = pd.DataFrame()

    dfEBITDA_HIC['Interest Total FY'] = df['InterestP&L']
    dfEBITDA_HIC['Interest Total H1'] = df['InterestP&L']/2

    # shift the values and add zero to the last one 
    dfEBITDA_HIC['shifted Interest Total H1'] = dfEBITDA_HIC['Interest Total H1'].shift(-1)
    # Replace NaN values with 0
    dfEBITDA_HIC['shifted Interest Total H1'].fillna(0, inplace=True)

    dfEBITDA_HIC['Interest Total H2'] = df['InterestP&L']/2
    dfEBITDA_HIC['LeaseInt Total FY'] = df['LeaseInterest']
    dfEBITDA_HIC['LeaseInt Total H1'] = df['LeaseInterest']/2

    #shift the value and add zero to the last one 
    dfEBITDA_HIC['shifted LeaseInt Total H1'] = dfEBITDA_HIC['LeaseInt Total H1'].shift(-1)
    dfEBITDA_HIC['shifted LeaseInt Total H1'].fillna(0, inplace=True)
    dfEBITDA_HIC['LeaseInt Total H2'] = df['LeaseInterest']/2

    # Divide each value by 12 to get monthly values
    dfEBITDA_HIC['Monthly Interest'] = dfEBITDA_HIC['Interest Total FY'] / 12
    dfEBITDA_HIC['Interest June'] = dfEBITDA_HIC['Monthly Interest']
    dfEBITDA_HIC['Interest December'] = dfEBITDA_HIC['Monthly Interest']



    # Divide each value by 12 to get monthly values
    dfEBITDA_HIC['Monthly LeaseInt'] = dfEBITDA_HIC['LeaseInt Total FY'] / 12
    dfEBITDA_HIC['LeaseInt June'] = dfEBITDA_HIC['Monthly LeaseInt']
    dfEBITDA_HIC['LeaseInt December'] = dfEBITDA_HIC['Monthly LeaseInt']

    # get Covenant Interest calculation
    dfEBITDA_HIC['Covenant Interest H1'] = (((dfEBITDA_HIC['Interest Total H1'])-(dfEBITDA_HIC['LeaseInt Total H1']))+((dfEBITDA_HIC['shifted Interest Total H1'])-(dfEBITDA_HIC['shifted LeaseInt Total H1']))).shift(1)
    dfEBITDA_HIC['Covenant Interest H1'].fillna(1.1, inplace=True)
    dfEBITDA_HIC['Covenant Interest H2'] = (dfEBITDA_HIC['Interest Total FY'])-(dfEBITDA_HIC['LeaseInt Total FY'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    shifted_ebitda_h2 = dfCovenant_HY["Cov EBITDA H2"].shift(1)
    dfEBITDA_HIC.loc[1:, "Main EBITDA H1"] = dfCovenant_HY['Cov EBITDA H1'] + shifted_ebitda_h2
    dfEBITDA_HIC["Main EBITDA H1"].fillna(1049, inplace=True)
    dfEBITDA_HIC["Main EBITDA H2"] =  dfCovenant_HY['Cov EBITDA H1'] + dfCovenant_HY["Cov EBITDA H2"]
    dfEBITDA_HIC["Main EBITDA FY"] = np.maximum(dfEBITDA_HIC["Main EBITDA H1"], dfEBITDA_HIC["Main EBITDA H2"])


    # get Amortisation
    dfEBITDA_HIC['Amortisation H1'] = (dfCovenant_HY['Prorated A&D H1'])*0.6666
    dfEBITDA_HIC['Amortisation H2'] = (dfCovenant_HY['Prorated A&D H2'])*0.6666
    dfEBITDA_HIC['Amortisation FY'] = (dfCovenant_HY['Prorated A&D FY'])*0.6666

    #get EBITDA calculated AD Minus D
    dfEBITDA_HIC['EBITDA A+D-D H1'] = ((dfEBITDA_HIC["Main EBITDA H1"])+(dfEBITDA_HIC['Amortisation H1']))
    dfEBITDA_HIC['EBITDA A+D-D H2'] = ((dfEBITDA_HIC["Main EBITDA H2"])+(dfEBITDA_HIC['Amortisation H2']))
    dfEBITDA_HIC['EBITDA A+D-D FY'] = np.maximum(dfEBITDA_HIC['EBITDA A+D-D H1'], dfEBITDA_HIC['EBITDA A+D-D H2'])

    #get calculation for EBITDA Headroom for Int Cover 
    dfEBITDA_HIC['EBITDA INT COVER H1'] = -((-3*dfEBITDA_HIC['Covenant Interest H1'])-dfEBITDA_HIC['EBITDA A+D-D H1'])
    dfEBITDA_HIC['EBITDA INT COVER H2'] = -((-3*dfEBITDA_HIC['Covenant Interest H2'])-dfEBITDA_HIC['EBITDA A+D-D H2'])
    dfEBITDA_HIC['EBITDA INT COVER FY'] = np.minimum(dfEBITDA_HIC['EBITDA INT COVER H1'], dfEBITDA_HIC['EBITDA INT COVER H2'])
    #----------------------------------------------------------------------------------------
    # BASE SCENAIRO End
    #----------------------------------------------------------------------------------------

    # RSS SCENAIRO
    #----------------------------------------------------------------------------------------
    #create a data frame to store all the data 
    dfRSSEBITDA_HIC = pd.DataFrame()

    dfRSSEBITDA_HIC['Interest Total FY'] = df['InterestP&L']
    dfRSSEBITDA_HIC['Interest Total H1'] = df['InterestP&L']/2

    # shift the values and add zero to the last one 
    dfRSSEBITDA_HIC['shifted Interest Total H1'] = dfRSSEBITDA_HIC['Interest Total H1'].shift(-1)
    # Replace NaN values with 0
    dfRSSEBITDA_HIC['shifted Interest Total H1'].fillna(0, inplace=True)

    dfRSSEBITDA_HIC['Interest Total H2'] = df['InterestP&L']/2
    dfRSSEBITDA_HIC['LeaseInt Total FY'] = df['LeaseInterest']
    dfRSSEBITDA_HIC['LeaseInt Total H1'] = df['LeaseInterest']/2

    #shift the value and add zero to the last one 
    dfRSSEBITDA_HIC['shifted LeaseInt Total H1'] = dfRSSEBITDA_HIC['LeaseInt Total H1'].shift(-1)
    dfRSSEBITDA_HIC['shifted LeaseInt Total H1'].fillna(0, inplace=True)
    dfRSSEBITDA_HIC['LeaseInt Total H2'] = df['LeaseInterest']/2

    # Divide each value by 12 to get monthly values
    dfRSSEBITDA_HIC['Monthly Interest'] = dfRSSEBITDA_HIC['Interest Total FY'] / 12
    dfRSSEBITDA_HIC['Interest June'] = dfRSSEBITDA_HIC['Monthly Interest']
    dfRSSEBITDA_HIC['Interest December'] = dfRSSEBITDA_HIC['Monthly Interest']



    # Divide each value by 12 to get monthly values
    dfRSSEBITDA_HIC['Monthly LeaseInt'] = dfRSSEBITDA_HIC['LeaseInt Total FY'] / 12
    dfRSSEBITDA_HIC['LeaseInt June'] = dfRSSEBITDA_HIC['Monthly LeaseInt']
    dfRSSEBITDA_HIC['LeaseInt December'] = dfRSSEBITDA_HIC['Monthly LeaseInt']

    # get Covenant Interest calculation
    dfRSSEBITDA_HIC['Covenant Interest H1'] = (((dfRSSEBITDA_HIC['Interest Total H1'])-(dfRSSEBITDA_HIC['LeaseInt Total H1']))+((dfRSSEBITDA_HIC['shifted Interest Total H1'])-(dfRSSEBITDA_HIC['shifted LeaseInt Total H1']))).shift(1)
    dfRSSEBITDA_HIC['Covenant Interest H1'].fillna(1.1, inplace=True)
    dfRSSEBITDA_HIC['Covenant Interest H2'] = (dfRSSEBITDA_HIC['Interest Total FY'])-(dfRSSEBITDA_HIC['LeaseInt Total FY'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    RSSshifted_ebitda_h2 = dfRSSCovenant_HY["Cov EBITDA H2"].shift(1)
    dfRSSEBITDA_HIC.loc[1:, "Main EBITDA H1"] = dfRSSCovenant_HY['Cov EBITDA H1'] + RSSshifted_ebitda_h2
    dfRSSEBITDA_HIC["Main EBITDA H1"].fillna(1049, inplace=True)
    dfRSSEBITDA_HIC["Main EBITDA H2"] =  dfRSSCovenant_HY['Cov EBITDA H1'] + dfRSSCovenant_HY["Cov EBITDA H2"]


    dfRSSEBITDA_HIC["EBITDA H1"] = ((((dfRSSCovenant_HY["Main EBITDA H1"])*4) + (dfRSSCovenant_HY['Net Cash for Covenants H1']))/5)


    dfRSSEBITDA_HIC["EBITDA H2"] = ((((dfRSSCovenant_HY["Main EBITDA H2"])*4) + (dfRSSCovenant_HY['Net Cash for Covenants H2']))/5)

    # Set "EBITDA FY" to the minimum of "EBITDA H1" and "EBITDA H2"
    dfRSSEBITDA_HIC["EBITDA FY"] = np.maximum(dfRSSCovenant_HY["EBITDA H1"], dfRSSCovenant_HY["EBITDA H2"])


    # get Amortisation
    dfRSSEBITDA_HIC['Amortisation H1'] = (dfRSSCovenant_HY['Prorated A&D H1'])*0.6666
    dfRSSEBITDA_HIC['Amortisation H2'] = (dfRSSCovenant_HY['Prorated A&D H2'])*0.6666
    dfRSSEBITDA_HIC['Amortisation FY'] = (dfRSSCovenant_HY['Prorated A&D FY'])*0.6666

    #get EBITDA calculated AD Minus D
    dfRSSEBITDA_HIC['EBITDA A+D-D H1'] = ((dfRSSEBITDA_HIC["Main EBITDA H1"])+(dfRSSEBITDA_HIC['Amortisation H1']))
    dfRSSEBITDA_HIC['EBITDA A+D-D H2'] = ((dfRSSEBITDA_HIC["Main EBITDA H2"])+(dfRSSEBITDA_HIC['Amortisation H2']))
    dfRSSEBITDA_HIC['EBITDA A+D-D FY'] = np.maximum(dfEBITDA_HIC['EBITDA A+D-D H1'], dfRSSEBITDA_HIC['EBITDA A+D-D H2'])

    #get calculation for EBITDA Headroom for Int Cover 
    dfRSSEBITDA_HIC['EBITDA INT COVER H1'] = -((-3*dfRSSEBITDA_HIC['Covenant Interest H1'])-dfRSSEBITDA_HIC['EBITDA A+D-D H1'])
    dfRSSEBITDA_HIC['EBITDA INT COVER H2'] = -((-3*dfRSSEBITDA_HIC['Covenant Interest H2'])-dfRSSEBITDA_HIC['EBITDA A+D-D H2'])
    dfRSSEBITDA_HIC['EBITDA INT COVER FY'] = np.minimum(dfRSSEBITDA_HIC['EBITDA INT COVER H1'], dfRSSEBITDA_HIC['EBITDA INT COVER H2'])

    #----------------------------------------------------------------------------------------
    #  RSS END
    #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # SBP SCENAIRO
    #----------------------------------------------------------------------------------------
    #create a data frame to store all the data 
    dfSBPEBITDA_HIC = pd.DataFrame()

    dfSBPEBITDA_HIC['Interest Total FY'] = df['InterestP&L']
    dfSBPEBITDA_HIC['Interest Total H1'] = df['InterestP&L']/2

    # shift the values and add zero to the last one 
    dfSBPEBITDA_HIC['shifted Interest Total H1'] = dfSBPEBITDA_HIC['Interest Total H1'].shift(-1)
    # Replace NaN values with 0
    dfSBPEBITDA_HIC['shifted Interest Total H1'].fillna(0, inplace=True)

    dfSBPEBITDA_HIC['Interest Total H2'] = df['InterestP&L']/2
    dfSBPEBITDA_HIC['LeaseInt Total FY'] = df['LeaseInterest']
    dfSBPEBITDA_HIC['LeaseInt Total H1'] = df['LeaseInterest']/2

    #shift the value and add zero to the last one 
    dfSBPEBITDA_HIC['shifted LeaseInt Total H1'] = dfSBPEBITDA_HIC['LeaseInt Total H1'].shift(-1)
    dfSBPEBITDA_HIC['shifted LeaseInt Total H1'].fillna(0, inplace=True)
    dfSBPEBITDA_HIC['LeaseInt Total H2'] = df['LeaseInterest']/2

    # Divide each value by 12 to get monthly values
    dfSBPEBITDA_HIC['Monthly Interest'] = dfSBPEBITDA_HIC['Interest Total FY'] / 12
    dfSBPEBITDA_HIC['Interest June'] = dfSBPEBITDA_HIC['Monthly Interest']
    dfSBPEBITDA_HIC['Interest December'] = dfSBPEBITDA_HIC['Monthly Interest']



    # Divide each value by 12 to get monthly values
    dfSBPEBITDA_HIC['Monthly LeaseInt'] = dfSBPEBITDA_HIC['LeaseInt Total FY'] / 12
    dfSBPEBITDA_HIC['LeaseInt June'] = dfSBPEBITDA_HIC['Monthly LeaseInt']
    dfSBPEBITDA_HIC['LeaseInt December'] = dfSBPEBITDA_HIC['Monthly LeaseInt']

    # get Covenant Interest calculation
    dfSBPEBITDA_HIC['Covenant Interest H1'] = (((dfSBPEBITDA_HIC['Interest Total H1'])-(dfSBPEBITDA_HIC['LeaseInt Total H1']))+((dfSBPEBITDA_HIC['shifted Interest Total H1'])-(dfSBPEBITDA_HIC['shifted LeaseInt Total H1']))).shift(1)
    dfSBPEBITDA_HIC['Covenant Interest H1'].fillna(1.1, inplace=True)
    dfSBPEBITDA_HIC['Covenant Interest H2'] = (dfSBPEBITDA_HIC['Interest Total FY'])-(dfSBPEBITDA_HIC['LeaseInt Total FY'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    SBPshifted_ebitda_h2 = dfSBPCovenant_HY["Cov EBITDA H2"].shift(1)
    dfSBPEBITDA_HIC.loc[1:, "Main EBITDA H1"] = dfSBPCovenant_HY['Cov EBITDA H1'] + SBPshifted_ebitda_h2
    dfSBPEBITDA_HIC["Main EBITDA H1"].fillna(1049, inplace=True)
    dfSBPEBITDA_HIC["Main EBITDA H2"] =  dfSBPCovenant_HY['Cov EBITDA H1'] + dfSBPCovenant_HY["Cov EBITDA H2"]
    dfSBPEBITDA_HIC["Main EBITDA FY"] = np.maximum(dfSBPEBITDA_HIC["Main EBITDA H1"], dfSBPEBITDA_HIC["Main EBITDA H2"])


    # get Amortisation
    dfSBPEBITDA_HIC['Amortisation H1'] = (dfSBPCovenant_HY['Prorated A&D H1'])*0.6666
    dfSBPEBITDA_HIC['Amortisation H2'] = (dfSBPCovenant_HY['Prorated A&D H2'])*0.6666
    dfSBPEBITDA_HIC['Amortisation FY'] = (dfSBPCovenant_HY['Prorated A&D FY'])*0.6666

    #get EBITDA calculated AD Minus D
    dfSBPEBITDA_HIC['EBITDA A+D-D H1'] = ((dfSBPEBITDA_HIC["Main EBITDA H1"])+(dfSBPEBITDA_HIC['Amortisation H1']))
    dfSBPEBITDA_HIC['EBITDA A+D-D H2'] = ((dfSBPEBITDA_HIC["Main EBITDA H2"])+(dfSBPEBITDA_HIC['Amortisation H2']))
    dfSBPEBITDA_HIC['EBITDA A+D-D FY'] = np.maximum(dfSBPEBITDA_HIC['EBITDA A+D-D H1'], dfSBPEBITDA_HIC['EBITDA A+D-D H2'])

    #get calculation for EBITDA Headroom for Int Cover 
    dfSBPEBITDA_HIC['EBITDA INT COVER H1'] = -((-3*dfSBPEBITDA_HIC['Covenant Interest H1'])-dfSBPEBITDA_HIC['EBITDA A+D-D H1'])
    dfSBPEBITDA_HIC['EBITDA INT COVER H2'] = -((-3*dfSBPEBITDA_HIC['Covenant Interest H2'])-dfSBPEBITDA_HIC['EBITDA A+D-D H2'])
    dfSBPEBITDA_HIC['EBITDA INT COVER FY'] = np.minimum(dfSBPEBITDA_HIC['EBITDA INT COVER H1'], dfSBPEBITDA_HIC['EBITDA INT COVER H2'])
    #----------------------------------------------------------------------------------------
    #  SBP END
    #----------------------------------------------------------------------------------------


    #----------------------------------------------------------------------------------------
    # SBP57 SCENAIRO START
    #----------------------------------------------------------------------------------------
    #create a data frame to store all the data 
    dfSBP57EBITDA_HIC = pd.DataFrame()

    dfSBP57EBITDA_HIC['Interest Total FY'] = fsdf['InterestP&L']
    dfSBP57EBITDA_HIC['Interest Total H1'] = fsdf['InterestP&L']/2

    # shift the values and add zero to the last one 
    dfSBP57EBITDA_HIC['shifted Interest Total H1'] = dfSBP57EBITDA_HIC['Interest Total H1'].shift(-1)
    # Replace NaN values with 0
    dfSBP57EBITDA_HIC['shifted Interest Total H1'].fillna(0, inplace=True)

    dfSBP57EBITDA_HIC['Interest Total H2'] = fsdf['InterestP&L']/2
    dfSBP57EBITDA_HIC['LeaseInt Total FY'] = fsdf['LeaseInterest']
    dfSBP57EBITDA_HIC['LeaseInt Total H1'] = fsdf['LeaseInterest']/2

    #shift the value and add zero to the last one 
    dfSBP57EBITDA_HIC['shifted LeaseInt Total H1'] = dfSBP57EBITDA_HIC['LeaseInt Total H1'].shift(-1)
    dfSBP57EBITDA_HIC['shifted LeaseInt Total H1'].fillna(0, inplace=True)
    dfSBP57EBITDA_HIC['LeaseInt Total H2'] = fsdf['LeaseInterest']/2

    # Divide each value by 12 to get monthly values
    dfSBP57EBITDA_HIC['Monthly Interest'] = dfSBP57EBITDA_HIC['Interest Total FY'] / 12
    dfSBP57EBITDA_HIC['Interest June'] = dfSBP57EBITDA_HIC['Monthly Interest']
    dfSBP57EBITDA_HIC['Interest December'] = dfSBP57EBITDA_HIC['Monthly Interest']



    # Divide each value by 12 to get monthly values
    dfSBP57EBITDA_HIC['Monthly LeaseInt'] = dfSBP57EBITDA_HIC['LeaseInt Total FY'] / 12
    dfSBP57EBITDA_HIC['LeaseInt June'] = dfSBP57EBITDA_HIC['Monthly LeaseInt']
    dfSBP57EBITDA_HIC['LeaseInt December'] = dfSBP57EBITDA_HIC['Monthly LeaseInt']

    # get Covenant Interest calculation
    dfSBP57EBITDA_HIC['Covenant Interest H1'] = (((dfSBP57EBITDA_HIC['Interest Total H1'])-(dfSBP57EBITDA_HIC['LeaseInt Total H1']))+((dfSBP57EBITDA_HIC['shifted Interest Total H1'])-(dfSBP57EBITDA_HIC['shifted LeaseInt Total H1']))).shift(1)
    dfSBP57EBITDA_HIC['Covenant Interest H1'].fillna(1.1, inplace=True)
    dfSBP57EBITDA_HIC['Covenant Interest H2'] = (dfSBP57EBITDA_HIC['Interest Total FY'])-(dfSBP57EBITDA_HIC['LeaseInt Total FY'])

    #GET EBITDA DATA
    #main EBITDA H1 and H2
    SBP57shifted_ebitda_h2 = dfSBP57Covenant_HY["Cov EBITDA H2"].shift(1)
    dfSBP57EBITDA_HIC.loc[1:, "Main EBITDA H1"] = dfSBP57Covenant_HY['Cov EBITDA H1'] + SBP57shifted_ebitda_h2
    dfSBP57EBITDA_HIC["Main EBITDA H1"].fillna(1049, inplace=True)
    dfSBP57EBITDA_HIC["Main EBITDA H2"] =  dfSBP57Covenant_HY['Cov EBITDA H1'] + dfSBP57Covenant_HY["Cov EBITDA H2"]
    dfSBP57EBITDA_HIC["Main EBITDA FY"] = np.maximum(dfSBPEBITDA_HIC["Main EBITDA H1"], dfSBP57EBITDA_HIC["Main EBITDA H2"])


    # get Amortisation
    dfSBP57EBITDA_HIC['Amortisation H1'] = (dfSBP57Covenant_HY['Prorated A&D H1'])*0.6666
    dfSBP57EBITDA_HIC['Amortisation H2'] = (dfSBP57Covenant_HY['Prorated A&D H2'])*0.6666
    dfSBP57EBITDA_HIC['Amortisation FY'] = (dfSBP57Covenant_HY['Prorated A&D FY'])*0.6666

    #get EBITDA calculated AD Minus D
    dfSBP57EBITDA_HIC['EBITDA A+D-D H1'] = ((dfSBP57EBITDA_HIC["Main EBITDA H1"])+(dfSBP57EBITDA_HIC['Amortisation H1']))
    dfSBP57EBITDA_HIC['EBITDA A+D-D H2'] = ((dfSBP57EBITDA_HIC["Main EBITDA H2"])+(dfSBP57EBITDA_HIC['Amortisation H2']))
    dfSBP57EBITDA_HIC['EBITDA A+D-D FY'] = np.maximum(dfSBPEBITDA_HIC['EBITDA A+D-D H1'], dfSBP57EBITDA_HIC['EBITDA A+D-D H2'])

    #get calculation for EBITDA Headroom for Int Cover 
    dfSBP57EBITDA_HIC['EBITDA INT COVER H1'] = -((-3*dfSBP57EBITDA_HIC['Covenant Interest H1'])-dfSBP57EBITDA_HIC['EBITDA A+D-D H1'])
    dfSBP57EBITDA_HIC['EBITDA INT COVER H2'] = -((-3*dfSBP57EBITDA_HIC['Covenant Interest H2'])-dfSBP57EBITDA_HIC['EBITDA A+D-D H2'])
    dfSBP57EBITDA_HIC['EBITDA INT COVER FY'] = np.minimum(dfSBP57EBITDA_HIC['EBITDA INT COVER H1'], dfSBP57EBITDA_HIC['EBITDA INT COVER H2'])

    #----------------------------------------------------------------------------------------
    #  SBP57 END
    #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    #  EBITDA Headroom Int Cover CALCULATIONS END
    #----------------------------------------------------------------------------------------
    
    
    #Create a dataframe to show the base model for all years
    
     
    
    dfp4=pd.DataFrame()
    Op_cashflow_columns=[col for col in dfp.columns if "Op_cash" in col]
    Free_cashflow_columns=[col for col in dfp.columns if "Free Cashflow" in col]
    Other_non_op_columns=[col for col in dfp.columns if "Shares,M&A,Other " in col]
    Net_Cashflow_columns=[col for col in dfp.columns if "Net Cashflow " in col]
    
     
    
    Month=[col for col in dfp.columns if "Month" in col]
    dfp4=dfp.loc[:, Op_cashflow_columns+Free_cashflow_columns+Other_non_op_columns+Net_Cashflow_columns+Month]
    #---- use for testing----print(dfp4.columns)
    dfp4Transp = dfp4.set_index('Month').transpose()
    dfp4Transp = dfp4Transp.round(decimals = 1)
    
     
    
    #Print cashflow scenario tables-------------
    
     
    
    Totyrs = len(df)
    i=0
    while i<Totyrs:
      yrs=str(dfProfit.loc[i,"Years"])
      html_table=(dfp4Transp.loc[[f"Op_cash {yrs}",f"Free Cashflow {yrs}",f"Shares,M&A,Other {yrs}",f"Net Cashflow {yrs}",f"YTD Net Cashflow {yrs}"],:]).to_html()
    
      i=i+1
    
     
    
    # Print dataframe for downside scenarios
    dftots["Month"]=dfflows["Month"]
    dftots = dftots.set_index('Month').transpose()
    dftots = dftots.round(decimals = 1)
    
     
    
    #Create code to present downside sceanrio tables
    l=0
    while l<=(Number-1):
      i=0
      while i<Totyrs:
        yrs=str(dfProfit.loc[i,"Years"])
        nameg=Scenlist[l]
        html_table=(dftots.loc[[f"{nameg} oper cash {yrs}",f"{nameg} free cash flow {yrs}",f"{nameg} Shares,M&A,Other {yrs}",f"{nameg} net debt change {yrs}",f"{nameg} ytd net debt change {yrs}"],:]).to_html()
    
        i=i+1
      l=l+1
    
    
    
    #----------------------------------------------------------------------------------------
    # Defining scenairos(RSS, SBP, BASE AND 5+7) by Items Sales, profit, cashflow and net debt
    #----------------------------------------------------------------------------------------
    
    #Defining Libraries for BASE
    def calculate_base_scenario(item):
        dfHY_nos = pd.DataFrame()
        dfHY_nos["Years"] = df["Years"]


        
        if item == "Sales":
            dfHY_nos["H1"] = (dfProfit["Sales"] * H1_Sales_wt).round(decimals=1)
            dfHY_nos["H2"] = (dfProfit["Sales"] * (1 - H1_Sales_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Sales"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Profits":
            dfHY_nos["H1"] = (dfProfit["Profit"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (dfProfit["Profit"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Profits"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Cash Flow":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (df["Op cash pre res"] * H1_op_cash_wt).round(decimals=1)
            dfHY_nos["H2"] = (df["Op cash pre res"] * (1 - H1_op_cash_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Cash Flow"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Net Debt":
            # Assign H1 and H2 values for Net Debt
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_net).round(decimals=1)
            dfHY_nos["H2"] =  dfHY_nos["Years"].map(H2_net).round(decimals=1)
            dfHY_nos["FY"] = (df["Net debt"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Minimum Liquidity":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_liquid).round(decimals=1)
            dfHY_nos["H2"] = dfHY_nos["Years"].map(H2_liquid).round(decimals=1)
            dfHY_nos["FY"] = (BASEFYLIQUID['liquidity FY Base scenario']).round(decimals=1)
            dfHY_nos["Item"] = "Minimum Liquidity"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfCovenant_HY["EBITDA H1"].round(decimals=1)
            dfHY_nos["H2"] = dfCovenant_HY["EBITDA H2"].round(decimals=1)
            dfHY_nos["FY"] = dfCovenant_HY["EBITDA FY"].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom for Int Cover":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfEBITDA_HIC['EBITDA INT COVER H1'].round(decimals=1)
            dfHY_nos["H2"] = dfEBITDA_HIC['EBITDA INT COVER H2'].round(decimals=1)
            dfHY_nos["FY"] = dfEBITDA_HIC['EBITDA INT COVER FY'].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom for Int Cover"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))
    
    
    #Defining Libraries for RSS

    def calculate_RSS(item):
        dfHY_nos = pd.DataFrame()
        dfHY_nos["Years"] = df["Years"]
        
        if item == "Sales":
            dfHY_nos["H1"] = (df[f"{Scenlist[0]} op sales pst"] * H1_Sales_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[0]} op sales pst"] * (1 - H1_Sales_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Sales"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Profits":
            dfHY_nos["H1"] = (df[f"{Scenlist[0]} op profit pst"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[0]} op profit pst"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Profits"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Cash Flow":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (df[f"{Scenlist[0]} op cash pst"] * H1_op_cash_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[0]} op cash pst"] * (1 - H1_op_cash_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Cash Flow"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Net Debt":
            # Assign H1 and H2 values for Net Debt
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_Scen1).round(decimals=1)
            dfHY_nos["H2"] =  dfHY_nos["Years"].map(H2_Scen1).round(decimals=1)
            dfHY_nos["FY"] = (df[f"{Scenlist[2]} net debt"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Minimum Liquidity":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_liquidrss).round(decimals=1)
            dfHY_nos["H2"] = dfHY_nos["Years"].map(H2_liquidrss).round(decimals=1)
            dfHY_nos["FY"] = (BASEFYLIQUIDrss['liquidity FY RSS scenario']).round(decimals=1)
            dfHY_nos["Item"] = "Minimum Liquidity"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfRSSCovenant_HY["EBITDA H1"].round(decimals=1)
            dfHY_nos["H2"] = dfRSSCovenant_HY["EBITDA H2"].round(decimals=1)
            dfHY_nos["FY"] = dfRSSCovenant_HY["EBITDA FY"].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom for Int Cover":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfRSSEBITDA_HIC['EBITDA INT COVER H1'].round(decimals=1)
            dfHY_nos["H2"] = dfRSSEBITDA_HIC['EBITDA INT COVER H2'].round(decimals=1)
            dfHY_nos["FY"] = dfRSSEBITDA_HIC['EBITDA INT COVER FY'].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom for Int Cover"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))
    
            
    # Defining Libraries for SBP
    
    def calculate_SBP(item):
        dfHY_nos = pd.DataFrame()
        dfHY_nos["Years"] = df["Years"]
        
        if item == "Sales":
            dfHY_nos["H1"] = (df[f"{Scenlist[1]} op sales pst"] * H1_Sales_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[1]} op sales pst"] * (1 - H1_Sales_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Sales"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Profits":
            dfHY_nos["H1"] = (df[f"{Scenlist[1]} op profit pst"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[1]} op profit pst"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Profits"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Cash Flow":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (df[f"{Scenlist[1]} op cash pst"] * H1_op_cash_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[1]} op cash pst"] * (1 - H1_op_cash_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Cash Flow"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Net Debt":
            # Assign H1 and H2 values for Net Debt
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_Scen2).round(decimals=1)
            dfHY_nos["H2"] =  dfHY_nos["Years"].map(H2_Scen2).round(decimals=1)
            dfHY_nos["FY"] = (df[f"{Scenlist[1]} net debt"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Minimum Liquidity":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_liquidsbp).round(decimals=1)
            dfHY_nos["H2"] = dfHY_nos["Years"].map(H2_liquidsbp).round(decimals=1)
            dfHY_nos["FY"] = (BASEFYLIQUIDsbp['liquidity FY SBP scenario']).round(decimals=1)
            dfHY_nos["Item"] = "Minimum Liquidity"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfSBPCovenant_HY["EBITDA H1"].round(decimals=1)
            dfHY_nos["H2"] = dfSBPCovenant_HY["EBITDA H2"].round(decimals=1)
            dfHY_nos["FY"] = dfSBPCovenant_HY["EBITDA FY"].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom for Int Cover":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfSBPEBITDA_HIC['EBITDA INT COVER H1'].round(decimals=1)
            dfHY_nos["H2"] = dfSBPEBITDA_HIC['EBITDA INT COVER H2'].round(decimals=1)
            dfHY_nos["FY"] = dfSBPEBITDA_HIC['EBITDA INT COVER FY'].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom for Int Cover"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))
    
            
    # Defining Libraries for 5+7        
    
    def calculate_57(item):
        dfHY_nos = pd.DataFrame()
        dfHY_nos["Years"] = df["Years"]
        
        if item == "Sales":
            dfHY_nos["H1"] = (df[f"{Scenlist[2]} op sales pst"] * H1_Sales_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[2]} op sales pst"] * (1 - H1_Sales_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Sales"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Profits":
            dfHY_nos["H1"] = (df[f"{Scenlist[2]} op profit pst"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[2]} op profit pst"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Profits"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Cash Flow":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (df[f"{Scenlist[2]} op cash pst"] * H1_op_cash_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[2]} op cash pst"] * (1 - H1_op_cash_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Cash Flow"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Net Debt":
            # Assign H1 and H2 values for Net Debt
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_Scen3).round(decimals=1)
            dfHY_nos["H2"] =  dfHY_nos["Years"].map(H2_Scen3).round(decimals=1)
            dfHY_nos["FY"] = (df[f"{Scenlist[2]} net debt"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Minimum Liquidity":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfHY_nos["Years"].map(H1_liquidsbp).round(decimals=1)
            dfHY_nos["H2"] = dfHY_nos["Years"].map(H2_liquidsbp).round(decimals=1)
            dfHY_nos["FY"] = (BASEFYLIQUIDsbp['liquidity FY SBP scenario']).round(decimals=1)
            dfHY_nos["Item"] = "Minimum Liquidity"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfSBPCovenant_HY["EBITDA H1"].round(decimals=1)
            dfHY_nos["H2"] = dfSBPCovenant_HY["EBITDA H2"].round(decimals=1)
            dfHY_nos["FY"] = dfSBPCovenant_HY["EBITDA FY"].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "EBITDA Headroom for Int Cover":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = dfSBPEBITDA_HIC['EBITDA INT COVER H1'].round(decimals=1)
            dfHY_nos["H2"] = dfSBPEBITDA_HIC['EBITDA INT COVER H2'].round(decimals=1)
            dfHY_nos["FY"] = dfSBPEBITDA_HIC['EBITDA INT COVER FY'].round(decimals=1)
            dfHY_nos["Item"] = "EBITDA Headroom for Int Cover"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))    
    
    #----------------------------------------------------------------------------------------
    # End
    #----------------------------------------------------------------------------------------
        

    
    
    # Data and labels
    labels = ["Sales", "Operating Profits", "Operating Cash Flow", "Net Debt", "Minimum Liquidity", "EBITDA Headroom", "EBITDA Headroom for Int Cover"]
    scenarios = ["Base Scenario", "Reverse Stress scenario (Going Concern) AOP", 
                 "Severe but plausible AOP", "Reverse Stress Test (Viability)"]
   
    # Start with an empty dataframe
    df_final = pd.DataFrame()
    
    # Iterate over each dataframe
    for df, label in zip(df_final, labels):
        # Unpivot the dataframe
        df_melt = df.melt(id_vars='Years', var_name='HY', value_name='Values')
        df_melt['HY'] = df_melt['HY'].str.split('_').str[1]  # Remove suffix from 'HY' column
        df_melt.sort_values(['Years', 'HY'], inplace=True)
        
    # Data and labels
    labels = ["Sales", "Operating Profits", "Operating Cash Flow", "Net Debt", "Minimum Liquidity", "EBITDA Headroom", "EBITDA Headroom for Int Cover"]
    # Create an ordered categorical type with your specific order
    labels_category = pd.CategoricalDtype(categories=labels, ordered=True)
    scenarios_category = pd.CategoricalDtype(categories=scenarios, ordered=True)
    
    scenarios = ["Base Scenario", "Reverse Stress scenario (Going Concern) AOP", 
                 "Severe but plausible AOP", "Reverse Stress Test (Viability)"]
    
    # Start with an empty dataframe
    df_final = pd.DataFrame()
    
    # Iterate over each scenario and item
    for scenario in scenarios:
        for item in labels:
            # Get the calculated values for the current scenario and item
            if scenario == "Base Scenario":
                df_item = calculate_base_scenario(item)
            elif scenario == "Reverse Stress scenario (Going Concern) AOP":
                df_item = calculate_RSS(item)
            elif scenario == "Severe but plausible AOP":
                df_item = calculate_SBP(item)
            elif scenario == "Reverse Stress Test (Viability)":
                df_item = calculate_57(item)
            else:
                # Define custom calculations for other scenarios here
                # ...
                continue
            
            # Insert scenario and item columns
            df_item.insert(1, 'Scenario', scenario)
    
            # Here, we melt the dataframe
            df_item = df_item.melt(id_vars=["Item", "Scenario", "Years"], var_name="Metrics", value_name="Values")
            
            df_final = pd.concat([df_final, df_item])
    
    # Change 'Item' column to your ordered categorical type
    df_final['Item'] = df_final['Item'].astype(labels_category)
    df_final['Scenario'] = df_final['Scenario'].astype(scenarios_category)

    
    # Now, perform a pivot
    df_pivot = df_final.pivot_table(index=['Item', 'Scenario'], columns=['Years', 'Metrics'], values='Values', aggfunc=np.sum)
    
    # Reset the index
    df_pivot.reset_index(inplace=True)
    
    # Sort the DataFrame by 'Item'
    df_pivot.sort_values('Item', inplace=True)
    
    # Add empty string as a category
    df_pivot['Item'] = df_pivot['Item'].cat.add_categories('')
    
    # Now replace the duplicates
    df_pivot['Item'] = df_pivot['Item'].mask(df_pivot['Item'].duplicated(), '')

    selected_scenario_function = calculate_base_scenario

    # Scenario mapping to functions
    scenario_functions = {
        'calculate_base_scenario': calculate_base_scenario,
        'calculate_RSS': calculate_RSS,
        'calculate_SBP': calculate_SBP,
        'calculate_57': calculate_57
    }

    # Change function based on user selection
    if request.method == 'POST':
        selected_scenario = request.form.get('scenario')
        selected_scenario_function = scenario_functions.get(selected_scenario, calculate_base_scenario)

    # Your existing code for data manipulation and summaries
    df_final = pd.DataFrame()
    labels = ["Sales", "Operating Profits", "Operating Cash Flow", "Net Debt", "Minimum Liquidity", "EBITDA Headroom", "EBITDA Headroom for Int Cover"]

    for item in labels:
        df_item = selected_scenario_function(item)
        df_final = pd.concat([df_final, df_item])

    # Convert 'Item' column to categorical type with specified order
    df_final['Item'] = pd.Categorical(df_final['Item'], categories=labels, ordered=True)

    # Pivot and process data as needed here
    # ...

    # Summaries
    summaries = {label: generate_summary(df_final, label) for label in labels}

    # Prepare data for rendering (e.g., for charts)
    # ...
    chart_data = {
    "categories": dfflows["MonthYears"].tolist(),
    "series": [
        {"name": "Net debt", "data": dfflows["Net debt"].tolist()},
        {"name": f"{Scenlist[0]} Net debt", "data": dfflows['Scen1netdebt'].tolist()},
        {"name": f"{Scenlist[1]} Net debt", "data": dfflows['Scen2netdebt'].tolist()},
        {"name": f"{Scenlist[2]} Net debt", "data": dfflows['Scen3netdebt'].tolist()}
    ]
}
    return render_template('netdebt.html', summaries=summaries, chart_data=chart_data, df_pivot=df_pivot)  # Corrected variable name

def generate_summary(df, metric):
    summary = ""
    years = sorted(df['Years'].unique())

    for i in range(1, len(years)):
        previous_year = years[i-1]
        current_year = years[i]

        previous_value = df[(df['Item'] == metric) & (df['Years'] == previous_year)]['FY'].sum()
        current_value = df[(df['Item'] == metric) & (df['Years'] == current_year)]['FY'].sum()

        if previous_value == 0:  # Avoid division by zero
            change = "N/A"
        else:
            change = ((current_value - previous_value) / previous_value) * 100

        summary += f"From {previous_year} to {current_year}, {metric} changed by {change:.2f}%. "

    return summary.strip()



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
            return redirect(url_for('goingconcern.netdebt'))
        return f(*args, **kwargs)
    return decorated_function

@goingconcern_blueprint.route('/logout')
def logout():
    session.pop('user_info', None)  # This removes the user_info from the session
    return redirect(url_for('goingconcern.netdebt'))


@goingconcern_blueprint.route('/goingconcerncontrolsapp1')
def goingconcerncontrolsapp1():
    user_info = session.get('user_info', {})
    return render_template('goingconcerncontrolsapp1.html', user_info=user_info)

@goingconcern_blueprint.route('/goingconcerncontrolssignin', methods=['POST'])
def goingconcerncontrolssignin():
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
        return redirect(url_for('goingconcern.goingconcerncontrolsapp1'))
    else:
        # User not found or password does not match
        flash('Invalid credentials or user does not exist', 'error')
        return redirect(url_for('goingconcern.goingconcerncontrols'))

@goingconcern_blueprint.route('/goingconcerncontrols')
def goingconcerncontrols():
    # Check for flash messages
    messages = get_flashed_messages(with_categories=True)
    return render_template('goingconcerncontrols.html', messages=messages)

@goingconcern_blueprint.route('/goingconcerncontrolsapp2', methods=['GET', 'POST'])
def goingconcerncontrolsapp2():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['Q1'] = request.form.get('groupVerticalRadioExample111')
        user_responses['Q1commentNO'] = request.form.get('explanationInput') if user_responses['Q1'] == 'No' else None
        user_responses['Q1commentYES'] = request.form.get('explanationInput') if user_responses['Q1'] == 'Yes' else None
        user_responses['Q2'] = request.form.get('groupVerticalRadioExample222')
        user_responses['Q2commentNO'] = request.form.get('explanationInput2') if user_responses['Q2'] == 'No' else None
        user_responses['Q2commentYES'] = request.form.get('explanationInput2') if user_responses['Q2'] == 'Yes' else None
        user_responses['Q3'] = request.form.get('groupVerticalRadioExample333')
        user_responses['Q3commentNO'] = request.form.get('explanationInput3') if user_responses['Q3'] == 'No' else None
        user_responses['Q3commentYES'] = request.form.get('explanationInput3') if user_responses['Q3'] == 'Yes' else None
        user_responses['Q4'] = request.form.get('groupVerticalRadioExample111')
        user_responses['Q4commentNO'] = request.form.get('explanationInput4') if user_responses['Q4'] == 'No' else None
        user_responses['Q4commentYES'] = request.form.get('explanationInput4') if user_responses['Q4'] == 'Yes' else None

    return render_template('goingconcerncontrolsapp2.html',  user_info=user_info)

@goingconcern_blueprint.route('/goingconcerncontrolsapp3', methods=['GET', 'POST'])
def goingconcerncontrolsapp3():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['Q5'] = request.form.get('groupVerticalRadioExample555')
        user_responses['Q5commentNO'] = request.form.get('explanationInput5') if user_responses['Q5'] == 'No' else None
        user_responses['Q5commentYES'] = request.form.get('explanationInput5') if user_responses['Q5'] == 'Yes' else None
        user_responses['Q6'] = request.form.get('groupVerticalRadioExample666')
        user_responses['Q6commentNO'] = request.form.get('explanationInput6') if user_responses['Q6'] == 'No' else None
        user_responses['Q6commentYES'] = request.form.get('explanationInput6') if user_responses['Q6'] == 'Yes' else None
        user_responses['Q7'] = request.form.get('groupVerticalRadioExample777')
        user_responses['Q7commentNO'] = request.form.get('explanationInput7') if user_responses['Q7'] == 'No' else None
        user_responses['Q7commentYES'] = request.form.get('explanationInput7') if user_responses['Q7'] == 'Yes' else None
        user_responses['Q8'] = request.form.get('groupVerticalRadioExample888')
        user_responses['Q8commentNO'] = request.form.get('explanationInput8') if user_responses['Q8'] == 'No' else None
        user_responses['Q8commentYES'] = request.form.get('explanationInput8') if user_responses['Q8'] == 'Yes' else None

    return render_template('goingconcerncontrolsapp3.html',  user_info=user_info)

@goingconcern_blueprint.route('/goingconcerncontrolsapp4', methods=['GET', 'POST'])
def goingconcerncontrolsapp4():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['Q9'] = request.form.get('groupVerticalRadioExample999')
        user_responses['Q9commentNO'] = request.form.get('explanationInput9') if user_responses['Q9'] == 'No' else None
        user_responses['Q9commentYES'] = request.form.get('explanationInput9') if user_responses['Q9'] == 'Yes' else None
        user_responses['Q10'] = request.form.get('groupVerticalRadioExample10')
        user_responses['Q10commentNO'] = request.form.get('explanationInput10') if user_responses['Q10'] == 'No' else None
        user_responses['Q10commentYES'] = request.form.get('explanationInput10') if user_responses['Q10'] == 'Yes' else None
        user_responses['Q11'] = request.form.get('groupVerticalRadioExample11')
        user_responses['Q11commentNO'] = request.form.get('explanationInput11') if user_responses['Q11'] == 'No' else None
        user_responses['Q11commentYES'] = request.form.get('explanationInput11') if user_responses['Q11'] == 'Yes' else None
        user_responses['Q12'] = request.form.get('groupVerticalRadioExample12')
        user_responses['Q12commentNO'] = request.form.get('explanationInput12') if user_responses['Q12'] == 'No' else None
        user_responses['Q12commentYES'] = request.form.get('explanationInput12') if user_responses['Q12'] == 'Yes' else None

    return render_template('goingconcerncontrolsapp4.html',  user_info=user_info)

@goingconcern_blueprint.route('/goingconcerncontrolsapp5', methods=['GET', 'POST'])
def goingconcerncontrolsapp5():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['Q13'] = request.form.get('groupVerticalRadioExample13')
        user_responses['Q14'] = request.form.get('groupVerticalRadioExample14')
        user_responses['Q15'] = request.form.get('groupVerticalRadioExample15')
        user_responses['Q16'] = request.form.get('groupVerticalRadioExample16')
        user_responses['Q17'] = request.form.get('groupVerticalRadioExample17')
        user_responses['Q18'] = request.form.get('groupVerticalRadioExample18')

    return render_template('goingconcerncontrolsapp5.html',  user_info=user_info)


@goingconcern_blueprint.route('/goingconcerncontrolsapp6', methods=['GET', 'POST'])
def goingconcerncontrolsapp6():
    user_info = session.get('user_info', {})
    if request.method == 'POST':
        user_responses['Q19'] = request.form.get('groupVerticalRadioExample19')
        user_responses['Q20'] = request.form.get('groupVerticalRadioExample20')
        user_responses['Q21'] = request.form.get('groupVerticalRadioExample21')
        user_responses['Q22'] = request.form.get('groupVerticalRadioExample22')
        user_responses['Q23'] = request.form.get('groupVerticalRadioExample23')
        user_responses['Q24'] = request.form.get('groupVerticalRadioExample24')
        user_responses['Q25'] = request.form.get('groupVerticalRadioExample25')
        user_responses['Q26'] = request.form.get('groupVerticalRadioExample26')

    return render_template('goingconcerncontrolsapp6.html', responses=user_responses,  user_info=user_info)

@goingconcern_blueprint.route('/goingconcerncontrolsdownload_pdf', methods=['GET'])
def goingconcerncontrolsdownload_pdf():
    user_info = session.get('user_info', {})
    # Retrieve user responses
    document_title = "Going Concern Model Document Review"
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
    Q1 = user_responses.get('Q1', 'N/A')
    Q1commentYES = user_responses.get('Q1commentYES', 'N/A')
    Q1commentNO = user_responses.get('Q1commentNO', 'N/A')
    Q2 = user_responses.get('Q2', 'N/A')
    Q2commentYES = user_responses.get('Q2commentYES', 'N/A')
    Q2commentNO = user_responses.get('Q2commentNO', 'N/A')
    Q3 = user_responses.get('Q3', 'N/A')
    Q3commentYES = user_responses.get('Q3commentYES', 'N/A')
    Q3commentNO = user_responses.get('Q3commentNO', 'N/A')
    Q4 = user_responses.get('Q4', 'N/A')
    Q4commentYES = user_responses.get('Q4commentYES', 'N/A')
    Q4commentNO = user_responses.get('Q4commentNO', 'N/A')
    Q5 = user_responses.get('Q5', 'N/A')
    Q5commentYES = user_responses.get('Q5commentYES', 'N/A')
    Q5commentNO = user_responses.get('Q5commentNO', 'N/A')
    Q6 = user_responses.get('Q6', 'N/A')
    Q6commentYES = user_responses.get('Q6commentYES', 'N/A')
    Q6commentNO = user_responses.get('Q6commentNO', 'N/A')
    Q7 = user_responses.get('Q7', 'N/A')
    Q7commentYES = user_responses.get('Q7commentYES', 'N/A')
    Q7commentNO = user_responses.get('Q7commentNO', 'N/A')
    Q8 = user_responses.get('Q8', 'N/A')
    Q8commentYES = user_responses.get('Q8commentYES', 'N/A')
    Q8commentNO = user_responses.get('Q8commentNO', 'N/A')
    Q9 = user_responses.get('Q9', 'N/A')
    Q9commentYES = user_responses.get('Q9commentYES', 'N/A')
    Q9commentNO = user_responses.get('Q9commentNO', 'N/A')
    Q10 = user_responses.get('Q10', 'N/A')
    Q10commentYES = user_responses.get('Q10commentYES', 'N/A')
    Q10commentNO = user_responses.get('Q10commentNO', 'N/A')
    Q11 = user_responses.get('Q11', 'N/A')
    Q11commentYES = user_responses.get('Q11commentYES', 'N/A')
    Q11commentNO = user_responses.get('Q11commentNO', 'N/A')
    Q12 = user_responses.get('Q12', 'N/A')
    Q12commentYES = user_responses.get('Q12commentYES', 'N/A')
    Q12commentNO = user_responses.get('Q12commentNO', 'N/A')
    Q13 = user_responses.get('Q13', 'N/A')
    Q14 = user_responses.get('Q14', 'N/A')
    Q15 = user_responses.get('Q15', 'N/A')
    Q16 = user_responses.get('Q16', 'N/A')
    Q17 = user_responses.get('Q17', 'N/A')
    Q18 = user_responses.get('Q18', 'N/A')
    Q19 = user_responses.get('Q19', 'N/A')
    Q20 = user_responses.get('Q20', 'N/A')
    Q21 = user_responses.get('Q21', 'N/A')
    Q22 = user_responses.get('Q22', 'N/A')
    Q23 = user_responses.get('Q23', 'N/A')
    Q24 = user_responses.get('Q24', 'N/A')
    Q25 = user_responses.get('Q25', 'N/A')
    Q26 = user_responses.get('Q26', 'N/A')

    # Start Custom File Note Content
    file_note = f"""
    <b><font size="20">Going Concern Review Checklist</font></b>
    <br/><br/><br/>"""
    #--Q1--     
    if Q1 == 'Yes':                                                 
        if Q1commentYES:
            file_note += f"""<b>Accuracy of prior year Financial figures, closing balances and opening balances for current year</b><br/>
                Checked against prior year accounts/annual report. Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q1commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Accuracy of prior year Financial figures, closing balances and opening balances for current year</b><br/>
                Checked against prior year accounts/annual report. Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q1 == 'No':
        if Q1commentNO:
            file_note += f"""<b>Accuracy of prior year Financial figures, closing balances and opening balances for current year</b><br/>
                Checked against prior year accounts/annual report. Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity<br/>
                <b><font color="#913831">NO</font></b> ({ Q1commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Accuracy of prior year Financial figures, closing balances and opening balances for current year</b><br/>
                Checked against prior year accounts/annual report. Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    
    #--Q2--     
    if Q2 == 'Yes':                                                 
        if Q2commentYES:
            file_note += f"""<b>Accuracy of current year Financial figures</b><br/>
                Checked against current year draft financial reports (Prime reports, group 
                reports, others).
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q2commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Accuracy of current year Financial figures</b><br/>
                Checked against current year draft financial reports (Prime reports, group 
                reports, others).
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q2 == 'No':
        if Q2commentNO:
            file_note += f"""<b>Accuracy of current year Financial figures</b><br/>
                Checked against current year draft financial reports (Prime reports, group 
                reports, others).
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#913831">NO</font></b> ({ Q2commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Accuracy of current year Financial figures</b><br/>
                Checked against current year draft financial reports (Prime reports, group 
                reports, others).
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q3--     
    if Q3 == 'Yes':                                                 
        if Q3commentYES:
            file_note += f"""<b>Accuracy of LRP Figures included for all relevant years</b><br/>
                Checked against board approved current year LRP (Adjusted for FX) and master 
                LRP file prepared by treasury.
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q3commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Accuracy of LRP Figures included for all relevant years</b><br/>
                Checked against board approved current year LRP (Adjusted for FX) and master 
                LRP file prepared by treasury.
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q3 == 'No':
        if Q3commentNO:
            file_note += f"""<b>Accuracy of LRP Figures included for all relevant years</b><br/>
                Checked against board approved current year LRP (Adjusted for FX) and master 
                LRP file prepared by treasury.
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#913831">NO</font></b> ({ Q3commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Accuracy of LRP Figures included for all relevant years</b><br/>
                Checked against board approved current year LRP (Adjusted for FX) and master 
                LRP file prepared by treasury.
                Key Review Points: Sales, Profit, Interest, Tax, Operating Cashflow, 
                Restructuring, Non operational cashflows, Net Debt, Cash, Liquidity.<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q4--     
    if Q4 == 'Yes':                                                 
        if Q4commentYES:
            file_note += f"""<b>Data Sources Tab</b><br/>
                Review data souces tab and ensure all are accurate, current and are 
                correctly linked through to all scenario's<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q4commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Data Sources Tab</b><br/>
                Review data souces tab and ensure all are accurate, current and are 
                correctly linked through to all scenario's<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q4 == 'No':
        if Q4commentNO:
            file_note += f"""<b>Data Sources Tab</b><br/>
                Review data souces tab and ensure all are accurate, current and are 
                correctly linked through to all scenario's<br/>
                <b><font color="#913831">NO</font></b> ({ Q4commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Data Sources Tab</b><br/>
                Review data souces tab and ensure all are accurate, current and are 
                correctly linked through to all scenario's<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q5--     
    if Q5 == 'Yes':                                                 
        if Q5commentYES:
            file_note += f"""<b>Phasing of figures </b><br/>
                Are assumptions/workings used for the phasing of all figures correct? 
                Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non 
                operational cashflows, Amort + Depreciation<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q5commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Phasing of figures </b><br/>
                Are assumptions/workings used for the phasing of all figures correct? 
                Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non 
                operational cashflows, Amort + Depreciation<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q5 == 'No':
        if Q5commentNO:
            file_note += f"""<b>Phasing of figures </b><br/>
                Are assumptions/workings used for the phasing of all figures correct? 
                Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non 
                operational cashflows, Amort + Depreciation<br/>
                <b><font color="#913831">NO</font></b> ({ Q5commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Phasing of figures </b><br/>
                Are assumptions/workings used for the phasing of all figures correct? 
                Sales, Profit, Interest, Tax, Operating Cashflow, Restructuring, Non 
                operational cashflows, Amort + Depreciation<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q6--     
    if Q6 == 'Yes':                                                 
        if Q6commentYES:
            file_note += f"""<b>Validation of links within sheets, between tabs and to external documents.</b><br/>
                Check that all internal/external links are accurate and are correct. Links 
                to other tabs are correct and make sense and are easy to follow. Links 
                to external documents are minimised and were appropriate tested for 
                accuracy.
                Sufficent backup/explanation provided for all links<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q6commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Validation of links within sheets, between tabs and to external documents.</b><br/>
                Check that all internal/external links are accurate and are correct. Links 
                to other tabs are correct and make sense and are easy to follow. Links 
                to external documents are minimised and were appropriate tested for 
                accuracy.
                Sufficent backup/explanation provided for all links<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q6 == 'No':
        if Q6commentNO:
            file_note += f"""<b>Validation of links within sheets, between tabs and to external documents.</b><br/>
                Check that all internal/external links are accurate and are correct. Links 
                to other tabs are correct and make sense and are easy to follow. Links 
                to external documents are minimised and were appropriate tested for 
                accuracy.
                Sufficent backup/explanation provided for all links<br/>
                <b><font color="#913831">NO</font></b> ({ Q6commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Validation of links within sheets, between tabs and to external documents.</b><br/>
                Check that all internal/external links are accurate and are correct. Links 
                to other tabs are correct and make sense and are easy to follow. Links 
                to external documents are minimised and were appropriate tested for 
                accuracy.
                Sufficent backup/explanation provided for all links<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q7--     
    if Q7 == 'Yes':                                                 
        if Q7commentYES:
            file_note += f"""<b>Excel Formula's/Workings</b><br/>
                Check general excel formulas on all tabs for accuracy. Do they make 
                sense, are they adding correctly, are all relevant data points being 
                included? Check for circular references. <br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q7commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Excel Formula's/Workings</b><br/>
                Check general excel formulas on all tabs for accuracy. Do they make 
                sense, are they adding correctly, are all relevant data points being 
                included? Check for circular references. <br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q7 == 'No':
        if Q7commentNO:
            file_note += f"""<b>Excel Formula's/Workings</b><br/>
                Check general excel formulas on all tabs for accuracy. Do they make 
                sense, are they adding correctly, are all relevant data points being 
                included? Check for circular references. <br/>
                <b><font color="#913831">NO</font></b> ({ Q7commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Excel Formula's/Workings</b><br/>
                Check general excel formulas on all tabs for accuracy. Do they make 
                sense, are they adding correctly, are all relevant data points being 
                included? Check for circular references. <br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q8--     
    if Q8 == 'Yes':                                                 
        if Q8commentYES:
            file_note += f"""<b>Net Debt Calculations</b><br/>
                Are net debt calculations/formula's accurate. Do they correctly 
                calculate net debt? Are cash movement inputs being calculated 
                correctly? Are opening balances correctly linked to prior periods?<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q8commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Net Debt Calculations</b><br/>
                Are net debt calculations/formula's accurate. Do they correctly 
                calculate net debt? Are cash movement inputs being calculated 
                correctly? Are opening balances correctly linked to prior periods?<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q8 == 'No':
        if Q8commentNO:
            file_note += f"""<b>Net Debt Calculations</b><br/>
                Are net debt calculations/formula's accurate. Do they correctly 
                calculate net debt? Are cash movement inputs being calculated 
                correctly? Are opening balances correctly linked to prior periods?<br/>
                <b><font color="#913831">NO</font></b> ({ Q8commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Net Debt Calculations</b><br/>
                Are net debt calculations/formula's accurate. Do they correctly 
                calculate net debt? Are cash movement inputs being calculated 
                correctly? Are opening balances correctly linked to prior periods?<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q9--     
    if Q9 == 'Yes':                                                 
        if Q9commentYES:
            file_note += f"""<b>Liquidity Calculations</b><br/>
                Are liquidty calculations/formula's accurate. Do they correctly calculate 
                liquidty? Are cash movement inputs being calculated correctly? Are 
                opening balances correctly linked to prior periods?Are RCF figures 
                accurate and correctly reflect the RCF capacity for each period?<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q9commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Liquidity Calculations</b><br/>
                Are liquidty calculations/formula's accurate. Do they correctly calculate 
                liquidty? Are cash movement inputs being calculated correctly? Are 
                opening balances correctly linked to prior periods?Are RCF figures 
                accurate and correctly reflect the RCF capacity for each period?<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q9 == 'No':
        if Q9commentNO:
            file_note += f"""<b>Liquidity Calculations</b><br/>
                Are liquidty calculations/formula's accurate. Do they correctly calculate 
                liquidty? Are cash movement inputs being calculated correctly? Are 
                opening balances correctly linked to prior periods?Are RCF figures 
                accurate and correctly reflect the RCF capacity for each period?<br/>
                <b><font color="#913831">NO</font></b> ({ Q9commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Liquidity Calculations</b><br/>
                Are liquidty calculations/formula's accurate. Do they correctly calculate 
                liquidty? Are cash movement inputs being calculated correctly? Are 
                opening balances correctly linked to prior periods?Are RCF figures 
                accurate and correctly reflect the RCF capacity for each period?<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q10--     
    if Q10 == 'Yes':                                                 
        if Q10commentYES:
            file_note += f"""<b>Covenant Calculations</b><br/>
                Are all covenant inputs correct and being linked or calculated correctly? 
                Operating Profit, Amort + Depreciation, Net Debt, Leases, Interest. Are 
                all calculations/formula's accurate? EBITDA, EBITA, Net Cash for 
                Covenants, Net Debt/EBITDA Ratio, Covenant Interest, EBITDA 
                Headroom and EBITA Headroom for Int Cover.<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q10commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Covenant Calculations</b><br/>
                Are all covenant inputs correct and being linked or calculated correctly? 
                Operating Profit, Amort + Depreciation, Net Debt, Leases, Interest. Are 
                all calculations/formula's accurate? EBITDA, EBITA, Net Cash for 
                Covenants, Net Debt/EBITDA Ratio, Covenant Interest, EBITDA 
                Headroom and EBITA Headroom for Int Cover.<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q10 == 'No':
        if Q10commentNO:
            file_note += f"""<b>Covenant Calculations</b><br/>
                Are all covenant inputs correct and being linked or calculated correctly? 
                Operating Profit, Amort + Depreciation, Net Debt, Leases, Interest. Are 
                all calculations/formula's accurate? EBITDA, EBITA, Net Cash for 
                Covenants, Net Debt/EBITDA Ratio, Covenant Interest, EBITDA 
                Headroom and EBITA Headroom for Int Cover.<br/>
                <b><font color="#913831">NO</font></b> ({ Q10commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Covenant Calculations</b><br/>
                Are all covenant inputs correct and being linked or calculated correctly? 
                Operating Profit, Amort + Depreciation, Net Debt, Leases, Interest. Are 
                all calculations/formula's accurate? EBITDA, EBITA, Net Cash for 
                Covenants, Net Debt/EBITDA Ratio, Covenant Interest, EBITDA 
                Headroom and EBITA Headroom for Int Cover.<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q11--     
    if Q11 == 'Yes':                                                 
        if Q11commentYES:
            file_note += f"""<b>Risks </b><br/>
                Are risks correctly being linked to each downside scenario. Are risks 
                being accurately phased throughout each month/year on each 
                downside scenario. On the risk for EY tab, do the risks and associated 
                assumptions make sense and are they easy to follow? Has 
                backup/workings been provided for each risk and<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q11commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Risks </b><br/>
                Are risks correctly being linked to each downside scenario. Are risks 
                being accurately phased throughout each month/year on each 
                downside scenario. On the risk for EY tab, do the risks and associated 
                assumptions make sense and are they easy to follow? Has 
                backup/workings been provided for each risk and<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q11 == 'No':
        if Q11commentNO:
            file_note += f"""<b>Risks </b><br/>
                Are risks correctly being linked to each downside scenario. Are risks 
                being accurately phased throughout each month/year on each 
                downside scenario. On the risk for EY tab, do the risks and associated 
                assumptions make sense and are they easy to follow? Has 
                backup/workings been provided for each risk and<br/>
                <b><font color="#913831">NO</font></b> ({ Q11commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Risks </b><br/>
                Are risks correctly being linked to each downside scenario. Are risks 
                being accurately phased throughout each month/year on each 
                downside scenario. On the risk for EY tab, do the risks and associated 
                assumptions make sense and are they easy to follow? Has 
                backup/workings been provided for each risk and<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""
    #--Q12--     
    if Q12 == 'Yes':                                                 
        if Q12commentYES:
            file_note += f"""<b>Re-calculation of all key Metrics</b><br/>
                Using excel or another financial model recalculate all the key 
                outputs/metrics for each scenario to ensure they are correct.<br/>
                <b><font color="#AAFF00">YES</font></b>  ({ Q12commentYES })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Re-calculation of all key Metrics</b><br/>
                Using excel or another financial model recalculate all the key 
                outputs/metrics for each scenario to ensure they are correct.<br/>
                <b><font color="#AAFF00">YES</font></b><br/><br/><br/>"""
    elif Q12 == 'No':
        if Q12commentNO:
            file_note += f"""<b>Re-calculation of all key Metrics</b><br/>
                Using excel or another financial model recalculate all the key 
                outputs/metrics for each scenario to ensure they are correct.<br/>
                <b><font color="#913831">NO</font></b> ({ Q12commentNO })<br/><br/><br/>"""
        else:
            file_note += f"""<b>Re-calculation of all key Metrics</b><br/>
                Using excel or another financial model recalculate all the key 
                outputs/metrics for each scenario to ensure they are correct.<br/>
                <b><font color="#913831">NO</font></b><br/><br/><br/>"""
    else:
        file_note += f"""<b>N/A</b><br/><br/><br/>"""

    file_note += f"""
    <br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>
    <b><font size="20">Going Concern Data Source Checklist</font></b>
    <br/><br/><br/>"""

    #--Q13--     
    file_note += f"""<b>Long Range Plan figures (Original)</b><br/>
                Board Pack Approved Oct/Nov current year<br/>
                <b> {Q13}</b> <br/><br/><br/>"""
    #--Q14--     
    file_note += f"""<b>Next year Sales/Profit Phasing</b><br/>
                Sales/Profit and other phasin<br/>
                <b> {Q14}</b> <br/><br/><br/>"""
    #--Q15--     
    file_note += f"""<b>Interest Expense including phasing and lease interest split</b><br/>
                Interest Workings model (Which feeds into the LRP Board pack)<br/>
                <b> {Q15}</b> <br/><br/><br/>"""
    #--Q16--     
    file_note += f"""<b>Interest Expense including phasing and lease interest split</b><br/>
                Phasing<br/>
                <b> {Q16}</b> <br/><br/><br/>"""
    #--Q17--     
    file_note += f"""<b>Tax ETR Rates</b><br/>
                LRP Board pack (E-mail from tax team)<br/>
                <b> {Q17}</b> <br/><br/><br/>"""
    #--Q18--     
    file_note += f"""<b>Restructuring Costs </b><br/>
                Restructuring Workings<br/>
                <b> {Q18}</b> <br/><br/><br/>"""
    #--Q19--     
    file_note += f"""<b>5YP file</b><br/>
                Prepared by Treasury and forms basis of LRP/Board pack<br/>
                <b> {Q19}</b> <br/><br/><br/>"""
    #--Q20--     
    file_note += f"""<b>Opening Net Debt/Cash</b><br/>
                Annual Report<br/>
                <b> {Q20}</b> <br/><br/><br/>"""
    #--Q21--     
    file_note += f"""<b>RCF Facility</b><br/>
                Documents/Extracts/Workings back to GBP<br/>
                <b> {Q21}</b> <br/><br/><br/>"""
    #--Q22--     
    file_note += f"""<b>Amort + Depreciation</b><br/>
                Actuals Updated from PRIME<br/>
                <b> {Q22}</b> <br/><br/><br/>"""
    #--Q23--     
    file_note += f"""<b>Covenants</b><br/>
                RCF Document evidencing Covenants for:
                - Net Debt:EBITDA Thresholds (<4x)
                - INTEREST COVER Thresholds (>3x)<br/>
                <b> {Q23}</b> <br/><br/><br/>"""
    #--Q24--     
    file_note += f"""<b>Risk Data </b><br/>
               Going concern and viability divisional submissions<br/>
                <b> {Q24}</b> <br/><br/><br/>"""
    #--Q25--     
    file_note += f"""<b>M&A Forecast</b><br/>
                M&A Forecast<br/>
                <b> {Q25}</b> <br/><br/><br/>"""
    #--Q26--     
    file_note += f"""<b>Share Buy Back </b><br/>
                SBB Forecast <br/>
                <b> {Q26}</b> <br/><br/><br/>"""
    
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

@goingconcern_blueprint.route('/goingconcerncontrolsapp7')
def goingconcerncontrolsapp7():
    user_info = session.get('user_info', {})
    return render_template('goingconcerncontrolsapp7.html', user_info=user_info)
