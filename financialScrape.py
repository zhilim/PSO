import pandas as pd
import os
from pattern.web import URL
import numpy as np 


symbols = []
#initial ticker list is crude, consisting of funds, etfs, and some foreign stocks
#we clean up later
nyseSbls = list(pd.read_csv("nyse.csv")["Symbol"])
nasSbls = list(pd.read_csv("nasdaq.csv")["Symbol"])
nasSbls.remove('MSG')
amexSbls = list(pd.read_csv("amex.csv")["Symbol"])
mainUrl = "http://financials.morningstar.com/valuation/valuation-history.action?&t="
nyUrl = "XNYS:"
nasUrl = "XNAS:"
amxUrl = "XASE:"
trailUrl = "&region=usa&culture=en-US&cur=&type=price-earnings"


#downloads 10 year valuation ratios from morningstar
#the true scraper this
#depreciated, one time use only unless specially required.
def getValuation(marketUrl, marketSbls):

	vDict = {}
	count = 0
	for ticker in marketSbls:
		print "pulling stock: ", ticker
		#put the url for valuation history together
		tickerUrl = mainUrl + marketUrl + ticker + trailUrl
		rawDf = None
		try:
			#turn html into dataframe
			rawDf = pd.io.html.read_html(tickerUrl, tupleize_cols = True, header=0)
		except:
			print "Could not read valuation for: " + ticker + ", this might not be a company."
			count+=1

			continue

		#take the rows we need
		df = rawDf[0].iloc[[0,3,6,9]]

		#Rename columns
		original = ['Price/Earnings'] + ['Unnamed: ' + str(n) for n in range(1,12)]
		crispy = ['Valuation Ratio'] + [str(year) for year in range(2006,2015)] + ['TTM']

		redict = {}
		for o, c in zip(original, crispy):
			redict[o] = c

		df = df.rename(columns=redict)

		#rename indices
		for i, v in zip([0,3,6,9], ['P/E','P/B','P/S','P/CF']):
			df['Valuation Ratio'][i] = v

		df = df.set_index('Valuation Ratio')
		#change blank to -
		df = df.replace(u'\u2014','-')
		print "Saving to Database: " + ticker
		#put in folder as csv
		df.to_csv("data/" + ticker + ".csv", mode = 'w', encoding = 'utf-8')
		count += 1
		print "Progress: " + str(count) + "/" + str(len(marketSbls))

#downloads a csv of key ratios from morningstar for each stock
#extracts the ratios we desire, combine with valuation ratios previously, then chuck in database
#depreciated, do not use.
def getKeyRatios(marketUrl, marketSbls, valDict):
	krUrl = "http://financials.morningstar.com/ajax/exportKR2CSV.html?&callback=?&t="
	endUrl = "&region=usa&culture=en-US&cur=&order=asc"
	temp = "temp/mskr.csv"
	#the ratios we want we define here
	indexes = ['Dividends USD', 'Payout Ratio %', 'Shares Mil', 'Return on Assets %',
	 'Return on Equity %', 'Current Ratio', 'Quick Ratio', 'Debt/Equity']
	columns = [str(year) for year in range(2006,2015)] + ['TTM']	
	failed = []
	count = 1

	for ticker in marketSbls:
		#the df to store the data we extract
		refinedDf = pd.DataFrame(columns=columns, index=indexes)
		#the df to store all the data from the csv downloaded
		df = object()
		tickerUrl = krUrl + marketUrl + ticker + endUrl
		url = URL(tickerUrl)
		f = open(temp, 'wb')
		try:
			#actually download
			f.write(url.download())
		except:
			print "could not download csv: " + ticker
			count+=1
			failed.append(ticker)
			continue
		f.close()
		try:
			#turn csv into dataframe
			df = pd.read_csv(temp, header=2, thousands=",", index_col=0)
		except:
			count+=1
			failed.append(ticker)
			continue
		#change nans to dash
		df = df.fillna('-')
		#rename columns
		df.columns = columns
		#extract rows neededd
		for year in columns:
			refinedDf[year] = df[year][indexes]

		#append to valuation dataframe
		combined = valDict[ticker].append(refinedDf)
		print "saving combined KR and val data to db: " + ticker
		#save combined df to csv, into database
		combined.to_csv("db/" + ticker + ".csv", mode = 'w', encoding = 'utf-8')
		print "Progress: " + str(count) + "/" + str(len(marketSbls))
		count+=1
	return failed

