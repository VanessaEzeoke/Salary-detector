import numpy as np
import pandas as pd
from collections import Counter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime

def round_custom(amount):
    """
    A function that rounds customers inflow down or up, depending on the overflow, to create a custom range 
    for customer's transtion
    
    Arg:
    amount- float (tran_amt in table)
    
    Returns:
    int (amount rounded up/down)
    """
    n = len(str(round(amount)))
    if n==1:
        return 10 if amount>=5 else 0
    if n>=2:
        rem = 10**(n-1)
        ovflw = round(amount)%rem
        threshold = 5*rem/10
        if ovflw>threshold:
            return round(amount) - round(amount)%rem + (2*threshold)
        else:
            return round(amount) - round(amount)%rem
        
def generate_range(amount, intvl):
    """
    A function that creates a threshold range to group customers transaction amounts
    
    Arg:
    amount - float (transaction amount in htd)
    intvl - float - optional (interval- default is 0.1)
    
    Returns:
    string - interval ranges
    """
    lower_bound = amount*(1-intvl)
    upper_bound = amount*(1+intvl)
    
    return str(round_custom(lower_bound)) +'-'+ str(round_custom(upper_bound))

def getPeriodofInflow(dframe):
    """
    Returns the date range of each account's inflow
    
    Arg:
    df - sliced Dataframe per customer
    
    Return:
    str
    """
    # dframe = df.copy()
    mindate = str(dframe.TRAN_DATE.min())
    maxdate = str(dframe.TRAN_DATE.max())
    
    return mindate + ' - ' + maxdate

def checkRecency(dframe, precision):
    """
    Check if customer's inflow flagged as salaried, happened in the most recent "precision" months
    
    Arg:
    df - sliced dataframe
    precision - number of most recent months being reviewed (default =1)
    
    Return:
    Bool
    """
    # dframe = df.copy()
    now = pd.to_datetime(datetime.today())
    ref = now - relativedelta(months=precision)
    ref = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    max_date = dframe.TRAN_DATE.max()
    
    return ref<=max_date<=now

def getAvgAmt(dframe):
    """Return average of tran_amount per bucket/interval per account
    
    Arg:
    df- dataframe of identified salary
    
    Return:
    float
    """
    # dframe = df.copy()
    amt_list = dframe.TRAN_AMT.to_list()
    
    if len(amt_list)>0:
        return sum(amt_list)/len(amt_list)
    else:
        return 0

def checkPension(dframe):
    """Identify pension related inflow based on transaction particulars
    
    Arg:
    df- dataframe(initial)
    
    Returns:
    Bool
    """
    # dframe = df.copy()
    check1 = dframe.TRAN_PARTICULAR.str.contains('PEN').any()
    check2 = dframe.TRAN_PARTICULAR.str.contains('PFA').any()
    check3 = dframe.TRAN_PARTICULAR.str.contains('ANNUI').any()
    check4 = dframe.TRAN_PARTICULAR.str.contains('RSA').any()
    check5 = dframe.TRAN_PARTICULAR.str.contains('trGP FT').any()
    
    if check1==True:
        return True
    if check2==True:
        return True
    if check3==True:
        return True
    if check4==True:
        return True
    if check5==True:
        return True
    return False

def mth_idx(mth):
    """
    Returns the total indices of months customers received salary
    Arg:
    mth : month number salaried was received
    
    Return:
    list
    """
    ref = [1,2,3,4,5,6,7,8,9,10,11,12,1,2,3,4,5,6,7,8,9,10,11,12]
    idx = []
    for i in range(len(ref)):
        if ref[i]==mth:
            idx.append(i)
            
    return idx

def check_Month_Consistency(dframe, size):
    """
    Get consistency of customer's inflows
    
    Args:
    df - sliced dataframe of possible salaries
    size - a sliding window to check for atleast 'size' consistent inflows. Optional( default=3)
    
    Return:
    Bool
    
    """
    ref = [1,2,3,4,5,6,7,8,9,10,11,12,1,2,3,4,5,6,7,8,9,10,11,12]
    # dframe=df.copy()
    arr = dframe.Month.to_list()
    n= len(arr)
    trav_length = n-size+1

    for i in range(trav_length):
        window = arr[i:i+size]
        idx_list = mth_idx(window[0])
        ref1 = ref[idx_list[0]:idx_list[0]+size]
        check = ref1==window

        if check==True:
            return True
        else:
            try:
                ref2 = ref[idx_list[1]:idx_list[1]+size]
                check2 = ref2==window

                if check2==True:
                    return True
            except:
                continue
                
    return False

