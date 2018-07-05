import sys
import wx
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt
plt.ion()
import mysql.connector as sql
import math
import time

import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar


class Plot(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = Canvas(self, -1, self.figure)
        self.toolbar = Toolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)

database = sql.connect(host='mysql.ict.griffith.edu.au',user='s5101994',password='yYnz4SC3',database='1810ICTdb')
startTime = 0
maxTime = 10000


class City(object):
    posX = 0;
    posY = 0;
    cityID = 0;

    def __init__(self, id=0, x=0, y=0):
        self.cityID = id
        self.posX = x
        self.posY = y
        
class TSP(object):
    cityList = []
    length = 0
    name = ""
    solveTime = 0
    date = None
    author = "" 
    algorithm= "Semi Brute Force"
    def __init__(self, name="Unknown"):
        self.name = name
        
    def getLength(self):
        totalDistance = 0
        index = 0
        for city in self.cityList:
            totalDistance += getDistance(city, self.cityList[index-1])
            index += 1
        return totalDistance
    
def getListAsString(cityList):
    ret = ""
    for city in cityList:
        ret.append(city.cityID + " ")
    ret.append("-1")
    return ret
        
def uploadProblem(database, name, list):
    comment = ""
    cursor = database.cursor()
    cursor.execute("INSERT INTO Problem VALUES ('" + name + "', "+ str(len(list)) +", '"+ comment +"')")
    index = 0
    for city in list:
        cursor.execute("INSERT INTO Cities VALUES ('" + name + "', "+ str(index) +", "+ str(city.posX) +", "+ str(city.posY) + ")")
        index = (index + 1)
    cursor.close()
    database.commit()

def downloadCityList(database, name):
    returnList = []
    cursor = database.cursor()
    cursor.execute("SELECT ID, x, y FROM Cities WHERE Name = '"+name+"'")
    for row in cursor:
        localCity = City()
        localCity.cityID = toNumber(row[0])
        localCity.posX = toNumber(row[1])
        localCity.posY = toNumber(row[2])
        returnList.append(localCity)
    cursor.close()
    return returnList

def getCityListFromTourString(tour, name):
    ret = []
    for s in tour.split(" "):
        cityID = toNumber(s)
        if cityID > -1:
            cursor = database.cursor()
            cursor.execute("SELECT x, y FROM Cities WHERE Name = '"+name+"' AND ID = "+str(cityID))
            city = City()
            data = cursor.fetchall()[0]
            city.cityID = cityID
            city.posX = toNumber(data[0])
            city.posY = toNumber(data[1])
            print(str(cityID)+": ("+str(data[0])+", "+str(data[1])+")")
            ret.append(city)
    database.commit()
    cursor.close()
    return ret

def downloadSolution(database, name, author):
    solution = None
    tour = ""
    cursor = database.cursor()
    cursor.execute("SELECT SolutionID, TourLength, Date, Algorithm, RunningTime, Tour FROM Solution WHERE problemName = '"+name+"' AND Author = '"+author+"'")
    data = cursor.fetchall()[0]
    solution = TSP(name)
    solution.name = name
    solution.length = toNumber(data[1])
    solution.date = data[2]
    solution.algorithm = data[3]
    solution.solveTime = toNumber(data[4])
    tour = data[5]
    database.commit()
    cursor.close()
    solution.cityList = getCityListFromTourString(tour, name)
    return solution


def getSingleQueryReturn(cursor):
    for row in cursor:
        if row[0] is not None:
            return row[0]
    return -1

def plotGraph(xList, yList, name, plotArea):
    plt = plotArea.figure.gca()
    plt.clear()
    plotArea.figure.axes.clear()
    plt.plot(xList, yList)
    plotArea.Layout()
     
def plotTSP(tsp : TSP, plotArea):
    plt = plotArea.figure.gca()
    plt.clear()
    xList = []
    yList = []
    for city in tsp.cityList:
        xList.append(city.posX)
        yList.append(city.posY)
    plt.plot(xList, yList)
    plotArea.Layout()
    

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
    cursor = database.cursor()
    cursor.execute(qry)
    database.commit()
    cursor.close()
    return cursor.fetchall()

def toNumber(string):
    try:
        return int(string)
    except ValueError:
        return float(string)

loadedProblem = TSP()
loadedSolution = TSP()

def getLoadedProblem():
    return loadedProblem

def getLoadedSolution():
    return loadedSolution

def getShortestPath(testPaths):
    shortest = None
    for path in testPaths:
        if(shortest == None):
            shortest = path
        else:
            if(path.getTotalDistance() < shortest.getTotalDistance()):
                shortest = path
    return shortest

def getUploadedProblems(database):
    ret = ""
    cursor = database.cursor()
    cursor.execute("SELECT Name FROM Problem")
    for row in cursor:
        ret = (ret + "* " + row[0] + "\n")
    cursor.close()
    return ret

