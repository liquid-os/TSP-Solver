import sys
import math
import time
import builtins
import sqlite3

cityList = []
testPaths = []

dimension = 0
maxTime = 10000
startTime = time.time()
showDebugOutput = sqlite3.connect("TSPSolver.db")
name = ""
database = None

class City(object):
    posX = 0;
    posY = 0;
    cityID = 0;

    def __init__(self, id=0, x=0, y=0):
        self.cityID = id
        self.posX = x
        self.posY = y

class TestPath(object):
    cityList = []
    totalDistance = 0

    def getDistance(self, city1: City, city2: City):
        if city1 is None or city2 is None:
            return -1
        distA = getAbsoluteValue(city1.posX - city2.posX)
        distB = getAbsoluteValue(city1.posY - city2.posY)
        distC = math.sqrt((distA ** 2) + (distB ** 2))
        return distC

    def getTotalDistance(self):
        return self.totalDistance + self.getDistance(self.cityList[0], self.cityList[len(self.cityList)-1])

    def addCity(self, city : City):
        if(city not in self.cityList):
            self.cityList.append(city)
            if(len(self.cityList) > 1):
                prev = self.cityList[len(self.cityList)-2]
                dist = self.getDistance(city, prev)
                self.totalDistance += dist

    def writeToConsole(self):
        index = 0
        for city in self.cityList:
            index = index + 1
            print("City ",index,": ",city.cityID)
        print("-1")

    def __init__(self, path=[], len=0):
        self.cityList = path
        self.totalDistance = len

def queryDB(database, qry):
    #cursor = database.cursor()
    s = (qry)
    database.execute(qry)
    database.commit()

def main():
    cityList = []
    database = sqlite3.connect("tspsolver.db")
    setupQuery = open("setup.sql", "r", 1).read()
    #print(setupQuery)
    maxTime = 10000
    for line in open('setup.sql', 'r'):
        database.execute(line)
    startTime = time.time()
    path = None
    dimension = 0
    name = ""
    mode = -1 #1 = ADD, 2 = SOLVE, 3 = FETCH SOLUTION
    enableSolver = True
    if enableSolver == True:
        fileName = "C:/Users/Dean Shannon/a280.TSP"
        if len(sys.argv) >= 4:
            if sys.argv[1] == "ADD":
                mode = 1
            if sys.argv[1] == "SOLVE":
                mode = 2
            if sys.argv[1] == "FETCH":
                mode = 3
            print(toString(mode))
            fileName = sys.argv[2]
            maxTime = int(sys.argv[3])

        file = open(fileName, "r", 1)
        string = file.read()
        list = string.split("\n", -1)
        nodeStart = 1
        name = fileName.split("/")[-1].split(".")[0]
        if mode == 1:
            for string in list:
                if(string.isupper()):
                    ++nodeStart
                    if string != "NODE_COORD_SECTION" and string != "EOF":
                        dat_raw = string.split(":")
                        dat = dat_raw[1].strip(' ')
                        identifier = dat_raw[0].strip(' ')
                        if identifier == "NAME":
                            name = dat
                        if identifier == "DIMENSION":
                            dimension = int(dat)
                        if identifier == "EDGE_WEIGHT_TYPE":
                            if dat == "EUC_2D":
                                print("TSP Structure accepted.")
                            else:
                                print("Cannot resolve for this TSP structure.")
                                sys.exit(1)
                else:
                    str = string
                    cityDataValues = [0.0, 0.0, 0.0]
                    localIndex = 0
                    subList = str.split(" ", -1)
                    for str1 in subList:
                        localdat = 0
                        if str1.isnumeric():
                            localdat = toNumber(eval(str1))
                        if localdat > 0:
                            cityDataValues[localIndex] = localdat
                            localIndex = localIndex + 1
                    if(cityDataValues[0] > 0):
                        localCity = City(cityDataValues[0], cityDataValues[1], cityDataValues[2])
                        cityList.append(localCity)
            file.close()
            print("Storing problem '"+name+"' in database...")
            localID = storeProblem(database, name, cityList)
            if localID > -1:
                print("Problem stored successfully at ID "+toString(localID))

        if mode == 2:
            cityList = fetchProblem(database, name)

            for city in cityList:
                if showDebugOutput:
                    print("Creating new test path.")
                prototypePath = TestPath()
                prototypePath.addCity(cityList[0])
                prototypePath.addCity(city)
                localList = []
                for c in cityList:
                    if c != city and c != cityList[0]:
                        if c not in localList:
                            localList.append(c)
                if getNearestCity(city, localList, prototypePath) == False:
                    if showDebugOutput:
                        print("Recursion terminated.")
                testPaths.append(prototypePath)
                elapsed = (time.time()-startTime)
                if(elapsed >= maxTime):
                    print("Time limit reached, terminating application.\n[",elapsed," seconds elapsed]\n[",(elapsed-maxTime)," seconds beyond limit]")
                    sys.exit(1)
                if showDebugOutput:
                    print("Path #",len(testPaths)," created (",elapsed," seconds)")

            path = getShortestPath()
            storeSolution(database, path)
            print(">> TSP COMPLETE IN ",(time.time()-startTime)," SECONDS <<")
            print("TSP: ",name," (",fileName,")")
            print("Shortest Tour Length Found: ",path.getTotalDistance())
            print("Tour Order:")
            path.writeToConsole()

        if mode == 3:
            path = fetchSolution(database, name)
            print("TSP: ", name, " (", fileName, ")")
            print("Shortest Tour Length Found: ", path.getTotalDistance())
            print("Tour Order:")
            path.writeToConsole()


