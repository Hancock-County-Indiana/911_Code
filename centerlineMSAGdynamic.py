"""
#Created by Amanda Roberts on 01/08/2021.
#Last edited 04/09/2021 by Amanda Roberts
#Code is using Python 2.7 and ArcMap 10.7
#Status: Runs on vendor and AT&T data producing results
#
This code automates the process of turning the MSAG table data into a vector file
that can be compared to RCL data
"""

#import needed packages and set up the environment
import arcpy
from arcpy import env
import pandas as pd

#function that will remove specified rows in the msag table
#loops through the records in the field given
#removes records if they match the criteria given
#  inputDF - dataframe (table) the data is in
#  field - the field that needs values removed
#  value - the value that needs to be removed
def removeRow(inputDF, field, value):
    dataframeRows = arcpy.da.UpdateCursor(inputDF, field)
    for row in dataframeRows:
        tempVal = row[0]
        if tempVal == value:
            dataframeRows.deleteRow()
    print("Deleted rows in " + field)
    return

#function that will remove specified rows in the msag table
#loops through the records in the field given
#removes records if they don't match the criteria given
#  inputDF - dataframe (table) the data is in
#  field - the field that needs values removed
#  value - the value that needs to be kept
def keepRow(inputDF, field, value):
    dataframeRows = arcpy.da.UpdateCursor(inputDF, field)
    for row in dataframeRows:
        tempVal = row[0]
        if tempVal != value:
            dataframeRows.deleteRow()
    print("Deleted rows in " + field)

#function that will help calculate the zip code
#counts how many unique town names there are
#loops through them and assigns a zip code based off the zip code csv file
#if the town doesn't exist in the zip code file, it asks the user for input
#  inputDF - dataframe (table) the data is in
#  outLoc - the location where the output will go
#  commField - the field name where the town name is
#  zipField - the field to put the zip code into
def zipCalc(inputDF, outLoc, commField, zipField):
    #make table into a csv to count unique town names
    outTable = "toCountTEMP.csv"
    arcpy.TableToTable_conversion(str(inputDF) + ".dbf", outLoc, outTable)
    readTable = str(outLoc) + "/" + str(outTable)
    tempDF = pd.read_csv(readTable)
    tempCol = tempDF[commField]
    uniqueZips = tempCol.unique()
    zipRef = pd.read_csv(outLoc+'/zipExp.csv')
    
    for i in uniqueZips:
        var = str(commField)
        expression = "\"" + var + "\" = " + "'" + str(i) + "'" #"var" = 'zip'
        arcpy.MakeTableView_management(inputDF, "tempView")
        arcpy.SelectLayerByAttribute_management("tempView", "NEW_SELECTION", expression)
        #check if there's a matching town name in the zip code file
        try:
            temp = zipRef.loc[zipRef.NAME == str(i).title(), "POSTAL"]
            if temp.size > 1:
                zipCode = raw_input("Please enter the zip code for " + str(i) + ": ")
            else:
                zipCode = str(zipRef.loc[zipRef.NAME == str(i).title(), "POSTAL"].values[0])
                zipCode = zipCode[0:5]
        except:
            zipCode = raw_input("Please enter the zip code for " + str(i) + ": ")
        arcpy.CalculateField_management("tempView", "Zip", "'" + zipCode + "'", "PYTHON_9.3")
        print("Zip code for " + i + " assigned")

#creates the expression for the fields that were created
#calculates fields based on the expression and cleans them up 
#  neededFields - list of fields needed to build the expression
#  activeDictionary - dictionary with the aliases for the needed fields
#  inputDF - dataframe (table) the data is in
#  fieldName - the field the calculations will go into
def fieldCalc(neededFields, activeDictionary, inputDF, fieldName):
    expression = ""
    for i in neededFields:
        
        #checks if the field is in the dictionary; skips iteration if not
        try:
            len(activeDictionary[i])
        except:
            continue
        
        if fieldName != "FULL_ST_NM" and i != "FULL_ST_NM":
            newField = activeDictionary[i] + "Str"
            arcpy.AddField_management(inputDF, newField, "TEXT", "", "", 50)
            copyExpr = "!" + str(activeDictionary[i]) + "!"
            arcpy.CalculateField_management(inputDF, newField, copyExpr, "PYTHON_9.3")
            activeDictionary.update({i: newField})
        
        temp = str(activeDictionary[i])
        expression += "!" 
        expression += temp 
        expression += "! + \" \" + "
        
    #idk what this is for CHANGEME
    expression = expression.strip()
    length = len(expression) - 8
    expression = expression[:length]
    
    arcpy.CalculateField_management(msagEDIT, fieldName, expression, "PYTHON_9.3")
    expressClean = '!' + fieldName + '!.replace("  ", " ")' 
    arcpy.CalculateField_management(msagEDIT, fieldName, expressClean, "PYTHON_9.3")
    expressTrim = '!' + fieldName + '!.strip()'
    arcpy.CalculateField_management(msagEDIT, fieldName, expressTrim, "PYTHON_9.3")
    

