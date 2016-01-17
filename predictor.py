import numpy as np 
import financialScrape as fs
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
import psotest as pso


dataDict = fs.loadDatas()
gspc = fs.loadIndex('^GSPC')

global tickers
global ratios 
global year 
global validSyms
global rd
global applyLimits
global rdict, vdict
global term
applyLimits = False

#todo: add optimization for lower limits
#learn the screens!
#todo: test for returns over longer period of time
#test one solution fits all
#test unmodified PE PB PS etc

def rank(syms):
	#print "Screening database for ratios " + str(ratios) + " and year " + str(year)
	#print "Valid stock list is of length " + str(len(syms))
	rankingD = {}
	for ratio in ratios:
		print "ranking stocks for ratio: " + ratio
		valueList = []
		for stock in syms:
			df = dataDict[stock]
			value = float(df[year][ratio])
			if applyLimits:
				if ratio == 'P/B':
					if value < 0.8:
						value = 9999
				if ratio == 'P/E':
					if value < 1.5:
						value = 9999
				if ratio == 'P/S' or ratio == 'P/CF':
					if value < 1.5:
						value = 9999
			valueList.append(value)
		#print "Length value list " + str(len(valueList))
		rankingList = zip(syms, valueList)
		sortedList = sorted(rankingList, key=lambda elem: elem[1])

		#print str(sortedList)
		sortedSyms = list(zip(*sortedList)[0])
		
		if ratio == 'Return on Assets %' or ratio == 'Return on Equity %':
			sortedSyms.reverse()
		if ratio == 'Current Ratio' or ratio == 'Quick Ratio':
			sortedSyms.reverse()
		if ratio == '3Y EPS Growth %':
			sortedSyms.reverse()
		#print str(sortedSyms[:10])

		#print str(sortedList[:10])
		rankingD[ratio] = sortedSyms
		#print str(rankingList)
	return rankingD

def screen(value, ratio):
	pass
	#todo!

def weightRank(weights):
	#rd = rank(validSyms)
	weightedRankList = []
	if len(weights) != len(ratios):
		print "weights and ratio vectors must equal in length"
		return -1

	#print "Calculating weighted ranks for all valid stocks"
	for stock in validSyms:
		rlist = []
		for i in range(len(ratios)):
			rankScore = rd[ratios[i]].index(stock)
			weighted = rankScore * weights[i]
			rlist.append(weighted)
		weightedRankList.append(sum(rlist))

	zipped = zip(validSyms, weightedRankList)
	#print str(zipped[:10])

	sortZip = sorted(zipped, key=lambda elem: elem[1])

	#print str(sortZip[:10])
	sortedSyms = list(zip(*sortZip)[0])
	return sortedSyms

def calculateFitness(weights):

	ssyms = weightRank(weights)
	returns = []
	for stock in ssyms:
		df = dataDict[stock]
		returns.append(float(df[year]['Returns %']))

	portfolioSize = int(len(returns)/10)
	#print "portfolio size:" + str(portfolioSize)
	portfolioReturns = []
	for i in xrange(0, len(returns), portfolioSize):
		portfolioReturns.append(np.mean(returns[i:i+portfolioSize]))

	#print str(portfolioReturns)

	ranks = range(len(portfolioReturns)+1)
	ranks = ranks[1:]
	returns = pd.Series(portfolioReturns)
	ranks = pd.Series(ranks)
	spear = stats.spearmanr(ranks, returns)[0]
	#plt.scatter(ranks, returns)
	#plt.show()
	return spear

def bestAvgSpear(weights):
	global year, rdict, vdict, validSyms, rd
	byear = int(year)
	baseyear = year
	ylist = [str(yr) for yr in range(byear,byear+4)]
	spearlist = []
	for y in ylist:
		validSyms = vdict[y]
		rd = rdict[y]
		year = y
		spearlist.append(calculateFitness(weights))
	year = baseyear
	return np.mean(spearlist)


def famaFrench(weights):
	global year, rdict, vdict, validSyms, rd
	#base year
	byear = int(year)
	#list of years over which we take the average returns of
	ylist = [str(yr) for yr in range(byear,byear+3)]
	prlistdict = {}
	#base year in string
	baseYear = year
	#for each year in ylist
	for y in ylist:
		#rank valid stocks according to weights
		validSyms = vdict[y]
		rd = rdict[y]
		ssyms = weightRank(weights)
		returns = []
		#calculate y+1 average monthly returns for each stock
		for stock in ssyms:
			df = dataDict[stock]
			returns.append(float(df[y]['Returns %']))

		#determine portfolio size
		portfolioSize = int(len(returns)/10)
		pReturns = []
		#chop ranked list into portfolios, determine average monthly portfolio returns
		for i in xrange(0, len(returns), portfolioSize):
			pReturns.append(np.mean(returns[i:i+portfolioSize]))

		yearAverage = np.mean(pReturns)
		dev = np.std(pReturns)
		diffpRet = []
		for ret in pReturns:
			diffpRet.append((ret-yearAverage)/dev)

		#remember portfolio returns for this year
		prlistdict[y] = diffpRet
	avgPortReturns = []
	#average returns over the total number of years
	for x in range(len(prlistdict[baseYear])):
		temp = []
		for y in ylist:
			try:
				temp.append(prlistdict[y][x])
			except:
				pass
		avgPortReturns.append(np.mean(temp))
	
	ranks = range(len(avgPortReturns)+1)
	ranks = ranks[1:]
	avgPortReturns = pd.Series(avgPortReturns)
	ranks = pd.Series(ranks)
	spear = stats.spearmanr(ranks, avgPortReturns)[0]
	
	#print spear
	#plt.scatter(ranks, avgPortReturns)
	#marketAverage = mktAvg(byear)
	#plt.plot(ranks, [marketAverage]*len(ranks), 'r')
	#plt.show()
	return spear