### Check for Pension guys
def get_label(dframe, perc, size, precision):
    """
    Get classification of customer's transations as salaried, non-salaried, pensioners and salaried pensioners
    
    Arg:
    df - sliced dataframe per account
    perc - percentage (float), inflows relative to the total months provided (optional; default= 0.5)
    size - consistency per month (int)
    precision- number of most recent months being reviewed to check salary recency (default =1) (int)
    
    Return:
    dictionary
    """
    # dframe = df.copy()
    dframe['TRAN_DATE'] = pd.to_datetime(dframe['TRAN_DATE'], errors='coerce')
    dframe = dframe.loc[(dframe.transaction_type=='C')].sort_values(by='TRAN_DATE')
    
    dframe['TRAN_PARTICULAR'] = dframe['TRAN_PARTICULAR'].astype(str)
    dframe['TRAN_PARTICULAR'] = dframe['TRAN_PARTICULAR'].str.upper()
    dframe['TRAN_PARTICULAR'] = dframe['TRAN_PARTICULAR'].apply(lambda x: np.where(str(x).find('REV')!=-1, np.nan, x))
    dframe['TRAN_PARTICULAR'] = dframe['TRAN_PARTICULAR'].apply(lambda x: np.where(str(x).find('RVR')!=-1, np.nan, x))

    dframe = dframe.loc[~(dframe.TRAN_PARTICULAR=='nan')]

    dframe['Year'] = pd.DatetimeIndex(dframe['TRAN_DATE']).year
    dframe['Month'] = pd.DatetimeIndex(dframe['TRAN_DATE']).month
    dframe['Day'] = pd.DatetimeIndex(dframe['TRAN_DATE']).day
    dframe['Trans_Group'] = dframe.TRAN_AMT.apply(lambda amt: generate_range(amt, 0.05))
    Record_count= len(dframe)
    
    n_consistent = round(perc*dframe.Month.nunique())
    options = Counter(dframe.Trans_Group.to_list())
    dict_keys = list(options.keys())
    dict_vals = list(options.values())
    
    idx = []
    for i in range(n_consistent,dframe.Month.nunique()+10):
        if i in dict_vals:
            idx.append(dict_vals.index(i))
            
    possible_sal_range = []
    for i in idx:
        possible_sal_range.append(dict_keys[i])
        
    output = {}
    output['Label'] = []
    output['Duration'] = []
    output['Avg Salary Inflow'] = []
    output['Avg Pension Inflow'] = []
    output['Avg Inflow'] = []
    output['Trans Group'] = []
    output['inflowCount'] = []
    output['inflowPrevMonth'] = []
    output['Record_count'] = []
    
    AvgAmt_ifnonSal = getAvgAmt(dframe)
    period_ifnonSal = getPeriodofInflow(dframe)
    
    if len(possible_sal_range)>0:
        for i in possible_sal_range:
            tmp = dframe.loc[dframe.Trans_Group==i]
            pensionCheck = checkPension(tmp)
            mthConsistency = check_Month_Consistency(tmp, size)
            AvgAmt = getAvgAmt(tmp)
            period = getPeriodofInflow(tmp)
            Recency = checkRecency(tmp, precision)
            inflowCount = len(tmp)

            if mthConsistency == True:
                if pensionCheck==True:
                    output['Label'].append('Pensioner')
                    output['Duration'].append(period)
                    output['Avg Salary Inflow'].append(np.nan)
                    output['Avg Pension Inflow'].append(AvgAmt)
                    output['Avg Inflow'].append(np.nan)
                    output['Trans Group'].append(i)
                    output['inflowCount'].append(inflowCount)
                    output['inflowPrevMonth'].append(Recency)
                    output['Record_count'].append(Record_count)

                else:
                    output['Label'].append('Salaried')
                    output['Duration'].append(period)
                    output['Avg Salary Inflow'].append(AvgAmt)
                    output['Avg Pension Inflow'].append(np.nan)
                    output['Avg Inflow'].append(np.nan)
                    output['Trans Group'].append(i)
                    output['inflowCount'].append(inflowCount)
                    output['inflowPrevMonth'].append(Recency)
                    output['Record_count'].append(Record_count)
            else:
                output['Label'].append('Non Salaried')
                output['Duration'].append(period)
                output['Avg Salary Inflow'].append(np.nan)
                output['Avg Pension Inflow'].append(np.nan)
                output['Avg Inflow'].append(AvgAmt)
                output['Trans Group'].append(i)
                output['inflowCount'].append(np.nan)
                output['inflowPrevMonth'].append(Recency)
                output['Record_count'].append(Record_count)
    else:
        output['Label'].append('Non Salaried')
        output['Duration'].append(period_ifnonSal)
        output['Avg Salary Inflow'].append(np.nan)
        output['Avg Pension Inflow'].append(np.nan)
        output['Avg Inflow'].append(AvgAmt_ifnonSal)
        output['Trans Group'].append(np.nan)
        output['inflowCount'].append(np.nan)
        output['inflowPrevMonth'].append(False)
        output['Record_count'].append(Record_count)
            
    return output

