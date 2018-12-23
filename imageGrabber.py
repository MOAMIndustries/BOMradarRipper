import time
import datetime
import requests
import numpy as np
import cv2

#Compiler variables
debug = 0
numFrames = 6
yResolution = 288
xResolution = 512
stationID = "IDR703"
outputDirectory = "/var/www/html/"    #output path for final text files

#note BGR formatting required for openCV!
intensityList = np.array([
    [255,245,245],
    [255,180,180],
    [255,120,120],
    [255,20,20],
    [195,216,0],
    [144,150,0],
    [102,102,0],
    [0,255,255],
    [0,200,255],
    [0,150,255],
    [0,100,255],
    [0,0,255],
    [0,0,200],
    [0,0,120],
    [0,0,40]
])
print"Starting"
startTime = datetime.datetime.now()

baseURL = "http://www.bom.gov.au/radar/{}.T.".format(stationID)
#get current UTC time, should be better handling of UTC offset instead of hardcode as this breaks when running locally
#minutes subtraction is to ensure the previous six minute block is captured as latest image is not updated immediatly
timeIndex = datetime.datetime.now() - datetime.timedelta(hours = 8, minutes = 5)

#sift to nearest six minute block
shift = timeIndex.minute %6
timeIndex -= datetime.timedelta(minutes = shift)

#create List of URLs for images
imageURL = []
for x in range(0,numFrames):
    imageURL.append(baseURL + timeIndex.strftime("%Y%m%d%H%M") + ".png")
    timeIndex -=  datetime.timedelta(minutes = 6)
    if debug:
        print imageURL[x]    

#create a list of file names and download the images to them
imageFileName = []
for x in range(0,len(imageURL)):
    nameString = "image%d.png" %x
    imageFileName.append(nameString)
    
    with open(imageFileName[x], 'wb') as handle:
        response = requests.get(imageURL[x], stream=True)
        if not response.ok:
            print response
            print imageURL[x]
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    
    
#create a list of cv2 image objects, cropped from 1:1 to 16:9 aspect ratio of led display. Focussed on 'Armadale'
imageList = []
for x in range(0, len(imageURL)):
    image = cv2.imread(imageFileName[x])
    image = image[58:346, 0:512]
    imageList.append(image)

#Display images when debugging
if debug:
    for x in range(0, len(imageURL)):
        cv2.imshow(imageFileName[x],imageList[x])
        cv2.waitKey(10000)
        cv2.destroyAllWindows()    

#process rain intensity images into a scaled text file suitable for processing a on a microcontroller
intensityFrames = []
for idx, image in enumerate(imageList):
    intensityPlot = np.zeros(shape=(yResolution,xResolution), dtype='uint8')  #create Null array for processed data
    if debug:
        cv2.imshow('view',image)
        cv2.waitKey(100)
    #itterate through pixels and compare against intensity
    #TODO: Look for numpy and openCV functions to perform this comparison more efficiently
    for x in range(0,xResolution):
        for y in range(0,yResolution):
            if not np.array_equal(image[y,x],[0,0,0]): #saves itterating through array if first value is null
                 for i in range(0,len(intensityList)):
                    if np.array_equal(image[y,x],intensityList[i]):
                        intensityPlot[y,x] = i+1

    if debug:
        #export intensity array as text file for verification
        nameString = "large{}.txt".format(idx)
        np.savetxt(nameString, intensityPlot, fmt='%u')

    #scale image to LED display resolution, sampling 32x32 area with the highest value
    #TODO: Make code more flexible for different display resolutions and ratios
    scaledPlot = np.zeros(shape=(9,16), dtype='uint8')
    for x in range(0,16):
        for y in range(0,9):
            yLower = y*32
            yUpper = yLower + 32
            xLower = x*32
            xUpper = xLower + 32
            scaledPlot[y,x] = np.amax(intensityPlot[yLower:yUpper,xLower:xUpper])
    nameString = "small{}.txt".format(idx)
    np.savetxt(nameString, scaledPlot, fmt='%u')

    #convertscaled plot into formatted string
    #string formatting allows for simpler microcontroller processing of code
    #collumns are ',' deliminated
    #rows are ';' deliminated
    #files are terminated with '.'
    messageString = ""
    for y in range(0,9):
        for x in range(0,16):
            messageString += "%d" %scaledPlot[y,x]
            messageString += ","
        messageString+= ";"
    messageString += "."
    print messageString
    outputFile = "{}{}.txt".format(outputDirectory, idx)
    with open(outputFile, 'wb') as handle:
        handle.write(messageString)

elapsedTime = datetime.datetime.now() - startTime
print "Elapsed Time"
print str(elapsedTime)
