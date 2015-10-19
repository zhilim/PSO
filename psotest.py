from __future__ import division
import random
import sys
import numpy as np
import math


dmn = 2
searchRange = 5.12
c1 = c2 = 2.05
w = 0.7298
population = 30
maxIterations = 30000
acceptableThreshold = 0
deviation = 0.000001
maxTestIterations = 100


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

class Drone:
	v = []
	pos = []
	pB = []
	lB = []
	
	def __init__(self):
		#have to reset lists otherwise the variables accumulate
		self.pos = []
		self.v = []
		self.pB = []

		for i in range(dmn):
			self.pos.append(random.uniform(-searchRange, searchRange))
			self.v.append(random.uniform(-1,1))
			self.pB.append(self.pos[i])
				
	def updateV(self, localBest):
		for i in range(dmn):
			r1 = random.random()
			r2 = random.random()
			social = c1 * r1 * (localBest[i] - self.pos[i])
			cognitive = c2 * r2 * (self.pB[i] - self.pos[i])
			self.v[i] = w * (self.v[i] + social + cognitive)

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

def particleSwarmOptimize(fitnessFunction, ringTop):
	swarm = []
	solution = []
	pbResults = []
	optimum = 99

	for h in range(population):
		swarm.append(Drone())
		#print "drone " + str(h) + " OK"
	#print "Swarm Generated"

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
		if not ringTop:
			swarm[pbResults.index(optimum)].reinitialize()

		#acceptable conditions to end PSO
		if (optimum < (acceptableThreshold + deviation)) & (optimum > (acceptableThreshold - deviation)):
			break

		#for each drone index
		for k in range(population):
			#get the neighbor indexes
			leftNeighbor = 0
			rightNeighbor = 0
			if k == 0:
				leftNeighbor = population - 1
				rightNeighbor = k + 1
			if k == population - 1:
				leftNeighbor = k - 1
				rightNeighbor = 0
			else:
				leftNeighbor = k - 1
				rightNeighbor = k + 1

			#update local best
			lbResult = pbResults[k]
			lBest = swarm[k].pB
			if lbResult > pbResults[leftNeighbor]:
				lbResult = pbResults[leftNeighbor]
				lBest = swarm[leftNeighbor].pB
			if lbResult > pbResults[rightNeighbor]:
				lBest = swarm[rightNeighbor].pB

			#update velocity
			if ringTop:
				swarm[k].updateV(lBest)
			elif not ringTop:
				swarm[k].updateV(solution)
			swarm[k].updatePos()

			#update pbest
			fitnessResult = fitnessFunction(swarm[k].pos)
			if fitnessResult < pbResults[k]:
				pbResults[k] = fitnessResult
				swarm[k].pB = swarm[k].pos

	print "Total Iterations: " + str(i+1) 
	return solution, i, optimum

def strengthTest(fitnessFunction, testI, ringTop):

	global maxIterations
	global dmn
	global population
	global acceptableThreshold
	global deviation
	intractible = False
	testNumber = 0
	f = open('psolog.txt', 'a')
	funcStr = ""
	conclusion = ""
	dmn = 2

	while not intractible:
		testNumber += 1
		headerStr = "Strength Test " + str(testNumber) + " for " + str(dmn) + " dimensions at 30 percent passing mark.\n"
		topoStr = "Ring Topology: " + str(ringTop) + "\n"
		if fitnessFunction == rosenBrock:
			funcStr = "Fitness Function: RosenBrock\n"
		elif fitnessFunction == rastrigin:
			funcStr = "Fitness Function: Rastrigin\n"
		iterations = []
		failCases = []
		fails = 0
		for test in range(testI):
			print "Round: " + str(test+1)
			answer, i, opt = particleSwarmOptimize(fitnessFunction, ringTop)
			diff = opt - acceptableThreshold
			if diff > deviation or diff < -deviation:
				fails += 1
				failCases.append(opt)
			else:
				iterations.append(i)
			#print "Optimal Solution: " + str(answer) 
			#print "Global Optimum: " + str(opt) + "\n"
		repHeader =  "Test Report for Dimensions:" + str(dmn) + ", MaxIterations:" + str(maxIterations) + " Swarm Population:" + str(population) + "\n"
		avgStr =  "Average Iterations for successful cases: " + str(np.mean(iterations)) + "\n"
		failStr =  str(len(failCases)) + " cases trapped at: " + str(failCases) + "\n"
		failRate = (fails/testI)*100
		failRStr = "Fail Rate: " + str(failRate) + "%\n"
		if failRate > 30:
			intractible = True
			conclusion = "Fail rate too high, dimension may be intractible.\n\n"
		else:
			conclusion = "Optimization concluded successfully, increasing dimensions for greater challenge.\n\n"
			dmn += 1
		report = headerStr + topoStr + funcStr + repHeader + avgStr + failStr + failRStr + conclusion
		print report
		f.write(report)
	f.write("\nTest Segment Complete\n")
	f.close()





print "pso test v1.0\n"

strengthTest(rastrigin, maxTestIterations, False)

strengthTest(rosenBrock, maxTestIterations, False)


