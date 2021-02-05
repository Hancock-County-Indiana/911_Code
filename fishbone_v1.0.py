"""
#Created by Amanda Roberts on 01/08/2021.
#Last edited 02/03/2021
#Code is using Python 2.7 and ArcMap 10.7
#Status: Runs but needs improvements
#
#This code automates the fishbone analysis used by 911
#Search "CHANGEME" to find blocks of code that may need file path updates
"""

#import needed packages
import arcpy
from arcpy import env
import pandas as pd
import os

def fishbone(address, centerlines, outLoc):
    #make the address and centerline files feature layers so operations 
    #  can be performed on them
    addFC = "addressFC"
    centerFC = "centerFC"
    
    #determine the coordinate system of the files
    env.outputCoordinateSystem = arcpy.Describe(address + ".shp").spatialReference
    
    #run make feature layer 
    arcpy.MakeFeatureLayer_management(address + ".shp", addFC)
    arcpy.MakeFeatureLayer_management(centerlines + ".shp", centerFC)
    print("Created address and centerlines feature layers")
    
    #convert dbf of address to csv
    inTable = "addressFC.dbf"
    outTable = "addressdbfConvert1.csv"
    arcpy.TableToTable_conversion(inTable, outLoc, outTable)
    print("Converted address dbf")
    
    #remove the OID field that gets added from converting to csv 
    os.chdir(outLoc)
    df = pd.read_csv(outTable, delimiter = ",")
    try:
        df = df.drop("OID", axis = 1)
    except: 
        print("OID does not exist in the table")
    #CHANGEME
    df.to_csv("C:\Users\jmilburn\Desktop\Fishbone_Test\geocodeTable.csv")
    print("Created csv file")
    
    #geocode the csv file using a premade address locator
    #CHANGEME
    addressLocator = "C:\Users\jmilburn\Desktop\Fishbone_Test\Hancock_RCL_CreateAddressLoc"
    addressFields = "Street FULL_ADDRE;ZIP PROP_ZIP"
    geocodeResult = "geocodeResult1"
    
    arcpy.GeocodeAddresses_geocoding("geocodeTable.csv", addressLocator, addressFields, geocodeResult)
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
    #CHANGEME
    fc = "C:\Users\jmilburn\Desktop\Fishbone_Test/repairResult1.shp"
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
    arcpy.CalculateField_management(repairResult, "JoinField1", '!StAddr! + " " + !ZIP!', "PYTHON_9.3")
    arcpy.CalculateField_management(addFC, "JoinField2", '!FULL_ADDRE! + " " + !PROP_ZIP!', "PYTHON_9.3")
    
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
    return
    
#set up environment and local files
#CHANGEME
env.workspace = "C:/Users/jmilburn/AppData/Roaming/ESRI/Desktop10.7/"  + \
                "ArcCatalog/gis-01.annex.hancock.sde/sde.DBO.Staging"
env.overwriteOutput = True

#get addresses and centerlines off the database
inFeature = "sde.DBO.Hancock_Address_Points"
#CHANGEME
outLocation = "C:\Users\jmilburn\Desktop\Fishbone_Test"
arcpy.FeatureClassToFeatureClass_conversion(inFeature, outLocation, "addressEDIT")
print("Exported address points to local location")

inFeature2 = "sde.DBO.Hancock_Centerlines"
arcpy.FeatureClassToFeatureClass_conversion(inFeature2, outLocation, "centerEDIT")
print("Exported centerlines to local location")

#Change the environment to the local location, allow overwriting,
#and have the joined fields not include the table name
#CHANGEME
env.workspace = "C:\Users\jmilburn\Desktop\Fishbone_Test"
env.overwriteOutput = True
env.qualifiedFieldNames = False

#run the fishbone analysis
#CHANGEME
fishbone("addressEDIT", "centerEDIT", "C:\Users\jmilburn\Desktop\Fishbone_Test")

print("Exiting program")