def famaPlot(weights):
	global year, rdict, vdict, validSyms, rd
	byear = int(year)
	ylist = [str(yr) for yr in range(byear,byear+3)]
	#print ylist
	prlistdict = {}
	baseYear = year
	for y in ylist:
		validSyms = vdict[y]
		rd = rdict[y]
		ssyms = weightRank(weights)
		returns = []
		for stock in ssyms:
			df = dataDict[stock]
			returns.append(float(df[y]['Returns %']))

		portfolioSize = int(len(returns)/10)
		pReturns = []
		for i in xrange(0, len(returns), portfolioSize):
			pReturns.append(np.mean(returns[i:i+portfolioSize]))

		yearAverage = np.mean(pReturns)
		dev = np.std(pReturns)
		diffpRet = []
		for ret in pReturns:
			diffpRet.append((ret-yearAverage)/dev)

		#remember portfolio returns for this year
		prlistdict[y] = diffpRet
	avgPortReturns = []
	for x in range(len(prlistdict[baseYear])):
		temp = []
		for y in ylist:
			try:
				temp.append(prlistdict[y][x])
			except:
				pass
		avgPortReturns.append(np.mean(temp))
	ranks = range(len(avgPortReturns)+1)
	ranks = ranks[1:]
	avgPortReturns = pd.Series(avgPortReturns)
	ranks = pd.Series(ranks)
	spear = stats.spearmanr(ranks, avgPortReturns)[0]
	plt.clf()
	plt.scatter(ranks, avgPortReturns)
	marketAverage = mktAvg(byear)
	#plt.plot(ranks, [marketAverage]*len(ranks), 'r')
	plt.ylabel("Average of Average Year t+1 Monthly Returns %")
	plt.xlabel("Weighted Rank Scores")
	plt.title(str(byear) + " to " + str(byear+2) + " Spearman: " + str(spear) + " P-size: " + str(portfolioSize))
	plt.savefig('results/' + 'fama' + str(byear) + '_' + str(byear+2) + '.png')
	

def mktAvg(y):
	avg = []
	for yr in [str(yy) for yy in range(y,y+5)]:
		avg.append(gspc[yr]['Returns %'])
	return np.mean(avg)


def plotFitness(weights):

	ssyms = weightRank(weights)
	returns = []
	for stock in ssyms:
		df = dataDict[stock]
		returns.append(float(df[year]['Returns %']))

	portfolioSize = int(len(returns)/10)
	print "portfolio size:" + str(portfolioSize)
	portfolioReturns = []
	for i in xrange(0, len(returns), portfolioSize):
		portfolioReturns.append(np.mean(returns[i:i+portfolioSize]))

	#print str(portfolioReturns)

	ranks = range(len(portfolioReturns)+1)
	ranks = ranks[1:]
	returns = pd.Series(portfolioReturns)
	ranks = pd.Series(ranks)
	spear = stats.spearmanr(ranks, returns)[0]
	plt.clf()
	plt.scatter(ranks, returns)
	marketAverage = gspc[year]['Returns %']
	plt.plot(ranks, [marketAverage]*len(ranks), 'r')
	plt.ylabel("Average Year t+1 Monthly Returns %")
	plt.xlabel("Weighted Rank Scores")
	plt.title(str(year) + " Spearman: " + str(spear) + " P-size: " + str(portfolioSize))
	plt.savefig('results/famaInterYear' + year + '.png')
	return ssyms[0:portfolioSize]

def zoomplt():
	ssyms = weightRank([1,1])
	portfolioSize = int(len(ssyms)/30)
	print "Zoom to portfolio size/6:" + str(portfolioSize)	
	return ssyms[0:portfolioSize*6]


def check(tickers, ratios, year):
	sym = list(tickers)
	print "checking for year " + year
	print "removing benchmark gspc"
	removed = []
	for ratio in ratios + ['Returns %']:
		if ratio == 'Dividends USD' or ratio == 'Payout Ratio %':
			continue
		for stock in tickers:
			if stock in removed:
				continue
			df = dataDict[stock]
			if df[year][ratio] == '-':

				sym.remove(stock)
				removed.append(stock)
				continue
			if df[year][ratio] <= 0:
				if ratio == 'P/E' or ratio == 'P/B':
					sym.remove(stock)
					removed.append(stock)
					continue
				if ratio == 'P/S' or ratio == 'P/CF':
					sym.remove(stock)
					removed.append(stock)
					continue


	print "removed stocks " + str(len(removed))
	#print str(removed)

	return sym