#export a copy of the msag table to a local location
msagLoc = raw_input("Please enter the path to the folder the MSAG table is in: ")
#replace backslashes with forward slashes to eliminate any accidental formatting
msagLoc = msagLoc.replace("\\", "/")

#set workspace to the location of the msag table
env.workspace = msagLoc
env.overwriteOutput = True

#convert file to .csv
inFeature = raw_input("Please enter the name of the MSAG file with its extension: ")
inFeature = msagLoc + "/" + inFeature
try:
    readFile = pd.read_excel(inFeature)
    readFile.to_csv("Raw_MSAG_Caliber_CAD.csv", index = None, header = True)
except:
    readFile = pd.read_csv(inFeature)
outLocation = raw_input("Please enter the path to the folder the output will go in: ")
#replace backslashes with forward slashes to eliminate any accidental formatting
outLocation = outLocation.replace("\\", "/")
msagCSV = "msagTableEDIT.csv"
arcpy.TableToTable_conversion("Raw_MSAG_Caliber_CAD.csv", outLocation, msagCSV)
print("Exported MSAG table to local location as a csv")

zipLoc = raw_input("Please enter the path to the folder the zip code table is in: ")
zipLoc = zipLoc.replace("\\", "/")
env.workspace = zipLoc
env.overwriteOutput = True
zipTableName = raw_input("Please enter the name of the zip code file with its extension: ")
arcpy.TableToTable_conversion(zipTableName, outLocation, "zipExp.csv")
print("Exported zip table to local location as a csv")


#change to local location
env.workspace = outLocation
env.overwriteOutput = True

#create a feature table inside of a geodatabase
msagEDIT = "msagGDB.dbf"
arcpy.TableToDBASE_conversion(msagCSV, outLocation)
arcpy.TableToTable_conversion(msagCSV, outLocation, msagEDIT)
gdbOut = raw_input("Please enter the path to the file geodatabase including its extension: ")
gdbOut = gdbOut.replace("\\", "/")
arcpy.TableToGeodatabase_conversion(msagEDIT, gdbOut)
print("Created .dbf table inside of the geodatabase")

#change location to geodatabase
env.workspace = gdbOut
env.overwriteOutput = True
msagEDIT = "msagGDB"

#set the names of the fields that need to be searched and/or removed
fieldName = ["TenantId", "IsRecordActive", "State", "LastModified", "StreetName", \
             "HouseNumLow", "HouseNumHigh", "Community", "StreetSuffix", \
             "PrefixDirectional", "PostDirectional", "Zip", "MsagId"]
userFieldName = []
activeDict = {}
#the name of fields that need values removed
removeList = ["TenantId", "IsRecordActive", "HouseNumLow", "HouseNumHigh"]
#fields that need to be deleted
deleteList = ["State", "LastModified"]
    
#determines if the field name exists in the user's table
for item in fieldName:
    success = False
    while not success:
        answer = raw_input("Does " + item + " or something similar exist in your MSAG table ('Y'/'N')? ")
        if answer == "Y":
            userIn = raw_input("Enter the name for " + str(item) + " in your MSAG table: ")
            userFieldName.append(userIn)
            activeDict.update({str(item): str(userIn)})
            success = True
        elif answer == "N":
            print(str(item) + " is being skipped...")
            success = True
        else:
            print("Invalid value.  Please try again")

