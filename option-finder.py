import os 
import pyEX
import pandas as pd
import datetime

# parameters
symbols = ["BABA", "PM", "AAPL", "MO", "MSFT", "AMZN", "OMC", "GOOG"]
min_days = 20
max_days = 90 

monthly_profit_perc = 1 # expected monthly profit %, 1 means 1%
strike_price_perc = 8 # this is the price % where above we are ready to sell/buy in case of CALL/PUT 

today = datetime.date.today()
c = pyEX.Client()

# for each symbol 
for sym in symbols:
    stock_price = c.price(sym)

    cached_options = pd.DataFrame()
    exps = c.optionExpirations(sym)

    # for each expiration 
    for exp in exps:
        expd = datetime.datetime.strptime(exp, '%Y%m%d').date()
        diff = (expd - today).days

        # only for expirations that are within our range 
        if diff > min_days and diff < max_days:
            options = c.optionsDF(sym, exp)
        
            if (len(options.columns) == 0):
                continue 

            # calculate days remaining 
            options['days_remaining'] = diff
            # calculate midprice = open + close / 2
            options['mid'] = (options['ask'] + options['bid']) / 2
            # calculate premium per 30 days 
            options['premium_per_30d'] = options['mid'] / options['days_remaining'] * 30
            #calculate monthly premium percentage 
            options['monthly_premium_perc'] = options['premium_per_30d'] / options['strikePrice']
            
            # add stock price 
            options['stock_price'] = stock_price

            cached_options = cached_options.append(options, sort=False)

    # filtering 
    cached_options = cached_options[['symbol', 'side', 'strikePrice', 'stock_price', 'days_remaining', 'mid', 'premium_per_30d', 'monthly_premium_perc', 'expirationDate', 'ask', 'bid', 'subkey']].sort_values(['side', 'strikePrice', 'days_remaining'])
    
    calls = cached_options[cached_options['side'] == 'call']
    puts = cached_options[cached_options['side'] == 'put']  

    # filter out strike price for put
    put_strike_price = stock_price * (1 - (strike_price_perc/100))  
    puts = puts[puts['strikePrice'] < put_strike_price]
    
    # filter out strike price for calls 
    call_strike_price = stock_price * (1 + (strike_price_perc/100))
    calls = calls[calls['strikePrice'] > call_strike_price]      

    # filter out that does not give us enough premium             
    puts = puts[puts['premium_per_30d'] / puts['strikePrice'] > (monthly_profit_perc/100)] # premium_p30 / strike > 0.01                    
    calls = calls[calls['premium_per_30d'] / calls['strikePrice'] > (monthly_profit_perc/100)] # premium_p30 / strike > 0.01                

    if(len(puts) > 0):
        sorted_puts = puts[['symbol', 'side', 'strikePrice', 'stock_price', 'days_remaining', 'mid', 'monthly_premium_perc', 'subkey']].sort_values('mid', ascending=False)
        print(sorted_puts.shape)

        print('Best put contract for ' + sym)
        print(sorted_puts.head(1))

        print('Alternative puts to write:')
        print(sorted_puts.head())