#Adds indices(list) of key ratios to every ticker in the database
#
def updateKeyRatios(indices, tickers, marketUrl):
	krUrl = "http://financials.morningstar.com/ajax/exportKR2CSV.html?&callback=?&t="
	endUrl = "&region=usa&culture=en-US&cur=&order=asc"
	temp = "temp/mskr.csv"
	indexes = indices
	columns = [str(year) for year in range(2006,2016)] + ['TTM']
	slicedCol = [str(year) for year in range(2006,2016)]
	finCol = [str(year) for year in range(2006,2015)] + ['TTM']
	failed = []
	count = 1

	for ticker in tickers:
		filename = ticker + ".csv"
		dbdf = loadData(ticker)
		df = object()
		tickerUrl = krUrl + marketUrl + ticker + endUrl
		url = URL(tickerUrl)
		f = open(temp, 'wb')
		try:
			f.write(url.download())
		except:
			print "could not download csv: " + tickerUrl
			count += 1
			failed.append(ticker)
			continue
		f.close()
		try:
			df = pd.read_csv(temp, header=2, thousands=",", index_col=0)
		except:
			print "error reading temp csv."
			count+=1
			failed.append(ticker)
			continue
		df = df.fillna('-')
		df.columns = columns
		df = df[slicedCol]
		df.columns = finCol
		print "indexes are: " + str(indexes)

		tbremoved = []
		for index in indexes:
			print "checking " + index
			if index in dbdf.index:
				for year in finCol:
					dbdf[year][index] = df[year][index]
				print index + " already exists, adding to remove list"
				tbremoved.append(index)
		print "removal list: " + str(tbremoved)
		for i in tbremoved:
			indexes.remove(i)
		print "indexes now: " + str(indexes)
		combined = dbdf
		if len(indexes) > 0:
			newdf = pd.DataFrame(columns = columns, index=indexes)
			for year in finCol:
				newdf[year] = df[year][indexes]
			combined = dbdf.append(newdf)
		print "Saving new KR to db for: " + ticker
		combined = combined.fillna('-')
		combined.to_csv("db/" + filename, mode='w', encoding='utf-8')
		print "Progress: " + str(count) + "/" + str(len(tickers))
		count += 1
	return failed


def getQuotes(sym):
	frontUrl = "http://real-chart.finance.yahoo.com/table.csv?s="
	endUrl = "&amp;a=10&amp;b=8&amp;c=1997&amp;d=10&amp;e=8&amp;f=2015&amp;g=d&amp;ignore=.csv"
	
	failed = []
	count = 1

	for ticker in sym:
		fname = "quotes/" + ticker + ".csv"
		df = object()
		tickerUrl = frontUrl + ticker + endUrl
		url = URL(tickerUrl)
		f = open(fname, 'wb')
		try:
			f.write(url.download())
		except:
			print "quotes csv download failed: " + ticker
			failed.append(ticker)
			count += 1
			continue
		f.close()
		count+=1
		print "progress: " + str(count) + "/" + str(len(sym))

	return failed

def clean(directory):
	for filename in os.listdir(directory):
		fullname = directory + "/" + filename
		if os.stat(fullname).st_size == 0:
			print "removing empty file found: " + fullname
			os.remove(fullname)

#dangerous, do not use again
def repair(rlist):
	count = 1
	for filename in rlist:
		print "reparing " + filename
		ticker = filename.strip('.csv')
		damaged = loadData(ticker)
		vIndex = ['P/E', 'P/B', 'P/S', 'P/CF', 'Mkt Cap']
		krIndex = ['Dividends USD', 'Payout Ratio %', 'Shares Mil', 'Return on Assets %',
		'Return on Equity %', 'Current Ratio', 'Quick Ratio', 'Debt/Equity', '5Y Beta', 'Mkt Cap']
		vColumns = [str(year) for year in range(2006,2015)] + ['TTM']
		krColumns = [str(year) for year in range(2005,2015)]

		rCol = [str(year) for year in range(2006,2015)] + ['TTM']
		vdf = damaged[vColumns]
		try:
			vdf = vdf.drop(krIndex)
		except:
			print "already done " + ticker
			count += 1
			continue
		kdf = damaged[krColumns]
		kdf = kdf.drop(vIndex)
		vdf.columns = rCol
		kdf.columns = rCol

		finaldf = vdf.append(kdf)
		finaldf = finaldf.fillna('-')
		finaldf.to_csv("db/" + filename, mode = 'w', encoding = 'utf-8')
		print "progress: " + str(count) + "/" + str(len(rlist))
		count+=1

def check(rlist):
	failed = []
	count = 1
	for filename in rlist:
		print "checking " + str(count) + "/" + str(len(rlist))
		ticker = filename.strip('.csv')
		df = loadData(ticker)
		if 'Mkt Cap' in df.index:
			print "still not repaired: " + ticker
			failed.append(ticker)
		count += 1
	return failed



#initial helper function used to load from csv valuation for each stock
def loadValuation():
	vDict = {}
	
	for filename in os.listdir('data'):
		ticker = filename.strip('.csv')
		#symbols.append(ticker)
		vDict[ticker] = pd.DataFrame.from_csv('data/' + filename)
	print str(len(symbols)) + "value datas loaded."
	return vDict

def loadQuotes():
	qDict = {}
	print "Loading all historical Quotes.."
	for filename in os.listdir('quotes'):
		ticker = filename.strip('.csv')
		qDict[ticker] = pd.DataFrame.from_csv('quotes/' + filename)
	print "Quote histories loaded."
	return qDict

def loadQuote(ticker):
	#print "loading quotes for " + ticker
	return pd.DataFrame.from_csv('quotes/' + ticker + '.csv')