#removes records/fields and gets user input for those records
for field in fieldName:
    strField = str(field)
    if field in activeDict.keys():
        print("")
        num = userFieldName.index(activeDict[field])
        if field in removeList:
            print(strField + " needs rows removed")
            recordVal = raw_input("Please enter the value ")
            print("Should records with this value be kept or deleted?")
            keepOrDel = raw_input("Enter 'True' for kept or 'False' for deleted: ")
            if keepOrDel == True:
                keepRow(msagEDIT, userFieldName[num], recordVal)
            else:
                removeRow(msagEDIT, userFieldName[num], recordVal)
        elif field in deleteList:
            print(strField + " field is being removed")
            arcpy.DeleteField_management(msagEDIT, userFieldName[num])
            print("Deleted " + strField)
        else:
            print(strField + " doesn't need anything removed")
    else:
        print(strField + " is not in user's table...")

#removes fields C1-C20 if they exist
try:
    for i in range(20):
        arcpy.DeleteField_management(msagEDIT, "C" + str(i + 1))
except Exception:
    pass

#searches the streets field for any containing MM and deleting the record if it does
msagEDITRows = arcpy.da.UpdateCursor(msagEDIT, activeDict["StreetName"])
for row in msagEDITRows:
    try:
        temp = row[0]
        if temp[0:2] == "MM":
            msagEDITRows.deleteRow()
    except:
        print("StreetName record is empty")

#Checks if there is a zip field in the table and adds one if nope
if "Zip" not in activeDict.keys():
    arcpy.AddField_management(msagEDIT, "Zip", "TEXT", "", "", 50)
    activeDict.update({"Zip": "Zip"})
#calculate the zip code in the msag table by making it equal the postal community
zipCalc(msagEDIT, outLocation, str(activeDict["Community"]), str(activeDict["Zip"]))

#add three new text fields
arcpy.AddField_management(msagEDIT, "FULL_ST_NM", "TEXT", "", "", 50)
activeDict.update({"FULL_ST_NM": "FULL_ST_NM"})
arcpy.AddField_management(msagEDIT, "LOW_ADD", "TEXT", "", "", 50)
activeDict.update({"LOW_ADD": "LOW_ADD"})
arcpy.AddField_management(msagEDIT, "HIGH_ADD", "TEXT", "", "", 50)
activeDict.update({"HIGH_ADD": "HIGH_ADD"})

#make lists of the fields needed for the three new fields' calculation expression
needFields1 = ["PrefixDirectional", "StreetName", "StreetSuffix", "PostDirectional"]
needFields2 = ["HouseNumLow", "FULL_ST_NM"]
needFields3 = ["HouseNumHigh", "FULL_ST_NM"]

#run formula to calculate street name, low, and high
fieldCalc(needFields1, activeDict, msagEDIT, "FULL_ST_NM")
fieldCalc(needFields2, activeDict, msagEDIT, "LOW_ADD")
fieldCalc(needFields3, activeDict, msagEDIT, "HIGH_ADD")
print("Added and calculated FULL_ST_NM, LOW_ADD, and HIGH_ADD")

#geocode the low and high address ranges to create two new files
addrLoc = raw_input("Please enter the path to the address locator including the locator: ")
#replace backslashes with forward slashes to eliminate any accidental formatting
addrLoc = addrLoc.replace("\\", "/")

#spatial reference change see webpage for WKID: 
#https://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-classes/pdf/projected_coordinate_systems.pdf
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(2965)

#geocode the low and high addresses
lowOut = "lowGeo1"
addrFields = "Street LOW_ADD; ZIP Zip"
arcpy.GeocodeAddresses_geocoding(msagEDIT, addrLoc, addrFields, lowOut, 'STATIC')
highOut = "highGeo1"
addrFields = "Street HIGH_ADD; ZIP Zip"
arcpy.GeocodeAddresses_geocoding(msagEDIT, addrLoc, addrFields, highOut, 'STATIC')
print("Geocoding complete")

#repeat geocoding on newly editted data
print("Should a different address locator be used?  Enter the path if yes, otherwise hit enter")
addrInput = raw_input("Input: ")
if len(addrInput) > 0:
    addrLoc = addrInput.replace("\\", "/")


lowOut = "lowGeo2"
addrFields = "Street LOW_ADD; ZIP Zip"
arcpy.GeocodeAddresses_geocoding(msagEDIT, addrLoc, addrFields, lowOut, 'STATIC')
highOut = "highGeo2"
addrFields = "Street HIGH_ADD; ZIP Zip"
arcpy.GeocodeAddresses_geocoding(msagEDIT, addrLoc, addrFields, highOut, 'STATIC')
print("Geocoding complete")