def precalculate(years, zoom, fscore):
	global ratios, tickers, year, validSyms, rd
	original = list(ratios)
	rdict = {}
	vdict = {}
	for yr in years:
		year = yr
		if zoom:
			if year == '2006' and fscore:
				continue
			ratios = ['P/B', 'Mkt Cap']
			validSyms = check(tickers, ratios, yr)
			rd = rank(validSyms)
			t = zoomplt()
			print "zoomed in to " + str(len(t)) + "stocks."
			ratios = list(original)
			v = check(t, ratios, yr)
			r = rank(v)
		else:
			v = check(tickers, ratios, yr)
			r = rank(v)
		rdict[yr] = r
		vdict[yr] = v
	return rdict, vdict

def learn(y):
	
	print "the year is now " + year
	logname = 'results/weights.txt'
	f = open(logname, 'a')
	pso.dmn = len(ratios)
	
	ans, i, opt = pso.particleSwarmOptimize(calculateFitness, True, True)
		
	yearstring = str(year)
	report =  "Weights: " + str(ans) + ", Spearman: " + str(opt)
	ps = plotFitness(ans)
	f.write("\n")
	f.write(yearstring + ", Portfolio Size: " + str(ps) + ", 30 Portfolios")
	f.write("\n")
	f.write(report)

	f.close()

def famaLearn():
	print "the year is now " + year
	logname = 'results/newfamaWeights.txt'
	f = open(logname, 'a')
	pso.dmn = len(ratios)

	ans, i, opt = pso.particleSwarmOptimize(famaFrench, True, True)

	yearString = str(year)
	report = "Weights: " + str(ans) + ", Spearman: " + str(opt)
	famaPlot(ans)
	f.write("\n")
	f.write(str(year) + " to " + str(int(year) + 4))
	f.write("\n")
	f.write(report)
	f.close()
	return ans

def spearLearn():
	global year
	print "the year is now " + year
	logname = 'results/avgSpearWeights.txt'
	f = open(logname, 'a')
	pso.dmn = len(ratios)

	ans, i, opt = pso.particleSwarmOptimize(bestAvgSpear, True, True)

	yearString = str(year)
	report = "Weights: " + str(ans) + ", Spearman: " + str(opt)
	

	f.write("\n")
	f.write(str(year) + " to " + str(int(year) + 3))
	f.write("\n")
	f.write(report)
	f.close()
	return ans



def test(years):
	global validSyms, rd, year, rdict, vdict
	for yr in years:
		validSyms = vdict[yr]
		rd = rdict[yr]
		year = yr
		learn(year)

def plot(years, weights, zoom, fscore):
	global year, validSyms, rd, ratios
	original = list(ratios)
	for y in years:
		year = y
		if zoom:
			if year == '2006' and fscore:
				continue
			ratios = ['P/B', 'Mkt Cap']
			validSyms = check(tickers, ['P/B', 'Mkt Cap'], y)
			rd = rank(validSyms)
			t = zoomplt()
			print "zoomed in to " + str(len(t)) + "stocks."
			ratios = list(original)
			validSyms = check(t, ratios, y)
			rd = rank(validSyms)
		else:
			validSyms = check(tickers, ratios, year)
			rd = rank(validSyms)
		logname = 'results/syms.txt'
		f = open(logname, 'a')
		symlist = plotFitness(weights)
		quantopianhack = []
		for s in symlist:
			hack = "symbol('" + s + "')"
			quantopianhack.append(hack)
		quantopianhack = '[%s]' % ', '.join(map(str, quantopianhack))
		report = 'context.sd[' + year + '] = ' + str(quantopianhack) + '\n\n'
		f.write(report)
		f.close()


tickers = fs.symbols
#tickers.remove('^GSPC')
ratios = ['P/B', 'Mkt Cap', 'Return on Assets %', 'CFO/Assets', 'Current Ratio', 'Accrual', 'P/CF', 'Operating Cash Flow Growth % YOY']
#ratios = ['P/B', 'Mkt Cap']
year = '2006'
validSyms = check(tickers, ratios, year)
rd = rank(validSyms)
years = [str(y) for y in range(2006,2015)]
rdict, vdict = precalculate(years, True, False)
year = '2007'

ans = spearLearn()


plot(years, ans, True, False)

'''
for y in ['2006','2007','2008','2009','2010','2011']:
	year = y
	ans = spearLearn()
	forecastYear = str(int(y) + 3)
	plot([forecastYear], ans, True, False) 

'''
'''
for y in ['2006','2007']:
	
	iteration = 0

	while iteration < 5:
		year = y
		spearLearn()
		iteration += 1


if applyLimits:
	print "LIMITS ARE BEING APPLIED"
'''
