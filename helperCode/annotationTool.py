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

def checkIfImagesAreDone(fileName):   # This function makes query to database to see if the image is aready done
    sql= "SELECT ImageName from "+inputTable+" WHERE ImageName ='"+fileName[fileName.rfind("\\")+1:fileName.rfind(".")].replace("'","")+"'"

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
        
        self.imageList=None           # List of images in the folder to check
        self.img=None                 # Current image
        self.imgPath=None             # Current image path
        self.tuts=None                # Tuturial file
        self.imgDir=None              # Image directory
        self.label=None               # Image widget
        self.dbname=None              # Database name
        self.msg=None                 # Message 
        self.progress=None            # Progress Bar
        self.continueFlag=False

        self.statusBar()  
        self.loadLabel = self.createLabel((150, 202),(250,30),"LOAD IMAGES")
        self.loadLabel.setFont(QtGui.QFont('SansSerif', 12, QtGui.QFont.Bold))

        self.browseButton=self.createButton("BROWSE",(370, 200),(120,35),self.getImagesFolderName)
        self.pathLabel = self.createLabel((150, 250),(500,30),"")

        self.DBloadLabel = self.createLabel((150, 300),(250,30),"DATABASE FILE")
        self.DBloadLabel.setFont(QtGui.QFont('SansSerif', 12, QtGui.QFont.Bold))

        self.DBbrowseButton=self.createButton("BROWSE",(370, 300),(120,35),self.getDatabasefile)
        self.DBpathLabel = self.createLabel((150, 350),(500,30),"")


        self.startProcessing=self.createButton("START TRAINING",(250, 400),(150,35),self.loadImages)

        # Define All Labels and buttons
        self.heading = self.createLabel((970, 90),(500,30),".:IMAGE TRAINER:.")
        self.heading.setFont(QtGui.QFont('SansSerif', 15, QtGui.QFont.Bold))
        self.heading = self.createLabel((900, 140),(700,30),'1. SEARCH FOR THE OBJECT IN THE IMAGE')
        self.heading = self.createLabel((900, 170),(700,30),'2. LEFT CLICK ON UPPER LEFT CORNER OF OBJECT')
        self.heading = self.createLabel((900, 200),(700,30),'3. THEN LEFT CLICK ON LOWER RIGHT CORNER OF OBJECT')
        self.heading = self.createLabel((900, 230),(700,30),'4. LEFT CLICK ANYWHERE TO CONFIRM SELECTION')
        self.heading = self.createLabel((900, 260),(700,30),'5. IF THERE ARE NO OBJECTS THEN GO THE NEXT IMAGE BY')
        self.heading = self.createLabel((900, 280),(700,30),'   SCROLLING DOWN OR PRESSING RIGHT ARROW KEY')
        self.heading = self.createLabel((900, 310),(700,30),'6. USE D OR RIGHT-ARROW OR SCROLL-DOWN OR')
        self.heading = self.createLabel((900, 340),(700,30),'   MIDDLE MOUSE BUTTON FOR NEXT IMAGE')
        self.heading = self.createLabel((900, 360),(700,30),'7. USE A OR LEFT-ARROW OR SCROLL-UP FOR PREVIOUS IMAGE')
        self.heading = self.createLabel((900, 390),(700,30),'8. USE RIGHT CLICK TO UNDO SELECTION')
        self.heading = self.createLabel((900, 420),(700,30),'9. MAKE SURE THE OBJECT FALLS COMPLETELY IN THE BOX')
        self.heading = self.createLabel((900, 450),(700,30),'10. IN CASE MORE THAN ONE OBJECTS ARE PRESENT THEN AFTER')
        self.heading = self.createLabel((900, 470),(700,30),'   FIRST SELECTION PRESS F AND MAKE THE NEXT SELECTION')
        self.tutButton=self.createButton("TUTORIAL",(950, 530),(130,35),self.showTuts)  # Create button
        self.quitButton=self.createButton("CLOSE",(1100, 530),(130,35),QtCore.QCoreApplication.instance().quit)

        
        self.setMinimumSize(1550, 700)  # Set minimum window size 
        #self.showMaximized()            # Maximize window  
        self.show()                     # Show window


    def getDatabasefile(self):  # Open file dialog box to get database file name
        self.dbname=  QFileDialog.getSaveFileName(None, 'Open Database', '',"Database files (*.db)") [0]
        self.DBpathLabel.setText(self.dbname)           

    def getImagesFolderName(self): # Open Directory dialog box to get input image folder
        self.imgDir=QFileDialog.getExistingDirectory(None, 'Open Images Directory:', '', QFileDialog.ShowDirsOnly)
        self.pathLabel.setText(self.imgDir)

    def loadImages(self):  # Load images from directory

        if self.dbname== None or self.imgDir==None:  # Validate input fields
            self.msg = QMessageBox(self) 
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setWindowTitle("Start Training Error")
            self.msg.setText("Manditory Fields Not Entered")
            self.msg.show()
            return

        self.imageList=glob.glob(self.imgDir+"\*.jpg")

        if len (self.imageList) == 0:
            self.msg = QMessageBox(self) 
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setWindowTitle("Folder Empty")
            self.msg.setText("No Images found in the folder")
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

    
        # connect database
        conn = sqlite3.connect(self.dbname)
        conn.execute('''CREATE TABLE IF NOT EXISTS TaggedImages
         (ImageName varchar(500) NOT NULL PRIMARY KEY,
         tags varchar(300),
         Detection varchar(15));''')

        # Read all images from folder
        

        try:
            while checkIfImagesAreDone(self.imageList[self.index]):  # Skip all images already processed
                self.index+=1
        except IndexError:
            self.index = len(self.imageList)-1
            self.msg = QMessageBox(self) 
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setWindowTitle("Completed")
            self.msg.setText("All Images in folder tagged")
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

    def showTuts(self): # show tutorial
        self.tuts=Tutorial()    # Create tutorial object
        self.tuts.show()


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
        h,w,_=self.img.shape
        self.delta=600/float(h) if 600/float(h)<1 else 1

        cv_img=cv2.resize(self.img, (0,0), fx=self.delta, fy=self.delta)  

        height, width, bytesPerComponent = cv_img.shape
        self.label.resize(width,height)
        bytesPerLine = bytesPerComponent * width;
        cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB, cv_img)
        self.label.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888))) 


    def getPos(self , event):  # This function is called when mouse is clicked

        sizeDelta = int(self.img.shape[0]/float(700))

        if event.button() == QtCore.Qt.LeftButton:

            if not self.continueFlag:
                if len(self.points)%2==0 and len(self.points)>0:  # This code block is run when user confirms selection
                    # Add Data to database and load next image
                    fltpt=[str(z) for y in self.points for z in y]
                    sql="INSERT OR REPLACE INTO "+inputTable+" (ImageName,tags,Detection) VALUES ('"+self.imgPath[self.imgPath.rfind("\\")+1:self.imgPath.rfind(".")].replace("'","\'")+"','"+"|".join([fltpt[x]+","+fltpt[x+1]+";"+fltpt[x+2]+","+fltpt[x+3] for x in  range(0,len(fltpt),4)])+"','"+"Detected"+"')"
                    conn.execute(sql)
                    conn.commit()
                    self.points=[]
                    self.index+=1
                    self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
                    try:
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

    
    def keyPressEvent(self, e):      # In the event that a key is pressed
        if e.key() == QtCore.Qt.Key_Right or e.key() == QtCore.Qt.Key_D or e.key() == QtCore.Qt.MiddleButton:   # If key pressed is right arrow or D
            # Load next image
            sql="INSERT OR REPLACE INTO "+inputTable+" (ImageName,tags,Detection) VALUES ('"+self.imgPath[self.imgPath.rfind("\\")+1:self.imgPath.rfind(".")].replace("'","")+"',' ','"+"Not Detected"+"')"
            conn.execute(sql)
            conn.commit()
            self.index+=1
            self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
            self.points=[]
            try:
                self.imageOpenCv2ToQImage(self.imageList[self.index])
            except IndexError:
                self.index-=1
                self.msg = QMessageBox(self) 
                self.msg.setIcon(QMessageBox.Information)
                self.msg.setWindowTitle("Completed")
                self.msg.setText("All Images in folder tagged")
                self.msg.show()
            
        elif e.key() == QtCore.Qt.Key_Left or e.key() == QtCore.Qt.Key_A:   # If key pressed is left arrow or A
            # Load previous image
            self.index-=1
            self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
            self.points=[]
            try:
                self.imageOpenCv2ToQImage(self.imageList[self.index])
            except IndexError:
                self.index+=1
                self.msg = QMessageBox(self) 
                self.msg.setIcon(QMessageBox.Information)
                self.msg.setWindowTitle("Completed")
                self.msg.setText("All Images in folder tagged")
                self.msg.show()

        if  e.key() == QtCore.Qt.Key_F:
            self.continueFlag=True


    def wheelEvent(self,event):

        if event.angleDelta().y()>0: # Scroll Up
            # Load next image
            sql="INSERT OR REPLACE INTO "+inputTable+" (ImageName,tags,Detection) VALUES ('"+self.imgPath[self.imgPath.rfind("\\")+1:self.imgPath.rfind(".")].replace("'","")+"',' ','"+"Not Detected"+"')"
            conn.execute(sql)
            conn.commit()
            self.index+=1
            self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
            self.points=[]
            try:
                self.imageOpenCv2ToQImage(self.imageList[self.index])
            except IndexError:
                self.index-=1
                self.msg = QMessageBox(self) 
                self.msg.setIcon(QMessageBox.Information)
                self.msg.setWindowTitle("Completed")
                self.msg.setText("All Images in folder tagged")
                self.msg.show()

        
        if event.angleDelta().y()<0:# Scroll Down
            # Load previous image
            self.index-=1
            self.progress.setValue(abs(self.index*100/float(len(self.imageList))))
            self.points=[]
            try:
                self.imageOpenCv2ToQImage(self.imageList[self.index])
            except IndexError:
                self.index+=1
                self.msg = QMessageBox(self) 
                self.msg.setIcon(QMessageBox.Information)
                self.msg.setWindowTitle("Completed")
                self.msg.setText("All Images in folder tagged")
                self.msg.show()



