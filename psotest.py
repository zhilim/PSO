from __future__ import division
import random
import sys
import numpy as np
import math


dmn = 2
searchRange = 10
c1 = c2 = 2.05
ki = 0.7298
w = 0.8
population = 30
maxIterations = 400000
acceptableThreshold = 0
deviation = 0.000001
maxTestIterations = 30
auto = False
constricted = False

if sys.argv[1] == "automate":
	auto = True


print sys.argv

def rosenBrock(candidate):
	summ = 0
	#rosenBrock needs at least 2 variables
	if(len(candidate) < 2):
		print "Error: RosenBrock candidate < 2 dimensions"
		return -1
	#summation i = 1 to N - 1
	for i in range(len(candidate[1:])):
		#rosenBrock's formula
		y = i + 1
		summ += (100*(candidate[y] - candidate[i]**2)**2 + (candidate[i] - 1)**2)

	return summ

def rastrigin(candidate):
	summ = 0
	for x in candidate:
		summ += 10 + (x**2 - 10*math.cos(2*math.pi*x))
	return summ

def sphere(candidate):
	summ = 0
	for x in candidate:
		summ += x**2
	return summ

def ackley(candidate):
	squared = [x**2 for x in candidate]
	p1 = -20 * math.exp(-0.2 * ((sum(squared)/len(squared))**0.5))

	cosined = [math.cos(2*math.pi*x) for x in candidate]
	p2 = math.exp(sum(cosined)/len(cosined))

	f = p1 - p2 + 20 + math.exp(1)

	return f


class Drone:
	v = []
	pos = []
	pB = []
	lB = []
	leftNeighbor = 0
	rightNeighbor = 0
	
	def __init__(self):
		#have to reset lists otherwise the variables accumulate
		self.pos = []
		self.v = []
		self.pB = []
		self.lB = []

		for i in range(dmn):
			self.pos.append(random.uniform(-searchRange, searchRange))
			self.v.append(random.uniform(-1,1))
			self.pB.append(self.pos[i])
				
	def updateV(self, Best):
		for i in range(dmn):
			r1 = random.random()
			r2 = random.random()
			social = c1 * r1 * (Best[i] - self.pos[i])
			cognitive = c2 * r2 * (self.pB[i] - self.pos[i])
			if constricted:
				#print "constricted"
				self.v[i] = ki * (self.v[i] + social + cognitive)
			elif not constricted:
				#print "not constricted"
				self.v[i] = w * self.v[i] + social + cognitive
		
	def updatePos(self):
		self.pos = [x + y for x,y in zip(self.pos, self.v)]

	def reinitialize(self):
		self.pos = []
		self.v = []

		for i in range(dmn):
			self.pos.append(random.uniform(-searchRange, searchRange))
			self.v.append(random.uniform(-1,1))

	def printPos(self):
		return " pos: " + str(self.pos) + "\nvelo: " + str(self.v) + "\n\n\n"

def particleSwarmOptimize(fitnessFunction, ringTop, reIn):

	global w
	swarm = []
	solution = []
	pbResults = []
	optimum = 99

	for h in range(population):
		#create drone and remember its neighbours
		dr = Drone()
		if h == 0:
			dr.leftNeighbor = population - 1
			dr.rightNeighbor = h + 1
		if h == population - 1:
			dr.leftNeighbor = h - 1
			dr.rightNeighbor = 0
		elif h > 0 and h < (population - 1):
			dr.leftNeighbor = h - 1
			dr.rightNeighbor = h + 1

		swarm.append(dr)


	#initialize the personal best results list, this is done here to reduce number of fitness tests we have to do
	for drone in swarm:
		pbResults.append(fitnessFunction(drone.pB))


	#for each iteration
	for i in range(maxIterations):
		#logging
		sys.stdout.write("Iteration: %d    \r" % (i+1))
		sys.stdout.flush()
		
		#get global minimum result from pb results list
		optimum = min(pbResults)

		#get the actual vector of answers
		solution = swarm[pbResults.index(optimum)].pB

		#randomize position of the global best particle to escape potential trap
		if reIn:
			swarm[pbResults.index(optimum)].reinitialize()

		#acceptable conditions to end PSO
		if (optimum < (acceptableThreshold + deviation)) & (optimum > (acceptableThreshold - deviation)):
			break

		#for each drone index
		if ringTop:
			for k in range(population):
			
				#update and remember the local best
				lbResult = pbResults[k]
				lBest = swarm[k].pB
				if lbResult > pbResults[swarm[k].leftNeighbor]:
					lbResult = pbResults[swarm[k].leftNeighbor]
					lBest = swarm[swarm[k].leftNeighbor].pB
				if lbResult > pbResults[swarm[k].rightNeighbor]:
					lBest = swarm[swarm[k].rightNeighbor].pB
				swarm[k].lB = lBest

		#for each drone index
		for d in range(population):
			#update velocity
			if ringTop:
				swarm[d].updateV(swarm[d].lB)
			elif not ringTop:
				#print "not ringTop"
				swarm[d].updateV(solution)
			
			
			#update position
			swarm[d].updatePos()

			#update pbest
			fitnessResult = fitnessFunction(swarm[d].pos)
			if fitnessResult < pbResults[d]:
				pbResults[d] = fitnessResult
				swarm[d].pB = swarm[d].pos

		if not constricted:
			step = 0.4/(maxIterations-1)
			w = w - step
			#print "w decreased to: " + str(w)

	print "Total Iterations: " + str(i+1) 
	return solution, i, optimum