def getSolutionsFromAuthor(database, author):
    ret = ""
    cursor = database.cursor()
    cursor.execute("SELECT problemName, SolutionID, TourLength FROM Solution WHERE Author = '"+author+"'")
    for row in cursor:
        ret = (ret + "* " + str(row[1]) + " > " + row[0] + " (" + str(row[2]) + ")" + "\n")
    cursor.close()
    return ret

def getNearestCity(origin : City, avail=[], path : TestPath = None, cityList=[]):
    lastDist = -1
    lastCity = cityList[1]
    if len(avail) <= 1:
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
        return getNearestCity(lastCity, newlist, path, cityList)
    
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


class Window(wx.Frame):
    
    plotArea = None
    console = None
    
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self,parent,id,title)
        self.parent = parent
        self.initFrame()
        
    def initFrame(self):
        sizer = wx.FlexGridSizer(0,0,1,1)
        self.SetSizerAndFit(sizer)
        self.Show(True)
        self.SetSize(width=800,height=64 * 7 + 200)
        panel = wx.Panel(self)
        panel.SetSize(width=800,height=64 * 7 + 200)
        panel.SetBackgroundColour("GRAY")
        
        buttonUpload = wx.Button(panel,label="Upload\nProblem",pos=(0,0),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.loadFile, buttonUpload)
        
        buttonLoadProblem = wx.Button(panel,label="Download",pos=(0,64),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.loadProblem, buttonLoadProblem)
        
        buttonSolve = wx.Button(panel,label="Solve",pos=(0,128),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.solveProblem, buttonSolve)
        
        buttonSave = wx.Button(panel,label="Upload\nSolution",pos=(0,192),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.saveSolution, buttonSave)
        
        buttonLoadSolution = wx.Button(panel,label="Download\nSolution",pos=(0,256),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.loadSolution, buttonLoadSolution)
        
        buttonSchema = wx.Button(panel,label="Upload\nDB Schema",pos=(0,320),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.uploadSchema, buttonSchema)
        
        buttonTruncate = wx.Button(panel,label="Truncate\nTable(s)",pos=(0,384),size=(64,64))
        self.Bind(wx.EVT_BUTTON, self.truncateTable, buttonTruncate)
        
        global plotArea
        plotArea = Plot(parent=panel)
        plotArea.SetSize(64,0,700,64 * 7)
        global console
        console = wx.TextCtrl(panel, wx.ID_ANY, size=(800, 200), pos=(0, 64 * 7), style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        sys.out = console
        self.Bind(wx.EVT_CLOSE, self.exitApp)
        
    def truncateTable(self, event):
        dlg = wx.TextEntryDialog(self, 'Enter the name of the table you want to truncate. (Or enter \'*\' for all tables)','Truncate a table...')
        dlg.SetValue("Default")
        name = ""
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
        if name.find("."):
            name = name.split(".")[0]
        dlg.Destroy()
        
        cursor = database.cursor()
        if name == "*":
            cursor.execute("TRUNCATE TABLE Cities")
            cursor.execute("TRUNCATE TABLE Problem")
            cursor.execute("TRUNCATE TABLE Solution")
        else:
            cursor.execute("TRUNCATE TABLE "+name)
        cursor.close()
            
    def uploadSchema(self, event):
        fileChooser = wx.FileDialog(form, "Select a .SQL schema file to setup database.", "", "","SQL files (*.SQL)|*.SQL", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fileChooser.ShowModal() == wx.ID_CANCEL:
            return False
        path = fileChooser.GetPath()
        file = open(path, "r", 1)
        string = file.read()
        cursor = database.cursor()
        cursor.execute(string,multi=True)
        cursor.close()
        database.commit()
        
    def loadFile(self, event):
        fileChooser = wx.FileDialog(self, "Select your .TSP file", "", "","TSP files (*.TSP)|*.TSP", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fileChooser.ShowModal() == wx.ID_CANCEL:
            return
        cityList = []
        path = fileChooser.GetPath()
        file = open(path, "r", 1)
        string = file.read()
        list = string.split("\n", -1)
        nodeStart = 1
        name = path.split("\\")[-1].split(".")[0]
        print(name)
        self.SetTitle(name)
        for string in list:
                if(string.isupper()):
                    ++nodeStart
                    if string != "NODE_COORD_SECTION" and string != "EOF":
                        dat_raw = string.split(":")
                        dat = dat_raw[1].strip(' ')
                        identifier = dat_raw[0].strip(' ')
                        if identifier == "NAME":
                            name = dat
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
        uploadProblem(database, name, cityList)
        
    def loadProblem(self, event):
        problemList = getUploadedProblems(database)
        print("Downloading problem")
        dlg = wx.TextEntryDialog(self, '<< Enter the name of the TSP problem you would like to download >>\n'+problemList,'TSP Name')
        dlg.SetValue("")
        name = ""
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
        if name.find("."):
            name = name.split(".")[0]
        dlg.Destroy()
        self.SetTitle(name)
        
        cityList = downloadCityList(database, name)
        
        global loadedProblem
        loadedProblem = TSP(name)
        loadedProblem.cityList = cityList
        
        if cityList is not None:
            xList = []
            yList = []
            for city in cityList:
                xList.append(city.posX)
                yList.append(city.posY)
            global plotArea
            plotGraph(xList, yList, name, plotArea)
            
        

        
    def saveSolution(self, event):
        solution = getLoadedSolution()
        pathString = ""
        for city in solution.cityList:
            pathString = (pathString + str(city.cityID) + " ")
        pathString = (pathString + "-1")
        
        cursor = database.cursor()
        qry = "INSERT INTO Solution (problemName, TourLength, Date, Author, Algorithm, RunningTime, Tour) VALUES ('"+solution.name+"',"+str(solution.getLength())+",NOW(),'"+solution.author+"','"+solution.algorithm+"',"+str(solution.solveTime)+",'"+pathString+"')"
        print(qry)
        cursor.execute(qry)
        database.commit()
        cursor.close()
        
    
    def loadSolution(self, event):
        author = "s5101994"
        problemList = getSolutionsFromAuthor(database, author)
        print("Downloading problem")
        dlg = wx.TextEntryDialog(self, '<< Enter the name of the TSP problem you would like to download >>\n'+problemList,'TSP Name')
        dlg.SetValue("")
        name = ""
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
        if name.find("."):
            name = name.split(".")[0]
        dlg.Destroy()
        self.SetTitle(name + " [Solution]")
        
        solution = downloadSolution(database, name, author)
        
        global loadedSolution
        loadedSolution = solution
        
        if solution.cityList is not None:
            xList = []
            yList = []
            for city in solution.cityList:
                xList.append(city.posX)
                yList.append(city.posY)
            global plotArea
            plotTSP(solution, plotArea)
            
            consoleText = loadedProblem.name+" Solution:\n* Author: "+loadedSolution.author+"\n* Solve Time: "+str(loadedSolution.solveTime)+" seconds\n* Tour Length: "+str(loadedSolution.getLength())+"\n* Date/Time: "+str(loadedSolution.date)+"\n* Algorithm: "+loadedSolution.algorithm+"\nTour:\n"
            index = 1
            for city in solution.cityList:
                consoleText = (consoleText + str(index)+": City " + str(city.cityID)+" ("+str(city.posX)+","+str(city.posY)+")\n")
                index = (index + 1)
            global console
            console.Value = consoleText
        
        
        
    def solveProblem(self, event):
        startTime = time.time()
        if getLoadedProblem() is not None:
            if not (getLoadedProblem().name == "Default"):
                cityList = getLoadedProblem().cityList
                testPaths = []
                for city in cityList:
                    prototypePath = TestPath()
                    prototypePath.addCity(cityList[0])
                    prototypePath.addCity(city)
                    localList = []
                    for c in cityList:
                        if c != city and c != cityList[0]:
                            if c not in localList:
                                localList.append(c)
                    if getNearestCity(city, localList, prototypePath, cityList) == False:
                        testPaths.append(prototypePath)
                elapsed = (time.time()-startTime)
                global maxTime
                if(elapsed >= maxTime):
                    print("Time limit reached, terminating application.\n[",elapsed," seconds elapsed]\n[",(elapsed-maxTime)," seconds beyond limit]")
                    return None
                path = getShortestPath(testPaths)
                global loadedSolution
                loadedSolution = TSP(loadedProblem.name)
                loadedSolution.solveTime = elapsed
                loadedSolution.author = "s5101994"
                loadedSolution.cityList = path.cityList
                consoleText = loadedProblem.name+" Solution:\n* Author: "+loadedSolution.author+"\n* Solve Time: "+str(loadedSolution.solveTime)+" seconds\n* Tour Length: "+str(loadedSolution.getLength())+"\n* Date/Time: Just Now"+"\n* Algorithm: "+loadedSolution.algorithm+"\nTour:\n"
                index = 1
                for city in path.cityList:
                    consoleText = (consoleText + str(index)+": City " + str(city.cityID)+" ("+str(city.posX)+","+str(city.posY)+")\n")
                    index = (index + 1)
                global console
                console.Value = consoleText
                global plotArea
                plotTSP(loadedSolution, plotArea)
                return path
            
        
    def exitApp(self, event):
        self.Destroy()
        sys.exit(0)
        
if __name__=='__main__':    
    app = wx.App()
    form = Window(None,-1,"TSP Solver")
    form.Show(True)
    
    app.MainLoop()
    


