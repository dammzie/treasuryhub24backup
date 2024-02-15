from flask import Blueprint, render_template
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import re
import ast
import os
import inspect
import plotly.graph_objects as go

goingconcern_blueprint = Blueprint('goingconcern', __name__, template_folder='templates5')


@goingconcern_blueprint.route('/netdebt')
def netdebt():
    
    #Import the weightings to dataframe dfw
    dfw = pd.read_csv('modelfiles/goingconcern22weightings.csv', header=0)
    #Add cumulative calcs for Amortisation and Depreciation, profit and interest for the covenant calcs
    dfw['Cum_Sales_wt']=dfw['Sales wt'].cumsum()
    dfw['Cum_A&D_wt']=dfw['A&D_Weight'].cumsum()
    dfw["Cum_profit_wt"]=dfw["Profit wt"].cumsum()
    dfw["Cum_op_cash_wt"]=dfw["Op cash wt"].cumsum()
    dfw["Cum_interest_wt"]=dfw["Interest cash wt"].cumsum()
    #Extract the 6th row from each (representing the H1 weighting)
    H1_Sales_wt = dfw.loc[5,'Cum_Sales_wt']
    H1_AD_wt = dfw.loc[5,'Cum_A&D_wt']
    H1_profit_wt = dfw.loc[5,'Cum_profit_wt']
    H1_op_cash_wt = dfw.loc[5,'Cum_op_cash_wt']
    H1_interest_cash_wt = dfw.loc[5,'Cum_interest_wt']
    
     
    
    #Create mini table for Half year weightings
    dfHYweights=pd.DataFrame()
    dfHYweights['Period']=["H1","H2"]
    dfHYweights['Sales']=[H1_Sales_wt,(1-H1_Sales_wt)]
    dfHYweights['Profit']=[H1_profit_wt,(1-H1_profit_wt)]
    dfHYweights['Op_cash']=[H1_op_cash_wt,(1-H1_op_cash_wt)]
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
      while j<Totyrs:
        yrs=str(dfProfit.loc[j,"Years"])
        dftots[op_cash+f" {yrs}"]= df.loc[j,op_cash]*dfw['Op cash wt']
        dfb[restr+f" {yrs}"]= df.loc[j,restr]*dfw['Restruct wt']
        dfb[opcashpostrestruc+f" {yrs}"]=dftots[op_cash+f" {yrs}"]+dfb[restr+f" {yrs}"]
        dfa[intcash+f" {yrs}"]=df.loc[j,intcash]*dfw['Interest cash wt']
        dfa[txcash+f" {yrs}"]=df.loc[j,txcash]*dfw['Tax cash wt']
        dfa[dividends+f" {yrs}"]=df.loc[j,dividends]*dfw['Dividends wt']
        dfa[acqsdisps+f" {yrs}"]=df.loc[j,acqsdisps]*dfw['M&A wt']
        dfa[newequity+f" {yrs}"]=df.loc[j,newequity]*dfw['Equity wt']
        dfa[other+f" {yrs}"]=df.loc[j,other]*dfw['Other wt']
        dftots[freecash+f" {yrs}"]= dfb[opcashpostrestruc+f" {yrs}"]+dfa[intcash+f" {yrs}"]+dfa[txcash+f" {yrs}"]
        dftots[othercash+f" {yrs}"]=+dfa[dividends+f" {yrs}"]+dfa[acqsdisps+f" {yrs}"]+dfa[newequity+f" {yrs}"]+dfa[other+f" {yrs}"]
        dftots[netdebtch+f" {yrs}"]= dftots[freecash+f" {yrs}"]+dfa[dividends+f" {yrs}"]+dfa[acqsdisps+f" {yrs}"]+dfa[newequity+f" {yrs}"]+dfa[other+f" {yrs}"]
        dftots[ytdnetdebtch+f" {yrs}"]=dftots[netdebtch+f" {yrs}"].cumsum()
        j=j+1
      i=i+1
    
    #Calculate net debt using opening net debt £350m
     
    
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
    
    #Join annual net cashflows to create a single series
    list = dfp['Net Cashflow '+str(dfProfit.loc[0,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[1,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[2,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[3,"Years"])].tolist()+dfp['Net Cashflow '+str(dfProfit.loc[4,"Years"])].tolist()
    
     
    
    #Print the dataframe
    #Insert the month and year !!!!NOTE THIS IS ONLY SET UP FOR 5 YEARS!!!! If more or less are used it won't work
    list2 = dfw['Month'].tolist()*5
    list4 = [str(dfProfit.loc[0,"Years"]),str(dfProfit.loc[0,"Years"])]
    list5 = [str(dfProfit.loc[1,"Years"]),str(dfProfit.loc[1,"Years"])]
    list6 = [str(dfProfit.loc[2,"Years"]),str(dfProfit.loc[2,"Years"])]
    list7 = [str(dfProfit.loc[3,"Years"]),str(dfProfit.loc[3,"Years"])]
    list8 = [str(dfProfit.loc[4,"Years"]),str(dfProfit.loc[4,"Years"])]
    list9 = (list4*6)+(list5*6)+(list6*6)+(list7*6)+(list8*6)
    #Join annual free cashflows to create a single series
    list3 = dfp['Free Cashflow '+str(dfProfit.loc[0,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[1,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[2,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[3,"Years"])].tolist()+dfp['Free Cashflow '+str(dfProfit.loc[4,"Years"])].tolist()
    
     
    
    #Create dataframe to show each year's cashflows
    dfp['Month']=dfw["Month"]
    
     
    
    #Create a dataframe for cashflows
    dfflows=pd.DataFrame()
    dfflows["Month"] = list2
    dfflows["Years"] = list9
    dfflows["Netcashchange"] = list
    dfflows["Freecashchange"] = list3
    dfflows['Cum Net debt change'] = dfflows['Netcashchange'].cumsum()
    dfflows["Net debt"] = dfflows['Cum Net debt change'] + x
    dfflows["MonthYears"] = dfflows["Month"] + dfflows["Years"]
    dfflows["MonthYears"] = pd.to_datetime(dfflows["MonthYears"], format='%b%Y')
    
    
    
    
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
    
    
    # Create a new dataframe where Month is June or December
    # Note: Month in datetime is represented by integers where January is 1 and December is 12
    df_filtered = dfflows[(dfflows['Month'] == 6) | (dfflows['Month'] == 12)][['Net debt', 'Scen1netdebtchange', 'Scen2netdebtchange', 'Scen3netdebtchange']]
    
    
    # Create a new dataframe with only the specified columns and where Month is June or December
    df_filtered = dfflows[(dfflows['Month'] == 6) | (dfflows['Month'] == 12)][['MonthYears','Net debt', 'Scen1netdebtchange', 'Scen2netdebtchange', 'Scen3netdebtchange']]
    
    # Extract year and month from 'MonthYears' column
    df_filtered['Year'] = df_filtered['MonthYears'].dt.year
    df_filtered['Month'] = df_filtered['MonthYears'].dt.month
    
    # Pivot the dataframe to have one row per year and columns for each scenario
    df_pivot = df_filtered.pivot_table(index='Year', columns='Month', values=['Net debt','Scen1netdebtchange', 'Scen2netdebtchange', 'Scen3netdebtchange'], aggfunc='sum')
    
    
    # Extract H1 (June) and H2 (December) for each scenario
    H1_net = df_pivot.loc[:, ('Net debt', 6)] 
    H2_net = df_pivot.loc[:, ('Net debt', 12)]
    
    H1_Scen1 = df_pivot.loc[:, ('Scen1netdebtchange', 6)] 
    H2_Scen1 = df_pivot.loc[:, ('Scen1netdebtchange', 12)]
    
    H1_Scen2 = df_pivot.loc[:, ('Scen2netdebtchange', 6)] 
    H2_Scen2 = df_pivot.loc[:, ('Scen2netdebtchange', 12)]
    
    H1_Scen3 = df_pivot.loc[:, ('Scen3netdebtchange', 6)] 
    H2_Scen3 = df_pivot.loc[:, ('Scen3netdebtchange', 12)]
    
    #!! To do = simplify the list approach (lists 4-8 could be simplified)
    dfCovenant_HY = pd.DataFrame()
    dfCovenant_HY['Profit1'] = dfProfit.loc[0:3,'Profit']
    dfCovenant_HY['Profit2'] = [dfProfit.loc[1,'Profit']]+[dfProfit.loc[2,'Profit']]+[dfProfit.loc[3,'Profit']]+[dfProfit.loc[4,'Profit']]
    dfCovenant_HY['Prorated Profit'] = (dfCovenant_HY['Profit1']*(1-H1_profit_wt))+(dfCovenant_HY['Profit2']*H1_profit_wt)
    
     
    
    dfCovenant_HY['Amort&D1'] = df.loc[0:3,'A&D']
    dfCovenant_HY['Amort&D2'] = [df.loc[1,'A&D']]+[df.loc[2,'A&D']]+[df.loc[3,'A&D']]+[df.loc[4,'A&D']]
    dfCovenant_HY['Prorated A&D'] = (dfCovenant_HY['Amort&D1']*(1-H1_AD_wt))+(dfCovenant_HY['Amort&D2']*H1_AD_wt)
    
     
    
    dfCovenant_HY['Amort_1'] = df.loc[0:3,'Amort']
    dfCovenant_HY['Amort_2'] = [df.loc[1,'Amort']]+[df.loc[2,'Amort']]+[df.loc[3,'Amort']]+[df.loc[4,'Amort']]
    dfCovenant_HY['Prorated Amort'] = (dfCovenant_HY['Amort_1']*(1-H1_AD_wt))+(dfCovenant_HY['Amort_2']*H1_AD_wt)
    
     
    
    dfCovenant_HY['Interest1'] = df.loc[0:3,'InterestP&L']
    dfCovenant_HY['Interest2'] = [df.loc[1,'InterestP&L']]+[df.loc[2,'InterestP&L']]+[df.loc[3,'InterestP&L']]+[df.loc[4,'InterestP&L']]
    dfCovenant_HY['LeaseInt1'] = df.loc[0:3,'LeaseInterest']
    dfCovenant_HY['LeaseInt2'] = [df.loc[1,'LeaseInterest']]+[df.loc[2,'LeaseInterest']]+[df.loc[3,'LeaseInterest']]+[df.loc[4,'LeaseInterest']]
    dfCovenant_HY['Prorated Interest'] = ((dfCovenant_HY['Interest1']-dfCovenant_HY['LeaseInt1'])*(1-(dfHYweights.loc[0,'Interest'])))+((dfCovenant_HY['Interest2']-dfCovenant_HY['LeaseInt2'])*(dfHYweights.loc[0,'Interest']))
    
    
     
    
    dfCovenant_HY['HY net debt'] = [dfflows.loc[17,"Net debt"],dfflows.loc[29,"Net debt"],dfflows.loc[41,"Net debt"],dfflows.loc[53,"Net debt"]]
    dfCovenant_HY['LeasesHY'] = [df.loc[1,'Leases']]+[df.loc[2,'Leases']]+[df.loc[3,'Leases']]+[df.loc[4,'Leases']]
    dfCovenant_HY['HY cov net debt'] = dfCovenant_HY['HY net debt'] + dfCovenant_HY['LeasesHY']
    # Calculate HY EBITDA, EBITA, and ratios
    #Calculate covenant headroom - Net debt to EBITDA
    dfCovenant_HY["Cov EBITDA HY"] = dfCovenant_HY['Prorated Profit'] - dfCovenant_HY['Prorated A&D']
    dfCovenant_HY["Cov EBITA HY"] = dfCovenant_HY["Cov EBITDA HY"] + dfCovenant_HY["Prorated Amort"]
    dfCovenant_HY["Cov Leverage ratio HY"] = dfCovenant_HY["HY cov net debt"] / dfCovenant_HY["Cov EBITDA HY"]
    dfCovenant_HY["Cov debt headroom HY"] = 4 * dfCovenant_HY["Cov EBITDA HY"] + dfCovenant_HY["HY cov net debt"]
    dfCovenant_HY["Cov EBITDA headroom HY"] = ((dfCovenant_HY["Cov EBITDA HY"]*4 + (dfCovenant_HY["HY cov net debt"]))/5)
    
     
    
    dfNetdebtCovenantHY = dfCovenant_HY[["Cov EBITDA HY","HY cov net debt","Cov Leverage ratio HY","Cov debt headroom HY","Cov EBITDA headroom HY"]]
    dfNetdebtCovenantHY = dfNetdebtCovenantHY.round(decimals = 1)
    
     
    
    # Calculate covenant headroom - Interest to EBITA
    
     
    
    dfCovenant_HY["Cov Interest cover HY"] = -dfCovenant_HY["Cov EBITA HY"] / dfCovenant_HY['Prorated Interest']
    dfCovenant_HY["Cov profit headroom HY"] = dfCovenant_HY["Cov EBITA HY"] + (3 * dfCovenant_HY['Prorated Interest'])
    dfInterestCovenantHY = dfCovenant_HY[["Cov EBITA HY","Prorated Interest","Cov Interest cover HY","Cov profit headroom HY"]]
    dfInterestCovenantHY = dfInterestCovenantHY.round(decimals = 1)
    
    
     
    
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
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (H1_net).round(decimals=1)
            dfHY_nos["H2"] = (dfProfit["Profit"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (df["Net debt"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))
    
    
    #Defining Libraries for RSS
    
    def calculate_RSS(item):
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
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (df[f"{Scenlist[2]} net debt"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[2]} net debt"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
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
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (df[f"{Scenlist[2]} net debt"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (df[f"{Scenlist[2]} net debt"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))
    
            
    # Defining Libraries for 5+7        
    
    def calculate_57(item):
        dfHY_nos = pd.DataFrame()
        dfHY_nos["Years"] = df["Years"]
        
        if item == "Sales":
            dfHY_nos["H1"] = (fsdf[f"{fsScenlist[1]} op sales pst"] * fsH1_Sales_wt).round(decimals=1)
            dfHY_nos["H2"] = (fsdf[f"{fsScenlist[1]} op sales pst"] * (1 - fsH1_Sales_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Sales"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Profits":
            dfHY_nos["H1"] = (fsdf[f"{fsScenlist[1]} op profit pst"] * fsH1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (fsdf[f"{fsScenlist[1]} op profit pst"] * (1 - fsH1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Profits"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Operating Cash Flow":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (fsdf[f"{fsScenlist[1]} op cash pst"] * fsH1_op_cash_wt).round(decimals=1)
            dfHY_nos["H2"] = (fsdf[f"{fsScenlist[1]} op cash pst"] * (1 - fsH1_op_cash_wt)).round(decimals=1)
            dfHY_nos["FY"] = (dfHY_nos["H1"] + dfHY_nos["H2"]).round(decimals=1)
            dfHY_nos["Item"] = "Operating Cash Flow"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        elif item == "Net Debt":
            # ... (similar adjustments for other items)
            dfHY_nos["H1"] = (fsdf[f"{fsScenlist[2]} net debt"] * H1_profit_wt).round(decimals=1)
            dfHY_nos["H2"] = (fsdf[f"{fsScenlist[2]} net debt"] * (1 - H1_profit_wt)).round(decimals=1)
            dfHY_nos["FY"] = (df['Cum Net debt change']).round(decimals=1)
            dfHY_nos["Item"] = "Net Debt"
            return dfHY_nos[["Item", "Years", "H1", "H2", "FY"]]
        
        else:
            raise ValueError("Invalid item: {}".format(item))       
    
    #----------------------------------------------------------------------------------------
    # End
    #----------------------------------------------------------------------------------------
    
    # Data and labels
    labels = ["Sales", "Operating Profits", "Operating Cash Flow", "Net Debt"]
    scenarios = ["Base Scenario", "Reverse stress scenario (Going Concern) AOP", 
                 "Severe but plausible AOP", "Severe but plausible 5+7"]
    
    # Start with an empty dataframe
    df_final = pd.DataFrame()
    
    # Iterate over each dataframe
    for df, label in zip(df_final, labels):
        # Unpivot the dataframe
        df_melt = df.melt(id_vars='Years', var_name='HY', value_name='Values')
        df_melt['HY'] = df_melt['HY'].str.split('_').str[1]  # Remove suffix from 'HY' column
        df_melt.sort_values(['Years', 'HY'], inplace=True)
        
    # Data and labels
    labels = ["Sales", "Operating Profits", "Operating Cash Flow", "Net Debt"]
    # Create an ordered categorical type with your specific order
    labels_category = pd.CategoricalDtype(categories=labels, ordered=True)
    
    scenarios = ["Base Scenario", "Reverse stress scenario (Going Concern) AOP", 
                 "Severe but plausible AOP", "Severe but plausible 5+7"]
    
    # Start with an empty dataframe
    df_final = pd.DataFrame()
    
    # Iterate over each scenario and item
    for scenario in scenarios:
        for item in labels:
            # Get the calculated values for the current scenario and item
            if scenario == "Base Scenario":
                df_item = calculate_base_scenario(item)
            elif scenario == "Reverse stress scenario (Going Concern) AOP":
                df_item = calculate_RSS(item)
            elif scenario == "Severe but plausible AOP":
                df_item = calculate_SBP(item)
            elif scenario == "Severe but plausible 5+7":
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
    
    
    
    def generate_summary(df_pivot, metric):
        summary = ""
        
        for year in range(2023, 2027):
                current_year_value = df_pivot.loc[(df_pivot[('Item', '')] == metric), (year, 'FY')].values[0]
                previous_year_value = df_pivot.loc[(df_pivot[('Item', '')] == metric), (year - 1, 'FY')].values[0]
                change = ((current_year_value - previous_year_value) / previous_year_value) * 100
        summary += f" in year {year}, there was a change of {change:.2f}%,"
    
        summary = summary[:-1]  # Removing the last comma
    
        summary += f" concluding with the most recent year. This indicates the overall trend and performance for {metric}."
    
        return summary
    
    sales_summary = generate_summary(df_pivot, "Sales")
    profit_summary = generate_summary(df_pivot, "Operating Profits")
    cash_summary = generate_summary(df_pivot, "Operating Cash Flow")
    
    
    
    #-------------------------------------------------------netdebt graph ---------------------------
    # Create a figure
    fig = go.Figure()
    
    # Add traces (lines) for each series of data
    fig.add_trace(go.Scatter(x=dfflows["MonthYears"], y=dfflows["Net debt"], mode='lines', name='Net debt'))
    fig.add_trace(go.Scatter(x=dfflows["MonthYears"], y=dfflows['Scen1netdebt'], mode='lines', name=f"{Scenlist[0]} Net debt"))
    fig.add_trace(go.Scatter(x=dfflows["MonthYears"], y=dfflows['Scen2netdebt'], mode='lines', name=f"{Scenlist[1]} Net debt"))
    fig.add_trace(go.Scatter(x=dfflows["MonthYears"], y=dfflows['Scen3netdebt'], mode='lines', name=f"{Scenlist[2]} Net debt"))
    
    # Add title and labels
    fig.update_layout(title='Net Debt over time', xaxis_title='Months', yaxis_title='Net Debt (£m)')
    
    # Save the figure as an HTML string
    graph_html = fig.to_html(full_html=False)

    return render_template('netdebt.html', graph_html=graph_html, df_pivot=df_pivot, sales_summary=sales_summary, profit_summary=profit_summary, cash_summary=cash_summary)

    # Flask application for Cash Flow page
    @goingconcern_blueprint.route('/cashflow')
    def cashflow():
        # Your code for Cash Flow page goes here
        return render_template('cashflow.html')

    # Flask application for EditBA page
    @goingconcern_blueprint.route('/editba')
    def editba():
        # Your code for EditBA page goes here
        return render_template('editba.html')

