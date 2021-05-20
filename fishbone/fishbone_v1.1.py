"""
#Created by Amanda Roberts on 01/08/2021.
#Last edited 04/28/2021
#Code is using Python 2.7 and ArcMap 10.7
#Status: Runs and produces expected result
#
#This code automates the fishbone analysis used by 911 and takes in a 
#schema file that contains the needed inputs
"""

#import needed packages
import arcpy
from arcpy import env
import pandas as pd
import os

#make the fishbone process a function so it can be called in other programs
# address - the name of the address file without its extension
# centerlines - the name of the centerlines file without its extension
# schemaFile - the path to the schema file including its name and extension
def fishbone(address, centerlines, schemaFile):
    
    #determine the coordinate system of the files
    env.outputCoordinateSystem = arcpy.Describe(address + ".shp").spatialReference
    
    #run make feature layer so processes can be performed on the files
    addFC = "addressFC"
    centerFC = "centerFC"
    arcpy.MakeFeatureLayer_management(address + ".shp", addFC)
    arcpy.MakeFeatureLayer_management(centerlines + ".shp", centerFC)
    print("Created address and centerlines feature layers")
    
    #convert dbf of the address file to csv
    inTable = "addressFC.dbf"
    outTable = "addressdbfConvert1.csv"
    outLoc = schemaFile.iloc[0, 2]
    arcpy.TableToTable_conversion(inTable, outLoc, outTable)
    print("Converted address dbf")
    
    #remove the OID field that sometimes gets added from converting to csv 
    os.chdir(outLoc)
    df = pd.read_csv(outTable, delimiter = ",")
    outCSV = schemaFile.iloc[0, 5]
    try:
        df = df.drop("OID", axis = 1)
    except: 
        print("OID does not exist in the table")
    df.to_csv(outLoc + "/" + outCSV)
    print("Created csv file")
    
    #geocode the csv file using a premade address locator
    addressField = schemaFile.iloc[0, 6]
    zipField = schemaFile.iloc[0, 7]
    addressLocator = schemaFile.iloc[0, 8]
    addressFields = "Street " + addressField + ";ZIP " + zipField
    geocodeResult = "geocodeResult1"
    arcpy.GeocodeAddresses_geocoding(outCSV, addressLocator, addressFields, geocodeResult)
    print("Finished geocoding")
    
    #repair geometry on the addresses in the geocode output file
    tempLayer3 = "geocodeFC"
    arcpy.MakeFeatureLayer_management("geocodeResult1.shp", tempLayer3)
    arcpy.RepairGeometry_management(tempLayer3, "KEEP_NULL")
    
    #export to shapefile
    repairResult = "repairResult1"
    arcpy.CopyFeatures_management(tempLayer3, repairResult)
    print("Created new file with the repaired geometry")
    
    #check for scores that aren't 100
    fc = outputLoc + "/" + repairResult + ".shp"
    fields = ["Score", "FID"] 
    expression = "Score < 100" 
    unmatchValues = arcpy.da.UpdateCursor(fc, fields, expression)
    for record in unmatchValues:
        print("Record number " + str(record[1]) + " has a match score of " + str(record[0]))
    
    #add x, y, and join fields in the results and address files
    repairResult = "repairResult1.shp"
    arcpy.AddField_management(repairResult, "NewXField1", "FLOAT", 9, 2)
    arcpy.AddField_management(repairResult, "NewYField1", "FLOAT", 9, 2)
    arcpy.AddField_management(repairResult, "JoinField1", "TEXT", "", "", 100)
    
    arcpy.AddField_management(addFC, "NewXField2", "FLOAT", 9, 2)
    arcpy.AddField_management(addFC, "NewYField2", "FLOAT", 9, 2)
    arcpy.AddField_management(addFC, "JoinField2", "TEXT", "", "", 100)
    
    print("Added fields")
    
    #calculate geometry on x and y
    arcpy.CalculateField_management(repairResult, "NewXField1", "!shape.extent.XMax!", "PYTHON_9.3")
    arcpy.CalculateField_management(repairResult, "NewYField1", "!shape.extent.YMax!", "PYTHON_9.3")
    
    arcpy.CalculateField_management(addFC, "NewXField2", "!shape.extent.XMax!", "PYTHON_9.3")
    arcpy.CalculateField_management(addFC, "NewYField2", "!shape.extent.YMax!", "PYTHON_9.3")
    
    #calculate join to equal the full address and zip code 
    repairAddress = schemaFile.iloc[0, 9]
    repairZipcode = schemaFile.iloc[0, 10]
    expression1 = '!' + str(repairAddress) + '! + " " + !' + str(repairZipcode) + '!'
    expression2 = '!' + str(addressField) + '! + " " + !' + str(zipField) + '!'
    arcpy.CalculateField_management(repairResult, "JoinField1", expression1, "PYTHON_9.3")
    arcpy.CalculateField_management(addFC, "JoinField2", expression2, "PYTHON_9.3")
    
    print("Calculated fields")
    
    #join the two datasets and export them
    arcpy.MakeFeatureLayer_management(repairResult, "repairFC")
    arcpy.AddJoin_management("repairFC.shp", "JoinField1", "addressFC.dbf", "JoinField2")
    joinFile = "joinFile1"
    arcpy.CopyFeatures_management("repairFC", joinFile)
    print("Joined tables and exported file")
    
    #run xy to line
    arcpy.XYToLine_management("joinFile1.dbf", "outFish", "NewXField1", "NewYField1", "NewXField2", "NewYField2")
    print("XY to Line is complete")
    
    #delete temporary files; check for problems
    arcpy.Delete_management("centerEDIT.shp")
    arcpy.Delete_management("addressdbfConvert1.csv")
    arcpy.Delete_management("geocodeTable.csv")
    arcpy.Delete_management("geocodeResult1.shp")
    arcpy.Delete_management("repairResult1.shp")
    arcpy.Delete_management("addressEDIT.shp")
    arcpy.Delete_management("joinFile1.shp")
    
    return

#read in values from the schema file that are needed before the function is called   
schemaLoc = raw_input("Please enter the path to the schema file including its extension: ")
schemaLoc = schemaLoc.replace("\\", "/")
schemaIn = pd.read_csv(schemaLoc)
dataLoc = schemaIn.iloc[0, 0]
addrPoints = schemaIn.iloc[0, 1]
outputLoc = schemaIn.iloc[0, 2]
centerPath = schemaIn.iloc[0, 3]
centerFile = schemaIn.iloc[0, 4]

#set the environment to the location of the address points
env.workspace = dataLoc
env.overwriteOutput = True

#export the file to a local location
arcpy.FeatureClassToFeatureClass_conversion(addrPoints, outputLoc, "addressEDIT")
print("Exported address points to local location")

#set the environment to the location of the centerline file
env.workspace = centerPath
env.overwriteOutput = True

#export the file to a local location
arcpy.FeatureClassToFeatureClass_conversion(centerFile, outputLoc, "centerEDIT")
print("Exported centerlines to local location")

#Change the environment to the local location, allow overwriting,
#and have the joined fields not include the table name
env.workspace = outputLoc
env.overwriteOutput = True
env.qualifiedFieldNames = False

#run the fishbone analysis
fishbone("addressEDIT", "centerEDIT", schemaIn)

print("Exiting program")