#check to see if user wants to geocode again
answer = raw_input("Would you like to geocode again? Enter \"y\" to continue.  Otherwise, press enter ")
    
#if user wants to repeat geocoding, go through this loop
counter = 3
while answer == "y":
    print("Should a different address locator be used?  Enter the path if yes, otherwise hit enter")
    addrInput = raw_input("Input: ")
    if len(addrInput) > 0:
        addrLoc = addrInput.replace("\\", "/")
    addrLoc = addrLoc.replace("\\", "/")
    lowOut = "lowGeo" + str(counter)
    addrFields = "Street LOW_ADD; ZIP Zip"
    arcpy.GeocodeAddresses_geocoding(msagEDIT, addrLoc, addrFields, lowOut, 'STATIC')
    highOut = "highGeo" + str(counter)
    addrFields = "Street HIGH_ADD; ZIP Zip"
    arcpy.GeocodeAddresses_geocoding(msagEDIT, addrLoc, addrFields, highOut, 'STATIC')
    print("Geocoding complete")
    counter += 1
    answer = raw_input("Would you like to geocode again? Enter \"y\" to continue.  Otherwise, press enter ")

#add fields X1 and Y1
env.qualifiedFieldNames = False
arcpy.AddField_management(highOut, "X1", "DOUBLE", 10, 3)
arcpy.AddField_management(highOut, "Y1", "DOUBLE", 10, 3)
print("Added X1 and Y1 fields")

#calculate X1 and Y1 as being equal to the x and y fields in the high geocoding file
arcpy.CalculateField_management(highOut, "X1", "!X!", "PYTHON_9.3")
arcpy.CalculateField_management(highOut, "Y1", "!Y!", "PYTHON_9.3")
print("Calculated X1 and Y1")

#join the low and high range geocoding results based on MsagId or user input
arcpy.MakeFeatureLayer_management(lowOut, "lowOutFC")
if "MsagId" in activeDict.keys():
    arcpy.AddJoin_management("lowOutFC", "MsagId", str(highOut) + ".dbf", "MsagId")
    msagID = activeDict["MsagId"]
else:
    success = False
    print("MsagId is not in this table.")
    while not success:
        msagID = raw_input("What field should be used to join the tables?")
        try:
            arcpy.AddJoin_management("lowOutFC", msagID, str(highOut) + ".dbf", msagID)
            success = True
        except:
            print("This field isn't in the table")
#rename table
arcpy.CopyFeatures_management("lowOutFC", "joinedOutput")
#move table to output location
arcpy.TableToTable_conversion("joinedOutput.dbf", outLocation, "joinedTable")
print("Joined the high table to the low table and saved result")

#run xy to line
env.workspace = outLocation
env.qualifiedFieldNames = False
env.overwriteOutput = True
#spatial reference change see webpage for WKID: 
#https://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-classes/pdf/projected_coordinate_systems.pdf
env.outputCoordinateSystem = arcpy.SpatialReference(2965)

outFC = str(outLocation) + "/xyLineOutput"
arcpy.XYToLine_management("joinedTable.dbf", outFC, "X", "Y", "X1", "Y1", "GEODESIC", msagID) 
print("XY to line is complete")
print("File is located at " + str(outLocation))

#write irregularities to a file and delete them
indata = "xyLineOutput.shp"
xyRows1 = arcpy.da.UpdateCursor(indata, ["X", msagID]) 
xyRows2 = arcpy.da.UpdateCursor(indata, ["X1", msagID])
f = open(str(outLocation) + "/irregularities.csv", "a")
for row in xyRows1:
    if int(row[0]) < 1:
        f.write(str(row[1])+",\n")
        xyRows1.deleteRow()

for row in xyRows2:
    if int(row[0]) < 1:
        f.write(str(row[1])+",\n")
        xyRows2.deleteRow()
#determine the new extent with the irregularities removed
arcpy.RecalculateFeatureClassExtent_management(indata) 

#delete not needed data
arcpy.Delete_management("toCountTEMP.csv")
arcpy.Delete_management("zipExp.csv")
arcpy.Delete_management("msagGDB.dbf")
arcpy.Delete_management("msagTableEDIT.dbf")
arcpy.Delete_management("msagTableEDIT.csv")

print("Code is finished.  Exiting program...")