def strengthTest(fitnessFunction, testI, ringTop, reIn, constrict):

	global maxIterations
	global dmn
	global population
	global acceptableThreshold
	global deviation
	global constricted
	global w
	intractible = False
	testNumber = 0
	
	logname = fitnessFunction + str(ringTop) + str(reIn) + str(constrict) + ".txt"
	f = open(logname, 'a')
	conclusion = ""
	dmn = 10

	dispatch={
		'rastrigin': rastrigin,
		'rosenBrock': rosenBrock,
		'sphere' : sphere,
		'ackley' : ackley,
		'True' : True,
		'False' : False
	}

	constricted = dispatch[constrict]

	while not intractible:
		testNumber += 1
		headerStr = "Strength Test " + str(testNumber) + " for " + str(dmn) + " dimensions.\n"
		topoStr = "Ring Topology: " + ringTop + "\n"
		reinStr = "Reinitialization: " + reIn + "\n"
		conStr = "Constricted: " + constrict + "\n"
		funcStr = "Fitness Function: " + fitnessFunction + "\n"
		iterations = []
		failCases = []
		optimums = []
		fails = 0
		
		
		for test in range(testI):
			print "w end: " + str(w)
			w = 0.8
			print "w start: " + str(w)
			print "Round: " + str(test+1)
			answer, i, opt = particleSwarmOptimize(dispatch[fitnessFunction], dispatch[ringTop], dispatch[reIn])
			diff = opt - acceptableThreshold
			optimums.append(opt)
			if diff > deviation or diff < -deviation:
				fails += 1
				failCases.append(opt)
			else:
				iterations.append(i)
			print "Optimal Solution: " + str(answer) 
			print "Global Optimum: " + str(opt) + "\n"
		repHeader =  "Test Report for Dimensions:" + str(dmn) + ", MaxIterations:" + str(maxIterations) + " Swarm Population:" + str(population) + "\n"
		avgStr =  "Average Iterations for successful cases: " + str(np.mean(iterations)) + "\n"
		avgOpt = np.mean(optimums)
		avgOptStr = "Average Global Minimums: " + str(avgOpt) + "\n"
		failStr =  str(len(failCases)) + " cases trapped at: " + str(failCases) + "\n"
		failRate = (fails/testI)*100
		failRStr = "Fail Rate: " + str(failRate) + "%\n"
		if dmn > 30:
			intractible = True
			conclusion = "max dimensions reached.\n\n"
		else:
			conclusion = "Optimization concluded successfully, increasing dimensions for greater challenge.\n\n"
			dmn += 5
		report = headerStr + topoStr + reinStr + conStr + funcStr + repHeader + avgStr + avgOptStr + failStr + failRStr + conclusion
		print report
		f.write(report)
		
	f.write("\nTest Segment Complete\n")
	f.close()

def permutate(fit):
	
	fitFunction = fit
	'''
	ringTopology = "False"
	reInitialization = "False"
	constricted = "False"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)
	'''

	ringTopology = "False"
	reInitialization = "True"
	constricted = "False"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)


	ringTopology = "True"
	reInitialization = "True"
	constricted = "False"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)

	'''
	ringTopology = "True"
	reInitialization = "False"
	constricted = "False"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)

	ringTopology = "False"
	reInitialization = "False"
	constricted = "True"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)


	ringTopology = "False"
	reInitialization = "True"
	constricted = "True"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)


	ringTopology = "True"
	reInitialization = "True"
	constricted = "True"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)


	ringTopology = "True"
	reInitialization = "False"
	constricted = "True"

	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)
	'''





print "pso test v1.0\n"

if not auto:
	fitFunction = sys.argv[1]
	ringTopology = sys.argv[2]
	reInitialization = sys.argv[3]
	constricted = sys.argv[4]
	strengthTest(fitFunction, maxTestIterations, ringTopology, reInitialization, constricted)
elif auto:
	permutate("rastrigin")
	permutate("rosenBrock")
	#permutate("sphere")
	#permutate("ackley")
