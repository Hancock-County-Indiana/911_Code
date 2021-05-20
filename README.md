# Code
Publicly available code

This is a repository for various python code that's used to automate geospatial processes that support 911.

The fishbone_v1.1.py code automates the process outlined in the Appendix D - Fishbone Analysis Word document which shows how to create a fishbone analaysis in ArcGIS.  The final output (outFish shapefile) should provide the same results one would get if following the steps in Appendix D.  

The msag-centerline_v1.1 code automates the process outlined in the msag-centerline-Reconcilitaion PDF file which shows how to visualize discrepencies between the road centerlines (RCL) and the master street address guide (MSAG).  The final output produces a .csv file with the records that were removed due to their irregularity, the .dbf of the high and low ranges of the MSAG joined together, the MSAG data in vector-line format, and a geodatabase containing the low and high geocode results for the MSAG along with them joined together and the original MSAG table.