class Tutorial(QtWidgets.QMainWindow):
    def __init__(self,parent=None):

        QtWidgets.QMainWindow.__init__(self,parent) # Tutorial Window
        self.label = QLabel(self)
        self.label.move(105,40)   
        self.tutList=pickle.load(open(tutorialFile,"rb"))
        self.currImage=self.tutList[0]
        cv2.cvtColor(self.currImage, cv2.COLOR_BGR2RGB, self.currImage)
        self.imageOpenCv2ToQImage(self.currImage)
        self.label.mousePressEvent = self.nextImg
        self.setMinimumSize(820, 700)
        self.setMaximumSize(820, 700)
        self.counter=0
        self.quitButton = QPushButton("CLOSE", self) 
        self.quitButton.move(345, 650)                          # Position the button
        self.quitButton.clicked.connect(self.closeWindow) 
        self.createLabel((350,0),(200,40),"CLICK TO PROCEED")
        self.show()

    def createLabel(self,pos,size,data):
        label = QLabel(data,self)
        label.resize(size[0],size[1])
        label.move(pos[0],pos[1])
        label.setFont(QtGui.QFont('ComicSans', 10))

        return label

    def closeWindow(self):
        self.close()

    def imageOpenCv2ToQImage (self, cv_img):
        
        height, width, bytesPerComponent = cv_img.shape
        self.label.resize(width,height)
        bytesPerLine = bytesPerComponent * width;
        self.label.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)))

    def nextImg(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            font = cv2.FONT_HERSHEY_SIMPLEX
            if self.counter==0:
                self.counter+=1
                cv2.putText(self.currImage,'1. SEARCH FOR GAS TANKS IN THE IMAGE',(20,50), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==1:
                self.counter+=1
                cv2.putText(self.currImage,'2. LEFT CLICK ON UPPER LEFT CORNER OF GAS TANK',(20,80), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                cv2.circle(self.currImage,(240,325), 3, (0,0,255), -1)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==2:
                self.counter+=1
                cv2.putText(self.currImage,'3. LEFT CLICK ON LOWER RIGHT CORNER OF GAS TANK',(20,110), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                cv2.circle(self.currImage,(328,435), 3, (0,0,255), -1)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==3:
                self.counter+=1
                cv2.putText(self.currImage,'4. LEFT CLICK ANYWHERE TO CONFIRM SELECTION',(20,140), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                cv2.rectangle(self.currImage,(240,325),(328,435),(0,255,0),3)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==4:
                self.counter+=1
                self.currImage=self.tutList[1]
                self.label.move(50,80)   
                self.quitButton.move(345, 600) 
                cv2.cvtColor(self.currImage, cv2.COLOR_BGR2RGB, self.currImage)
                cv2.putText(self.currImage,'1. SEARCH FOR GAS TANKS IN THE IMAGE',(30,50), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==5:
                self.counter+=1
                self.currImage=self.tutList[1]
                cv2.putText(self.currImage,'2. IF NO GAS TANKS ARE FOUND GO TO NEXT IMAGE BY',(30,80), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                cv2.putText(self.currImage,'   SCROLLING UP OR PRESSING RIGHT ARROW KEY',(30,110), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==6:
                self.counter+=1
                self.currImage=self.tutList[2]
                self.label.move(70,50)   
                self.quitButton.move(345, 610) 
                cv2.cvtColor(self.currImage, cv2.COLOR_BGR2RGB, self.currImage)
                cv2.putText(self.currImage,'1. SEARCH FOR GAS TANKS IN THE IMAGE',(30,50), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==7:
                self.counter+=1
                cv2.putText(self.currImage,'2. MULTIPLE GAS TANKS PRESENT',(30,80), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==8:
                self.counter+=1
                cv2.putText(self.currImage,'3. MARK FIRST TANK',(30,110), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                cv2.rectangle(self.currImage,(226,400),(275,474),(0,255,0),3)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==9:
                self.counter+=1
                cv2.putText(self.currImage,'4. PRESS KEY F',(30,140), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==10:
                self.counter+=1
                cv2.putText(self.currImage,'5. MARK SECOND TANK',(30,170), font, 0.6,(255,255,0),2,cv2.LINE_AA)
                cv2.rectangle(self.currImage,(434,275),(545,325),(0,255,0),3)
                self.imageOpenCv2ToQImage(self.currImage)
            elif self.counter==11:
                self.close()


# inputData=r"D:\BackUp_Geospoc_Shubham\AmeriGas\APICALL\Detected\TrainSet\Tiles"
# imageList=glob.glob(inputData+"\*.jpg")


tutorialFile="Tutorial.pkl"
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
    ex = TrainerUI()
    #ex=Tutorial()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