def toNumber(string):
    try:
        return int(string)
    except ValueError:
        return float(string)

def getSingleQueryReturn(cursor):
    for row in cursor:
        if row[0] is not None:
            return row[0]
    return -1

def toString(val):
    return str(val)

def fetchSolution(database, name):
    id = 0
    cursor = database.execute("SELECT id FROM problems WHERE name = '"+name+"'")
    id = getSingleQueryReturn(cursor)
    cursor = database.execute("SELECT * FROM solutions WHERE problemID = "+str(id))
    path = TestPath()
    for row in cursor:
        path.cityList[toNumber(row[2])] = toNumber(row[1])
    return path

def storeProblem(database, name, list):
    id = 0
    cursor = database.execute("SELECT id FROM problems WHERE name = '" + name + "'")
    exists = getSingleQueryReturn(cursor)
    if exists == -1:
        cursor = database.execute("SELECT COUNT(*) FROM problems")
        id = getSingleQueryReturn(cursor)
        database.execute("INSERT INTO problems VALUES ("+str(id)+",'"+name+"')")
        for city in list:
            database.execute("INSERT INTO nodes VALUES ("+str(id)+","+str(city.cityID)+","+str(city.posX)+","+str(city.posY)+")")
        database.commit()
        return id
    else:
        print("A problem by that name already exists.")
        return -1


def fetchProblem(database, name):
    returnList = []
    id = 0
    cursor = database.execute("SELECT id FROM problems WHERE name = '" + name + "'")
    id = getSingleQueryReturn(cursor)
    cursor = database.execute("SELECT nodeID, x, y FROM nodes WHERE problemID = "+str(id))
    for row in cursor:
        localCity = City()
        localCity.cityID = toNumber(row[0])
        localCity.posX = toNumber(row[1])
        localCity.posY = toNumber(row[2])
        returnList.append(localCity)
    return returnList


def storeSolution(database, path):
    id = 0
    cursor = database.execute("SELECT id FROM problems WHERE name = '"+name+"'")
    id = getSingleQueryReturn(cursor)
    print(id)
    #database.execute("INSERT INTO problems VALUES ("+str(id)+",'"+name+"')")
    index = 0
    for city in path.cityList:
        database.execute("INSERT INTO solutions VALUES ("+str(id)+","+str(city.cityID)+","+str(index)+")")
        index = (index + 1)
    database.commit()



def getNearestCity(origin : City, avail=[], path : TestPath = None):
    lastDist = -1
    lastCity = cityList[1]
    if len(avail) <= 1:
        if showDebugOutput:
            print("Terminating recursion.")
        avail = None
        return False
    else:
        for city in avail:
            if lastDist == -1:
                lastCity = city
                lastDist = getDistance(origin, city)
            else:
                localDist = getDistance(origin, city)
                if localDist < lastDist:
                    lastCity = city
                    lastDist = getDistance(origin, city)
        path.addCity(lastCity)
        newlist = list(avail)
        newlist.remove(lastCity)
        return getNearestCity(lastCity, newlist, path)

def getShortestPath(testPaths):
    shortest = None
    for path in testPaths:
        if(shortest == None):
            shortest = path
        else:
            if(path.getTotalDistance() < shortest.getTotalDistance()):
                shortest = path
    return shortest


def getDistance(city1 : City, city2 : City):
    if city1 is None or city2 is None:
        return -1
    distA = getAbsoluteValue(city1.posX - city2.posX)
    distB = getAbsoluteValue(city1.posY - city2.posY)
    distC = math.sqrt((distA**2) + (distB**2))
    return distC

def getAbsoluteValue(num):
    if num >= 0:
        return num
    if num < 0:
        return num*(-1)

main()