def loadData(ticker):
	#print "loading data for " + ticker
	return pd.DataFrame.from_csv('db/' + ticker + '.csv')

def loadDatas():
	dDict = {}
	print "Loading all financial Data.."
	for filename in os.listdir('db'):
		ticker = filename.strip('.csv')
		dDict[ticker] = pd.DataFrame.from_csv('db/' + filename)
	print "Financial datas loaded."
	return dDict

#remove symbols that are not companies or simply incorrect
def updateSymbols(directory):
	global nyseSbls, nasSbls, amexSbls
	syms = []
	for filename in os.listdir(directory):
		ticker = filename.strip('.csv')
		syms.append(ticker)
	print str(len(syms)) + " symbols"
	nyseSbls = list(set(nyseSbls) & set(syms))
	print str(len(nyseSbls)) + " symbols in NYSE"
	nasSbls = list(set(nasSbls) & set(syms))
	print str(len(nasSbls)) + " symbols in NASDAQ"
	amexSbls = list(set(amexSbls) & set(syms))
	print str(len(amexSbls)) + " symbols in AMEX"
	return syms 

def calculateBeta(stockAdjCl, indexAdjCl):
	
	sadj = stockAdjCl
	iadj = indexAdjCl

	if len(sadj) != len(iadj):
		print "adj cl len not equal, mending"
		if len(sadj) > len(iadj):
			sadj = sadj[:len(iadj)]
		if len(sadj) < len(iadj):
			iadj = iadj[:len(sadj)]

	sret = []
	iret = []

	for i in range(len(sadj) - 1):
		sret.append((sadj[i]-sadj[i+1])/sadj[i+1])
		iret.append((iadj[i]-iadj[i+1])/iadj[i+1])

	covmat = np.cov(iret,sret)

	beta = covmat[0,1]/covmat[0,0]

	return beta

def getAllBeta():
	#todo: prevent repeat index if have to update beta in the future
	i = loadQuote('^GSPC')
	count = 1
	col = [str(year) for year in range(2006,2015)] + ['TTM']
	ind = ['5Y Beta']
	for ticker in symbols:
		if ticker == '^GSPC':
			continue
		df = pd.DataFrame(columns = col, index = ind)
		print "progress " + str(count) + "/" + str(len(symbols))
		print "calculating beta for " + ticker
		s = loadQuote(ticker)
		d = loadData(ticker)
		for year in d.columns:
			if year == 'TTM':
				upper = '2016'
				lower = '2010'
			else:
				upper = str(int(year) + 1)
				lower = str(int(upper)-6)
			i5 = i['Adj Close'][upper:lower]
			s5 = s['Adj Close'][upper:lower]

			if len(s5) == 0:
				continue

			im = i5.resample('BM').iloc[::-1]
			sm = s5.resample('BM').iloc[::-1]

			if '5Y Beta' in d.index:
				d[year]['5Y Beta'] = calculateBeta(sm,im)
			else:
				df[year]['5Y Beta'] = calculateBeta(sm,im)
		if '5Y Beta' not in d.index:
			combined = d.append(df)
		else:
			combined = d
		combined = combined.fillna('-')
		combined.to_csv("db/" + ticker + ".csv", mode = 'w', encoding = 'utf-8')
		count += 1

def fillNa(directory):
	for filename in os.listdir(directory):
		print "settling NANs for " + filename
		df = pd.DataFrame.from_csv(directory + '/' + filename)
		df = df.fillna('-')
		df.to_csv(directory + '/' + filename)

def calculateMCap():
	col = [str(year) for year in range(2006,2015)] + ['TTM']
	ind = ['Mkt Cap']
	count = 1
	for ticker in symbols:
		print "mcap for " + ticker
		print "progress: " + str(count) + "/" + str(len(symbols))
		df = pd.DataFrame(columns = col, index = ind)
		if ticker == '^GSPC':
			continue
		print "market cap calculation for " + ticker
		q = loadQuote(ticker)
		d = loadData(ticker)
		for year in d.columns:
			y = year
			if year == 'TTM':
				y = '2015'
			avgClose = np.mean(q['Adj Close'][y])
			outShares = str(d[year]['Shares Mil'])
			if outShares != '-':
				outShares = float(outShares.replace(',', ''))
			mCap = '-'
			if outShares != '-':
				mCap = avgClose * outShares

			if 'Mkt Cap' not in d.index:
				df[year]['Mkt Cap'] = mCap
			else:
				d[year]['Mkt Cap'] = mCap

		combined = d
		if 'Mkt Cap' not in d.index:
			combined = d.append(df)
		combined = combined.fillna('-')
		combined.to_csv("db/" + ticker + ".csv", mode = 'w', encoding = 'utf-8')
		count += 1




		





#todo: calculate beta, market cap, download historical prices, calculate 1 year returns

#clean('quotes')

symbols = updateSymbols('quotes')
#getQuotes(['^GSPC'])
#getAllBeta()
#calculateMCap()
updateKeyRatios(['Current Ratio', 'Quick Ratio', 'Financial Leverage'], ['AAPL'], nasUrl)