def getFinalResults(class_dict):
    """
    Takes output from getlabels() and retunrs the final clasification per account ie, salaried, pensioner, etc
    
    Arg:
    class_dict: a dictionary of lists
    
    Returns:
    Dataframe
    """
    labels = set(class_dict['Label'])
    df = pd.DataFrame(class_dict)
    
    if 'Salaried' in labels and 'Pensioner' in labels:
        n = len(df.loc[(df.Label=='Salaried') & (df.Label=='Pensioner')])
        tmp_sal = df.loc[(df.Label=='Salaried')].sort_values('Avg Salary Inflow').iloc[-1:,:]
        tmp_pen = df.loc[(df.Label=='Pensioner')].sort_values('Avg Pension Inflow').iloc[-1:,:]['Avg Pension Inflow'].iloc[0]
        tmp_sal['Avg Pension Inflow'].fillna(tmp_pen, inplace=True)
        tmp_sal['Label'].replace({'Salaried': 'Salaried-Pensioner'}, inplace=True)
        tmp_sal['possibleGroups'] = n
        return tmp_sal
    
    if 'Salaried' in labels and 'Pensioner' not in labels:
        n = len(df.loc[(df.Label=='Salaried')])
        tmp_sal = df.loc[(df.Label=='Salaried')].sort_values('Avg Salary Inflow').iloc[-1:,:]
        tmp_sal['possibleGroups'] = n
        return tmp_sal
    
    if 'Salaried' not in labels and 'Pensioner' in labels:
        n = len(df.loc[(df.Label=='Pensioner')])
        tmp_pen = df.loc[(df.Label=='Pensioner')].sort_values('Avg Pension Inflow').iloc[-1:,:]
        tmp_pen['possibleGroups'] = n
        return tmp_pen
    
    if 'Salaried' not in labels and 'Pensioner' not in labels:
        tmp = df.loc[(df.Label=='Non Salaried')].sort_values('Avg Inflow').iloc[-1:,:]
        tmp['possibleGroups'] = 0
        return tmp
        
        
def getBreakdown_Total(data):
    """
    Takes in the original dataframe and returns a filtered dataframe containing all the 
    specific transactions identified as salaried/pension etc
    
    Arg:
    data: a dataframe
    
    Returns:
    Dataframe
    """
    
    AccIDs = data.Acct_ID.unique()
    
    base = pd.DataFrame({'Acct_ID':[], 'transaction_type':[], 
              'TRAN_PARTICULAR':[], 'TRAN_DATE':[], 'TRAN_AMT':[], 'Account_type':[], 'Trans_Group':[]})
    
    count=0
    n = len(AccIDs)
    
    for Acc in AccIDs:
        
        tmp = data.loc[data.Acct_ID==Acc]
        tmp = tmp.loc[tmp.transaction_type=='C']
        tmp['Trans_Group'] = tmp.TRAN_AMT.apply(lambda amt: generate_range(amt, 0.1))
        tmp['TRAN_PARTICULAR'] = tmp['TRAN_PARTICULAR'].str.upper()
        tmp['TRAN_PARTICULAR'] = tmp['TRAN_PARTICULAR'].apply(lambda x: np.where(str(x).find('REV')!=-1, np.nan, x))
        tmp['TRAN_PARTICULAR'] = tmp['TRAN_PARTICULAR'].apply(lambda x: np.where(str(x).find('RVR')!=-1, np.nan, x))
        tmp = tmp.loc[~(tmp.TRAN_PARTICULAR=='nan')]
        
        temp_df = pd.DataFrame(get_label(tmp, perc=0.5, size=3, precision=1))
        temp_df = temp_df.loc[(temp_df.Label=='Salaried')|(temp_df.Label=='Pensioner')]
        groups = temp_df['Trans Group'].to_list()
        
        for group in groups:
            ref = tmp.loc[(tmp.Trans_Group==group)].sort_values(by='TRAN_DATE')
            base = pd.concat([base, ref.reset_index(drop=True)])
        
        count+=1
        LoopPerc = round((count/n) * 100, 2)
        
        if LoopPerc%10==0:
            print('========Progress: ' + str(LoopPerc) + '% complete')
            
    return base.reset_index(drop=True)

def runAll(slice, perc=0.5, size=3, precision=1):
    """
    Takes a sliced dataframe per customer (containing transaction records) and outputs a single record with final classification
    
    Arg:
    slice: a sliced dataframe
    perc - percentage (float), inflows relative to the total months provided (optional; default= 0.5)
    size - consistency per month (int)
    precision- number of most recent months being reviewed to check salary recency (default =1) (int)
    
    Returns:
    Dataframe
    """
    res = get_label(slice, perc=perc, size=size, precision=precision)
    final_res = getFinalResults(res)
    
    return final_res

def get_batch(dframe, cores):
    """
    Takes in the original dataframe and splits into several batches based on the number of cores of the machine
    
    Arg:
    slice: a dataframe
    cores: number of cores of the machine
    
    Returns:
    an array of Dataframes
    """
    batches = np.array_split(dframe.Acct_ID.unique(), cores)
    
    out_lst = []
    for i in range(cores):
        output = dframe.loc[dframe.Acct_ID.isin(batches[i])]
        output = np.array_split(output, 1)[0]
        out_lst.append(output)
    
    return out_lst


def job(dframe):
    """
    Takes a sliced dataframe per batch (refer to get_batch above) and outputs the classification results per batch
    
    Arg:
    slice: a sliced dataframe
    
    Returns:
    Dataframe
    """
    cols = [x for x in dframe.columns if x!= 'Acct_ID']
    result = dframe.groupby('Acct_ID')[cols].apply(runAll).reset_index().drop(columns=['level_1'])
    
    return result