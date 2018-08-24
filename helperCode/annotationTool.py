import sys
# from PySide2 import QtCore
# from PySide2 import QtGui
# from PySide2.QtGui import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

import cv2
import glob
import  pickle
import time
from collections import defaultdict
import sqlite3
import re
import os
import csv

def checkIfImagesAreDone(fileName):   # This function makes query to database to see if the image is aready done
    # sql= "SELECT ImageName from "+inputTable+" WHERE ImageName ='"+fileName[fileName.rfind("\\")+1:fileName.rfind(".")].replace("'","")+"'"
    sql = 'SELECT ImageName from {} WHERE ImageName = "{}" '.format(inputTable,os.path.basename(fileName)) 

    if list(conn.execute(sql))==[]:
        return False
    else:
        return True

#QtWidgets.QPushButton
# QtWidgets.QApplication
class TrainerUI(QtWidgets.QMainWindow):
    def __init__(self,parent=None):

        QtWidgets.QMainWindow.__init__(self,parent)
        
        self.points=[]                # Current points selection
        self.index=0                  # Index of current image
        self.delta=1                  # This is used to convert resized points to actual image coordinates
        
        self.imageList = None           # List of images in the folder to check
        self.img = None                 # Current image
        self.imgPath = None             # Current image path
        self.tuts = None                # Tuturial file
        self.imgDir = None              # Image directory
        self.label = None               # Image widget
        self.dbFile = None              # Database name
        self.msg = None                 # Message 
        self.progress = None            # Progress Bar
        self.continueFlag = False       # This flag is made true if you want to make multiple selections
        self.generateCSVButton = None   # Generate CSV Button

        self.statusBar()  
        self.loadLabel = self.createLabel((150, 202),(250,30),"LOAD IMAGES")
        self.loadLabel.setFont(QtGui.QFont('SansSerif', 12, QtGui.QFont.Bold))

        self.browseButton = self.createButton("BROWSE",(370, 200),(120,35),self.getImagesFolderName)
        self.pathLabel = self.createLabel((150, 250),(500,30),"")

        self.DBloadLabel = self.createLabel((150, 300),(250,30),"DATABASE FILE")
        self.DBloadLabel.setFont(QtGui.QFont('SansSerif', 12, QtGui.QFont.Bold))

        self.DBbrowseButton = self.createButton("BROWSE",(370, 300),(120,35),self.getDatabasefile)
        self.DBpathLabel = self.createLabel((150, 350),(500,30),"")

        # Define All Labels and buttons
        self.heading = self.createLabel((970, 90),(500,30),".:IMAGE TRAINER:.")
        self.heading.setFont(QtGui.QFont('SansSerif', 15, QtGui.QFont.Bold))

        self.heading = self.createLabel((900, 140),(700,30),'1. SEARCH FOR THE OBJECT IN THE IMAGE')
        self.heading = self.createLabel((900, 170),(700,30),'2. LEFT CLICK ON UPPER LEFT CORNER OF OBJECT')
        self.heading = self.createLabel((900, 200),(700,30),'3. THEN LEFT CLICK ON LOWER RIGHT CORNER OF OBJECT')
        self.heading = self.createLabel((900, 230),(700,30),'4. LEFT CLICK ANYWHERE TO CONFIRM SELECTION')
        self.heading = self.createLabel((900, 260),(700,30),'5. IF THERE ARE NO OBJECTS THEN GO THE NEXT IMAGE BY')
        self.heading = self.createLabel((900, 280),(700,30),'   SCROLLING DOWN OR PRESSING RIGHT ARROW KEY')
        self.heading = self.createLabel((900, 310),(700,30),'6. USE D OR RIGHT-ARROW OR SCROLL-DOWN FOR NEXT IMAGE')
        self.heading = self.createLabel((900, 340),(700,30),'7. USE A OR LEFT-ARROW OR SCROLL-UP FOR PREVIOUS IMAGE')
        self.heading = self.createLabel((900, 370),(700,30),'8. USE RIGHT CLICK TO UNDO SELECTION')
        self.heading = self.createLabel((900, 400),(700,30),'9. MAKE SURE THE OBJECT FALLS COMPLETELY IN THE BOX')
        self.heading = self.createLabel((900, 430),(700,30),'10. IN CASE MORE THAN ONE OBJECTS ARE PRESENT THEN AFTER')
        self.heading = self.createLabel((900, 450),(700,30),'   FIRST SELECTION PRESS F OR THE MIDDLE MOUSE BUTTON')
        self.heading = self.createLabel((900, 470),(700,30),'   AND THEN MAKE THE NEXT SELECTION')
        
        self.startProcessing = self.createButton("START TRAINING",(260, 420),(150,35),self.loadImages)
        self.generateCSVButton = self.createButton("GENERATE CSV",(260, 470),(150,35),self.generateCSV) 
        self.quitButton=self.createButton("CLOSE",(1025, 530),(130,35),QtCore.QCoreApplication.instance().quit)

        self.generateCSVButton.hide()

        self.setMinimumSize(1550, 800)  # Set minimum window size 
        #self.showMaximized()            # Maximize window  
        self.show()                     # Show window


    def getDatabasefile(self):  # Open file dialog box to get database file name
        global conn
        self.dbFile=  QFileDialog.getSaveFileName(None, 'Open Database', '',"Database files (*.db)") [0]

        if os.path.exists(self.dbFile):
            # If the database already exists then show createCSV function
            self.generateCSVButton.show()

        self.DBpathLabel.setText(self.dbFile)

        # connect database
        conn = sqlite3.connect(self.dbFile)
               

    def getImagesFolderName(self): # Open Directory dialog box to get input image folder
        self.imgDir = QFileDialog.getExistingDirectory(None, 'Open Images Directory:', '', QFileDialog.ShowDirsOnly)
        self.pathLabel.setText(self.imgDir)

    def messageBox(self,messageType,title,message):
        msg = QMessageBox(self) 
        msg.setIcon(messageType)
        msg.setWindowTitle(title)
        msg.setText(message)
        return msg


    def loadImages(self):  # Load images from directory

        if self.dbFile== None or self.imgDir==None:  # Validate input fields
            self.msg = self.messageBox(QMessageBox.Critical,"Start Training Error","Manditory Fields Not Entered")
            self.msg.show()
            return

        self.imageList=glob.glob(self.imgDir+"/*.jpg")

        if len (self.imageList) == 0:
            self.msg = self.messageBox(QMessageBox.Critical,"Folder Empty","No Images found in the folder")
            self.msg.show()
            return

        global conn   # Database connection object

        # Data input GUI
        self.loadLabel.hide()
        self.browseButton.hide()
        self.pathLabel.hide()
        self.startProcessing.hide()
        self.DBloadLabel.hide()
        self.DBbrowseButton.hide()
        self.DBpathLabel.hide()
        self.generateCSVButton.move(450,8)

        conn.execute('''CREATE TABLE IF NOT EXISTS TaggedImages
         (ImageName TEXT NOT NULL PRIMARY KEY,
         Tags TEXT,
         Detection TEXT,
         Height INT,
         Width INT) ;''')

        # Read all images from folder
        

        try:
            while checkIfImagesAreDone(self.imageList[self.index]):  # Skip all images already processed
                self.index+=1
        except IndexError:
            self.index = len(self.imageList)-1
            self.msg = self.messageBox(QMessageBox.Information,"Completed","All Images in folder tagged")
            self.msg.show()

        self.progLabel = self.createLabel((60, 12),(250,30),"PROGRESS:")
        self.progLabel.setFont(QtGui.QFont('SansSerif', 11, QtGui.QFont.Bold))
        self.progLabel.show()

        self.progress = QProgressBar(self)
        self.progress.move(170,18)
        self.progress.resize(200,18)
        self.progress.setStyle(QtWidgets.QStyleFactory.create("plastique")) 
        self.progress.show()

        self.progress.setValue(abs(self.index*100/float(len(self.imageList))))

        self.label = QLabel(self)   # This label is used to show the image
        self.label.move(50,50)
        self.imageOpenCv2ToQImage(self.imageList[self.index])  # This function displays an opencv image in window
        self.label.mousePressEvent = self.getPos   # Function assigned to on click event
        self.label.show()

    def writeCSV(self,detections,outputCSVFilename,objectClass):

        csvfile = open(outputCSVFilename, 'w', encoding='utf-8-sig')
        csvfile.write (",".join(["filename","width","height","class","xmin","ymin","xmax","ymax"])+"\n")

        for filename, detection, height, width in detections:
            boxes = detection.split("|")
            for box in boxes:
                box = box.split(";")
                x1,y1 = map(int,box[0].split(","))
                x2,y2 = map(int,box[1].split(","))

                xMax = max([x1,x2])
                yMax = max([y1,y2])
                xMin = min([x1,x2])
                yMin = min([y1,y2])

                csvfile.write (",".join(map(str, [filename,width,height,objectClass,xMin,yMin,xMax,yMax]))+"\n")

        csvfile.close()


    def generateCSV(self): 
        # objectClass, ok = QInputDialog.getText(self, 'Enter Name', 'Enter the name of the object')
        # if ok and objectClass.strip()!="":
        #     print (objectClass)
        # else:
        #     self.msg = self.messageBox(QMessageBox.Critical,"Invalid","Invalid Entry")
        #     self.msg.show()
        #     return

        sqlQuery = 'SELECT ImageName,Tags,Height,Width FROM {} WHERE Detection="Detected"'.format(inputTable)
        detections = list(conn.execute(sqlQuery))

        if detections == []:
            self.msg = self.messageBox(QMessageBox.Information,"Zero Detections","No detections found")
            self.msg.show()
            return

        # outputCSVFilename = QFileDialog.getSaveFileName(None, 'Save CSV File', '',"CSV files (*.csv)") [0]

        objectClass="humans"
        outputCSVFilename=r"J:\MySoftwares\Python\SmartTrafficLights\SmartTrafficLights\helperCode\humans.csv"

        self.writeCSV(detections,outputCSVFilename,objectClass)
        




    def createButton(self,text,pos,size,function,css=""):  # This function creates button 
        Button = QPushButton(text, self)  # Define button
        Button.move(pos[0], pos[1])             # Position the button
        Button.clicked.connect(function)        # Assign function to be called when button is clicked
        Button.resize(size[0],size[1])          # Size of the button
        Button.setStyleSheet(css)                   # Add stylesheet to the button
        Button.setFocusPolicy(QtCore.Qt.NoFocus)    # Stop buttons from focussing
        return Button

    def createLabel(self,pos,size,data):  # This function creates label
        label = QLabel(data,self)
        label.resize(size[0],size[1])
        label.move(pos[0],pos[1])
        label.setFont(QtGui.QFont('ComicSans', 10))
        return label

    def imageOpenCv2ToQImage (self, img_path,isPath=True):  # This function displays an opencv image in window 
        # if imgage path is passed then isPath should be True or if an opencv image is passed the isPath should be false

        if isPath:
            self.img=cv2.imread(img_path)
            self.imgPath=img_path

        # Resize image to fit out UI and save the ratio of resize in self.delta
        h = self.img.shape[0]
        self.delta=700/float(h) if 700/float(h)<1 else 1

        cv_img=cv2.resize(self.img, (0,0), fx=self.delta, fy=self.delta)  

        height, width, bytesPerComponent = cv_img.shape
        self.label.resize(width,height)
        bytesPerLine = bytesPerComponent * width
        cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB, cv_img)
        self.label.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888))) 


    def getPos(self , event):  # This function is called when mouse is clicked

        height,width,_ = self.img.shape
        sizeDelta = int(height/float(700))

        if event.button() == QtCore.Qt.LeftButton:

            if not self.continueFlag:
                if len(self.points)%2==0 and len(self.points)>0:  # This code block is run when user confirms selection
                    # Add Data to database and load next image
                    fltpt=[str(z) for y in self.points for z in y]
                    #sql="INSERT OR REPLACE INTO "+inputTable+" (ImageName,Tags,Detection) VALUES ('"+self.imgPath[self.imgPath.rfind("\\")+1:self.imgPath.rfind(".")].replace("'","\'")+"','"+"|".join([fltpt[x]+","+fltpt[x+1]+";"+fltpt[x+2]+","+fltpt[x+3] for x in  range(0,len(fltpt),4)])+"','"+"Detected"+"')"
                    detectionsString = "|".join([fltpt[x]+","+fltpt[x+1]+";"+fltpt[x+2]+","+fltpt[x+3] for x in  range(0,len(fltpt),4)])
                    sql = "INSERT OR REPLACE INTO {} (ImageName,Tags,Detection,Height,Width) VALUES ('{}','{}','Detected',{},{})".format(inputTable, os.path.basename(self.imgPath), detectionsString, height, width)
                    conn.execute(sql)
                    conn.commit()
                    self.points=[]
                    self.index+=1
                    self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
                    try:
                        self.statusBar().showMessage(os.path.basename(self.imageList[self.index]))
                        self.imageOpenCv2ToQImage(self.imageList[self.index])
                    except IndexError:
                        self.index-=1
                        self.msg = QMessageBox(self) 
                        self.msg.setIcon(QMessageBox.Information)
                        self.msg.setWindowTitle("Completed")
                        self.msg.setText("All Images in folder tagged")
                        self.msg.show()
                    return

            x = int(event.pos().x()/float(self.delta))
            y = int(event.pos().y()/float(self.delta))
            self.continueFlag=False

            self.points.append([x,y])
            self.statusBar().showMessage('Position : '+str(x)+" "+str(y)+" PointList: "+str(self.points))

            if len(self.points)%1==0:
                # Draw circle for first point
                cv2.circle(self.img,(self.points[-1][0],self.points[-1][1]), 2 + sizeDelta, (0,0,255), -1)
                self.imageOpenCv2ToQImage(None,isPath=False)

            if len(self.points)%2==0 and len(self.points)>0:
                # Draw rectangle for second point
                cv2.circle(self.img,(self.points[-1][0],self.points[-1][1]), 2 + sizeDelta, (0,0,255), -1)
                cv2.rectangle(self.img,(self.points[-2][0],self.points[-2][1]),(self.points[-1][0],self.points[-1][1]),(0,255,0),2 + sizeDelta)
                self.imageOpenCv2ToQImage(None,isPath=False)

        if event.button() == QtCore.Qt.RightButton: # Clear selection when right mouse button is clicked
            self.points=[]
            self.imageOpenCv2ToQImage(self.imageList[self.index])

        if event.button() == QtCore.Qt.MiddleButton:
            self.continueFlag=True

    def loadNextImage(self):
        height,width,_ = self.img.shape
        sql =  "INSERT OR REPLACE INTO {} (ImageName,Tags,Detection,Height,Width) VALUES ('{}','','Not Detected',{},{})".format(inputTable, os.path.basename(self.imgPath), height, width)

        conn.execute(sql)
        conn.commit()
        self.index+=1
        self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
        self.points=[]

        try:
            self.statusBar().showMessage(os.path.basename(self.imageList[self.index]))
            self.imageOpenCv2ToQImage(self.imageList[self.index])
        except IndexError:
            self.index-=1
            self.msg = QMessageBox(self) 
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setWindowTitle("Completed")
            self.msg.setText("All Images in folder tagged")
            self.msg.show()

    def loadPreviousImage(self):
        self.index-=1
        self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
        self.points=[]
        try:
            self.statusBar().showMessage(os.path.basename(self.imageList[self.index]))
            self.imageOpenCv2ToQImage(self.imageList[self.index])
        except IndexError:
            self.index+=1
            self.msg = QMessageBox(self) 
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setWindowTitle("Completed")
            self.msg.setText("All Images in folder tagged")
            self.msg.show()

    
    def keyPressEvent(self, e):      # In the event that a key is pressed
        if e.key() == QtCore.Qt.Key_Right or e.key() == QtCore.Qt.Key_D :   # If key pressed is right arrow or D
            # Load next image
            self.loadNextImage()
            
        elif e.key() == QtCore.Qt.Key_Left or e.key() == QtCore.Qt.Key_A:   # If key pressed is left arrow or A
            # Load previous image
            self.loadPreviousImage()
        
        if  e.key() == QtCore.Qt.Key_F:
            self.continueFlag=True
            


    def wheelEvent(self,event):

        if event.angleDelta().y()>0: # Scroll Up
            # Load previous image
            self.loadPreviousImage()

        
        if event.angleDelta().y()<0:# Scroll Down
            # Load next image
            self.loadNextImage()



# inputData=r"D:\BackUp_Geospoc_Shubham\AmeriGas\APICALL\Detected\TrainSet\Tiles"
# imageList=glob.glob(inputData+"\*.jpg")


inputTable='TaggedImages'
conn=None

# tutList= pickle.load(open(tutorialFile,"rb"))
# for i in tutList:
#     cv2.imshow("img",i)
#     cv2.waitKey(1000)

# tutList=[]
# for i in ["tutorial_01.jpg","tutorial_02.jpg","tutorial_03.jpg"]:
#     img=cv2.imread("tuts/"+i)
#     tutList.append(img)

# pickle.dump(tutList,open(tutorialFile,"wb"),2)
# quit()


# #Table Creation Query
# databaseFile = "TrainingData.db"
# conn = sqlite3.connect(databaseFile)
# conn.execute('''CREATE TABLE TaggedImages
#          (ImageName varchar(500) NOT NULL PRIMARY KEY,
#          tags varchar(300),
#          Detection varchar(15));''')
# quit()



def main():
    app = QtWidgets.QApplication(sys.argv)
    _ = TrainerUI()
    #ex=Tutorial()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


