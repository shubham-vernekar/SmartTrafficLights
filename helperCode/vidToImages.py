import cv2
import glob
import os
from tqdm import tqdm

def videoToImages(videoFileName, outputFolder, interval = 1):
    """ The function videoToImages saves each n'th frame of a video as an image
        Input arguments are:
        videoFileName: Path to the video file to be processed
        outputFolder: Path of the folder where the images will be saved
        interval: number of frames to be skipped between each frame write, Default is 1 """

    cap = cv2.VideoCapture(videoFileName)  # Open the video file
    counter = 0
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get total frames
    for counter in tqdm(range(length), ncols = 110, desc = "Splitting Video : {} , Progress ->".format(videoFileName)):
        ret, frame = cap.read()

        if counter%interval==0:
            # Write image to disk
            cv2.imwrite (os.path.join(outputFolder, os.path.splitext(os.path.basename (videoFileName))[0]+"_"+str(int(counter/interval)).zfill(5)+".jpg"), frame)
    
    # Cleanup
    cap.release()

videosFolder = r"..\videos\train"  # Folder location on disk where video files are stored
outputFolder = r"..\images\train"  # Folder location on disk where the image frames will be stored
videoFiles = glob.glob(videosFolder+"/*")

# Create output folder if it does not exists
if not os.path.exists(outputFolder):
    os.mkdir(outputFolder)

for videoFileName in videoFiles:
    videoToImages(videoFileName, outputFolder, 20)
