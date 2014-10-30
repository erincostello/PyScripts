# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~  CreateSSN_OBJ  ~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# The purpose of this script is to reformat a LSN as .ssn object.
# The script does a number of things: 1)a new folder is created
# for the .ssn object, 2) assigns a binary ID to edges in 
# a LSN featureclass, 3) Exports the binary IDs 
# as text files. One text file is created for each stream network
# (i.e. netID1.dat, netID2.dat....), 4) A netID value is assigned to
# the edges and sites attribute table and 5) the edges and sites are
# exported as shapefiles. 
#
# ~~~~~~~~~~~~~~~~  Contact Information ~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~ Erin Peterson                                          ~~~~~
# ~~~ CSIRO Division of Comuptational Informatics            ~~~~~
# ~~~e-mail: Erin.Peterson@csiro.au                          ~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Created by: Erin Peterson 09/25/09
# Last Modified: 03/23/14

# Create the geoprocessor
import arcgisscripting, sys, string, os, re, time, win32com.client, win32api, shutil, os.path 
from time import *


# Create the Geoprocessor object
gp = arcgisscripting.create()

conn1 = win32com.client.Dispatch(r'ADODB.Connection')

try:

##    
    edgesFC = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN04\lsn.mdb\edges"  # Input Feature Class
    sitesFC = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN04\lsn.mdb\sites"
    idField = "STATION_KE"
    predsFCList = "#"
    #predsFCList = "d:\\projects\\john\\lsns\\lsn.mdb\\preds"

    #edgesFC = sys.argv[1]
    #sitesFC = sys.argv[2]
    #idField = sys.argv[3]
    #predsFCList = sys.argv[4]

    if predsFCList != "#":   
        predsFCList = predsFCList.split(';')    
    else:
        predsFCList = ""

##    if idField == "#":
##        idField = "OBJECTID"
        
    Path = gp.Describe(edgesFC).Path    # Get the full path of the featureclass this includes PGDB name
    #OutputFilePath = os.path.dirname(Path)
    gp.Workspace = Path                                            #set work space = to featureclass path
    DSN = 'PROVIDER=Microsoft.Jet.OLEDB.4.0;DATA SOURCE=' + Path
    conn1.Open(DSN)  
    
    SitesFCName = gp.Describe(sitesFC).Name
    EdgesFCName = gp.Describe(edgesFC).Name
    RelTableName = "relationships"
    
    gp.MakeFeatureLayer(EdgesFCName,"edgeLyr")
    
    ############################################################################
    # Create a new folder for SSN Object
    ############################################################################
    gp.Addmessage("Creating new folder for SSN object")
    gp.Addmessage(" ")
    #print("Creating new folder for SSN object")
    #print(" ")

    
    # Get path where new folder is to be created
    newFolderPath = os.path.dirname(gp.Describe(edgesFC).Path)

    #Get new folder name
    newFolderName = os.path.basename(os.path.dirname(edgesFC))[:-4] + ".ssn"
    
    #check to see whether folder already exists
    fileList = os.listdir(newFolderPath)

    for name in fileList:
        if name == newFolderName:
            shutil.rmtree(newFolderPath + "\\" + newFolderName)
    
    #Make new directory
    os.makedirs(newFolderPath + "\\" + newFolderName)

    #Set OutputFilePath
    OutputFilePath = newFolderPath + "\\" + newFolderName


    #############################################################################
    # Create Binary Segment ID
    ############################################################################# 
    gp.Addmessage("Creating Binary Segment IDS and NetID values")
    gp.Addmessage(" ")
    #print("Creating Binary Segment IDS and NetID values")
    #print(" ")

    # look and see if the table valence exists, if it does then delete it    
    tbs = gp.ListTables(RelTableName)
    tb = tbs.next()

    if tb: # IF ReltableName exists then 
        rs = win32com.client.Dispatch(r'ADODB.Recordset')
        rs1 = win32com.client.Dispatch(r'ADODB.Recordset')
        querystring = "SELECT First(relationships.OBJECTID) AS FirstOfOBJECTID, relationships.tofeat AS fromfeat, relationships.fromfeat AS tofeat FROM (relationships LEFT JOIN " + EdgesFCName + " ON relationships.fromfeat = " + EdgesFCName + ".rid) LEFT JOIN " + EdgesFCName + " AS " + EdgesFCName + "_1 ON relationships.tofeat = " + EdgesFCName + "_1.rid GROUP BY relationships.tofeat, relationships.fromfeat ORDER BY First(relationships.OBJECTID) DESC;"

       
        #To list database fields in rs:---------------------------------------
##        for x in range(rs.Fields.Count): 
##...         #print rs.Fields.Item(x).Name 

        # rs: creates a database with 3 Fields: FirstOfOBJECTID, fromfeat (tofeat in relationships), 
        # tofeat (fromfeat in relationships. The table is sorted and grouped so that you start
        # with an outlet segment. As you move through the rows, you are moving upstream. 
        rs.Open(querystring, conn1, 1) 
        rs.MoveFirst
        count = 0


        FeatureList = [] # this list holds feature IDs that have been added or accumulated
        BinaryList = [] # this list holds add or accumulated feature values
        NetIdList = []
        fromFeatCount = [0]* gp.GetCount("edgeLyr")
        netID = 0
        featCount = 0
        
        gp.AddMessage(" ")
        #gp.AddMessage("Accumulating Upstream....")
        gp.AddMessage(" ")
        ##print "Accumulating upstream"
        while not rs.EOF:
            #get from feature
            fromfeat = rs.Fields.Item("fromfeat").Value
##            #print "fromfeat = " + str(fromfeat)
            #get to feature
            tofeat = rs.Fields.Item("tofeat").Value
##            #print "tofeat = " + str(tofeat)
##            print " "

            toexists = tofeat in FeatureList
            fromexists = fromfeat in FeatureList

            #---------------------------------------------------------------------------------------
            # If fromexists == 0, it is the start of a new network
            #-----------------------------------------------------------------------------------------
            if fromexists == 0: # if fromfeature not in list add it and add its weight value to accumulate list
            
########################################################################################################
## This should be added for single features
                FeatureList.append(fromfeat)
                BinaryList.append("1")                
                #print "outlet rid = " + str(fromfeat)
                netID = netID + 1
                NetIdList.append(netID)
#######################################################################################################
                ind2 = FeatureList.index(fromfeat)
               
##                print "fromfeat = " + str(fromfeat)
##                print "NetID = " + str(netID)
##                print "BinaryID = " + str(BinaryList[ind2])
                
                
            if toexists == 1: #These are errors that should never happen
##                print "fromfeat = " + str(fromfeat)
##                print "tofeat = " + str(tofeat)
##                print "toFeatCount = " + str(toFeatCount)
                                
                ind = FeatureList.index(tofeat)
                if fromexists == 1: 
                    #fromexists = 1, toexists = 1 THIS SHOULD NEVER HAPPEN
                    gp.AddWarning("Error - TO rid " + str(tofeat) + " and FROM rid " + str(fromfeat) + " have already been recorded")
                    print("Error - TO rid " + str(tofeat) + " and FROM rid " + str(fromfeat) + " have already been recorded")
                    sys.exit()
                    
                else:
                    # fromexists = 0, toexists = 1 THIS SHOULD NEVER HAPPEN                 
                    gp.AddWarning("Topological error - TO rid " + str(tofeat) + " recorded before FROM rid " + str(fromfeat))
                    print("Topological error - TO rid " + str(tofeat) + " recorded before FROM rid " + str(fromfeat))
                    sys.exit()

            #----------------------------------------------------------------------------
                #fromexists = 1, toexists = 0
                #Case 1: fromfeat added as a tofeat
                #Case 2: fromfeat added as tofeat or another fromfeat....
            #----------------------------------------------------------------------------
            else:
                
                FeatureList.append(tofeat)
                if fromexists == 1:
                    ind2 = FeatureList.index(fromfeat)
                            
                    fromFeatCount[ind2] = fromFeatCount[ind2]+ 1
                    NetIdList.append(netID)

                    if fromFeatCount[ind2] == 1:
                        BinaryList.append(BinaryList[ind2] + "0")
                    else:
                        BinaryList.append(BinaryList[ind2] + "1")
                    

                    if fromFeatCount[ind2] > 2:
                        gp.AddMessage("ERROR: rid " + str(tofeat) + " is part of a converging confluence with > 2 upstream segments")
                        print("ERROR: edge rid " + str(tofeat) + " is part of a converging confluence with > 2 upstream segments")
                        sys.exit()

                #----------------------------------------------------------------------       
                #fromexists = 0, toexists = 0, fromfeat is an Outlet
                #----------------------------------------------------------------------
                else:
                    ind2 = FeatureList.index(fromfeat)
                    fromFeatCount[ind2] = fromFeatCount[ind2] + 1                    

                    if fromFeatCount[ind2] == 1:
                        BinaryList.append(BinaryList[ind2] + "0")
                    else:
                        BinaryList.append(BinaryList[ind2] + "1")                    

                    NetIdList.append(netID)

                    
            rs.MoveNext()
        rs.Close()

        #Clean up-------------------------------------------------------------
        rs = "Nothing"
        conn1.Close()
        gp.RefreshCatalog(Path)        

        #############################################################################
        # Write out binary segment IDS and add NetID to edges attribute table
        #############################################################################
        gp.Addmessage("Writing Binary Segment IDS to file")
        gp.Addmessage("Adding NetID to edges attribute table")
        gp.Addmessage(" ")
        print("Adding Binary Segment IDs to file")
        print("Adding NetID to edges attribute table")
        print(" ")

           
        if gp.ListFields("edgeLyr", "netID").Next():
            gp.AddMessage("Populating Field netID....")
            gp.DeleteField("edgeLyr", "netID")
            gp.Delete("edgeLyr")
            print("deleted field and edgeLyr")
            gp.MakeFeatureLayer(edgesFC, "edgeLyr")
            gp.AddField("edgeLyr", "netID", "long")      
        else:
            gp.AddMessage("Populating Field netID ....")
            gp.AddField("edgeLyr", "netID", "long")
        gp.AddMessage(" ")


        print("Finished add field")
        
        oldNetId = 1
        ofh = open(OutputFilePath + "\\netID" + str(oldNetId) + ".dat", "w")
        ofh.write('"rid", "binaryID"' + "\n")
         
        for FID in FeatureList:
            querystring = "rid = " + str(FID)
            ind2 = FeatureList.index(FID)

            newNetId = NetIdList[ind2]

            if newNetId != oldNetId:
                #if this is the first write to file instance
                if ofh.closed == 1:
                    ofh = open(OutputFilePath + "\\netID" + str(newNetId) + ".dat", "w")
                    ofh.write('"rid", "binaryID"' + "\n")
                #if a new netID file is started
                else:
                    ofh.close()
                    ofh = open(OutputFilePath + "\\netID" + str(newNetId) + ".dat", "w")
                    ofh.write('"rid", "binaryID"' + "\n")
           
            ofh.write(str(FID) + "," + str(BinaryList[ind2]) + "\n")
            
            Rows = gp.UpdateCursor(EdgesFCName, querystring)
            Row = Rows.Next()
            while Row:
                Row.SetValue("netID", NetIdList[ind2])
                Rows.UpdateRow(Row)
                Row = Rows.Next()

            oldNetId = newNetId
        
###################################################################################
        #Check for missng netIDs here 
###################################################################################
        # select edges with NULL netID values - these have not been assigned binary IDs
        print("checking for missing netIDs")
        querystring = "netID is null"
        Rows = gp.UpdateCursor(EdgesFCName, querystring)
        Row = Rows.Next()

        gp.MakeTableView(RelTableName,"Relate")
        gp.MakeTableView("noderelationships","NodeRelate")

        while Row:
            missRid = Row.GetValue("rid")

            #Query relationships table to make sure that rid is not recorded in fromfeat
            querystring = "fromfeat = " + str(missRid)
            gp.SelectLayerByAttribute("Relate", "NEW_SELECTION", querystring)
            count = gp.GetCount("Relate")

            # If fromfeat = rid is recorded in relationships table then an error has occured
            if count > 0:
                gp.AddWarning("Error - RID " + str(missRID) + " is found in the relationships table, but wasn't assigned a binary ID")
                print("Error - RID " + str(missRID) + " is found in the relationships table, but wasn't assigned a binary ID")
                sys.exit()

            #Query noderelationships table to ensure that the rid is recorded there
            querystring = "rid = " + str(missRid)
            gp.SelectLayerByAttribute("NodeRelate", "NEW_SELECTION", querystring)
            count = gp.GetCount("NodeRelate")

            #If rid is not recorded in noderelationships table, then an error occurred - all edge rids should be recorded here.
            if count == 0:
                gp.AddWarning("Error - RID " + str(missRID) + " is not found in the relationships tables")
                print("Error - RID " + str(missRID) + " is found in the relationships tables")
                sys.exit()

            # Add network information for single edge features
            FeatureList.append(missRid)
            BinaryList.append("1")                
            #print "outlet rid = " + str(fromfeat)
            netID = oldNetId + 1
            NetIdList.append(netID)

            oldNetId = netID
            ofh = open(OutputFilePath + "\\netID" + str(oldNetId) + ".dat", "w")
            ofh.write('"rid", "binaryID"' + "\n")          
            ofh.write(str(missRid) + ", 1 \n")

            Row.SetValue("netID", oldNetId)
            Rows.UpdateRow(Row)
            Row = Rows.Next()
                               
        ofh.close() # close file
        gp.Delete("edgeLyr")
        del(Rows, Row, querystring)




        #############################################################################
        # Add length field to edges attribute table
        #############################################################################
        if gp.ListFields(EdgesFCName, "Length").Next():
            gp.AddMessage("Length field exists....")
            print("length field exists")
        else:
            gp.AddField(EdgesFCName, "Length", "FLOAT")
            print("added Length field")
        gp.AddMessage(" ")

        #shapefile = r"C:\temp\test.shp"
        #gp.AddField_management(shapefile, "SHAPE_LENGTH", "DOUBLE")
        query = "float(!SHAPE.LENGTH!)"
        gp.CalculateField(EdgesFCName, "Length", query, "PYTHON")        
      

        #############################################################################
        # Add locID to sites attribute table
        #############################################################################
        gp.AddMessage("Populating locID in sites attribute table")

        gp.AddMessage(" ")
        print("Populating locID in sites attribute table")
        gp.AddMessage("idField = " + idField)


##        Path = gp.Describe(sitesFC).Path    # Get the full path of the featureclass this includes PGDB name
##        #OutputFilePath = os.path.dirname(Path)
##        gp.Workspace = Path                                            #set work space = to featureclass path
##        DSN2 = 'PROVIDER=Microsoft.Jet.OLEDB.4.0;DATA SOURCE=' + Path
##        conn2.Open(DSN)  
        
        if idField != "#":
            gp.AddMessage(idField)
            
            #SitesFCName = gp.Describe(sitesFC).Name
            #gp.MakeFeatureLayer(SitesFCName,"siteLyr")

            gp.MakeTableView(SitesFCName, "siteTable")

            if gp.ListFields("siteTable", idField).Next():
            #if gp.ListFields(SitesFCName, idField).Next():    
                gp.AddMessage("ID field exists...")
            else:
                gp.AddMessage("ID field does not exist")
                sys.exit("ID field does not exist")

            # Add locID to sites attribute table
            gp.AddMessage("Adding locID to sites attribute table")
            gp.AddMessage(" ")
            print("Adding locID to sites attribute table")
            print(" ")

            #gp.Delete("siteTable")

    ####################################################################
            #MUST SORT SITELYR BY ID FIELD
    ####################################################################

            gp.MakeFeatureLayer(SitesFCName,"siteLyr")
            gp.RefreshCatalog(Path) 

            if gp.ListFields(SitesFCName, "locID").Next():
                gp.AddMessage("locID Field exists...")

            else:
                #gp.AddField("siteLyr", "locID", "long")
                gp.AddField(SitesFCName, "locID", "long")
                gp.AddMessage("Added locID field....")

            gp.Delete("siteLyr")
            gp.RefreshCatalog(Path)
            
            gp.MakeFeatureLayer(SitesFCName,"siteLyr2")

            siteRows = gp.UpdateCursor("siteLyr2", "", "", "", idField)
            siteRow = siteRows.Next()
            
            gp.RefreshCatalog(Path)
            
            oldSiteID = siteRow.GetValue(idField)
           
            locID = 1

            siteRow.SetValue("locID", locID)
            siteRows.UpdateRow(siteRow)
            siteRow = siteRows.Next()
                       
            while siteRow:     
                newSiteID = siteRow.GetValue(idField)
                if oldSiteID != newSiteID:
                    locID = locID + 1
                    oldSiteID = newSiteID
                
                siteRow.SetValue("locID", locID)
                siteRows.UpdateRow(siteRow)
                siteRow = siteRows.Next()
                
            #Clean up
            #siteCount = gp.GetCount("siteLyr")
            gp.Delete("siteLyr2")
            del(siteRows, siteRow)
      
            ###########################################################################
            # Prediction files with the potential for multiples
            ###########################################################################

            if not predsFCList:
                gp.AddMessage("No prediction sites included")

            else:            
                i = 0
                while i < len(predsFCList):
                                 
                   predsFCName = predsFCList[i]
                   gp.AddMessage("predsFCName = " + predsFCName)
                   gp.MakeFeatureLayer(predsFCName,"predLyr")
                 
                   if gp.ListFields(predsFCName, "locID").Next():
                       gp.AddMessage("locID Field exists...")
                   else:
                       gp.AddField("predLyr", "locID", "long")
                       gp.AddMessage("Added locID field....")

                   if gp.ListFields(predsFCName, idField).Next():
                       #Must check for multiples
                       gp.AddMessage("ID Field exists...")

                       predRows = gp.UpdateCursor("predLyr", "", "", "", idField)
                       predRow = predRows.Next()                  

                       oldPredID = predRow.GetValue(idField)
                       locID = locID + 1

                       predRow.SetValue("locID", locID)
                       predRows.UpdateRow(predRow)
                       predRow = predRows.Next()

                       while predRow:
                           newPredID = predRow.GetValue(idField)

                           if oldPredID != newPredID:
                               locID = locID + 1
                               oldPredID = newPredID

                           predRow.SetValue("locID", locID)
                           predRows.UpdateRow(predRow)
                           predRow = predRows.Next()                
                        
                   else:
                       #No multiples
                       predRows = gp.UpdateCursor("predLyr")
                       predRow = predRows.Next()

                       locID = locID + 1

                       while predRow:
                           predRow.SetValue("locID", locID)
                           predRows.UpdateRow(predRow)
                           locID = locID + 1
                           predRow = predRows.Next()
                        
                   #Clean up
                   gp.Delete("predLyr")
                   i = i + 1
                
                del(predRows, predRow, i)
                
        #############################################################################
        # There are no multiples
        ############################################################################
        else: # There are no multiples 
            #conn1.Open(DSN)

            # Add locID to sites attribute table
            gp.AddMessage("Adding locID to sites attribute table")
            gp.AddMessage(" ")
            print("Adding locID to sites attribute table")
            print(" ")

            #SitesFCName = gp.Describe(sitesFC).Name   
                              
            gp.AddMessage("made FL siteLyr")
            if gp.ListFields(SitesFCName, "locID").Next():
                gp.AddMessage("listed fields and field exists")
                gp.AddMessage("locID Field exists...")
            else:
                gp.AddMessage("right before locID addField")
                gp.AddField(SitesFCName, "locID", "long")
                gp.AddMessage("Added locID field....")

            gp.AddMessage("beyond list field")
            gp.MakeFeatureLayer(SitesFCName,"siteLyr") 
            siteRows = gp.UpdateCursor("siteLyr")
            siteRow = siteRows.Next()

            locID = 1

            while siteRow:
                siteRow.SetValue("locID", locID)
                siteRows.UpdateRow(siteRow)
                locID = locID + 1
                siteRow = siteRows.Next()
            gp.AddMessage("Updated siteRow")
            gp.Delete("siteLyr")
            
            ###########################################################################
            # Prediction files without the potential for multiples
            ###########################################################################

            if not predsFCList:
                gp.AddMessage("No prediction sites included")

            else:            
                i = 0
                while i < len(predsFCList):
                                 
                   predsFCName = predsFCList[i]
                   gp.AddMessage("predsFCName = " + predsFCName)
                   
                 
                   if gp.ListFields(predsFCName, "locID").Next():
                       gp.AddMessage("locID Field exists...")
                   else:
                       gp.AddField(predsFCName, "locID", "long")
                       gp.AddMessage("Added locID field....")

                   gp.MakeFeatureLayer(predsFCName,"predLyr")
                   predRows = gp.UpdateCursor("predLyr")
                   predRow = predRows.Next()

                   locID = locID + 1

                   while predRow:
                       predRow.SetValue("locID", locID)
                       predRows.UpdateRow(predRow)
                       locID = locID + 1
                       predRow = predRows.Next()
                        
                   #Clean up
                   gp.Delete("predLyr")
                   i = i + 1
                
                del(predRows, predRow, i)
        #conn2.Close()

        
        #############################################################################
        # Add NetID and pid to sites attribute table
        #############################################################################        
        gp.AddMessage("Populating NetID in sites attribute table")
        gp.AddMessage(" ")
        print("Populating NetID in sites attribute table")
        print(" ")

        SiteRIDList = []
        SiteNetID = []

        #SitesFCName = gp.Describe(sitesFC).Name   
        
##########################################################################
        if gp.ListFields(SitesFCName, "netID").Next():
            gp.AddMessage("NetID exists...")
        else:
            gp.AddField(SitesFCName, "netID", "long")
            gp.AddMessage("Added NetID field....")


        if gp.ListFields(SitesFCName, "pid").Next():
            gp.AddMessage("pid Field exists...")
        else:
            gp.AddField(SitesFCName, "pid", "long")
            gp.AddMessage("Added pid field....")

        gp.MakeFeatureLayer(SitesFCName,"siteLyr")            
        siteRows = gp.UpdateCursor("siteLyr")
        siteRow = siteRows.Next()
        while siteRow:
            siteRID = siteRow.GetValue("rid")
            sitePID = siteRow.GetValue("OBJECTID")
            
            ind2 = FeatureList.index(siteRID)
            netID = NetIdList[ind2]
            
            siteRow.SetValue("netID", netID)
            siteRow.SetValue("pid", sitePID)
            siteRows.UpdateRow(siteRow)
            siteRow = siteRows.Next()

        #Clean up
        siteCount = gp.GetCount("siteLyr")
        gp.Delete("siteLyr")

        #del(NetIdList, BinaryList, fromFeatCount, FeatureList)
        del(BinaryList, fromFeatCount)
        del(siteRows, siteRow)
        
        ###########################################################################
        # Prediction files
        ###########################################################################

        if not predsFCList:
            gp.AddMessage("No prediction sites were included in SSN Object")

        else:
            
            i = 0
            while i < len(predsFCList):
                            
               PredRIDList = []
               PredNetID = []

               predsFCName = predsFCList[i]
               gp.AddMessage("predsFCName = " + predsFCName)
                            
               if gp.ListFields(predsFCName, "netID").Next():
                   gp.AddMessage("NetID exists...")
               else:
                   gp.AddField(predsFCName, "netID", "long")
                   gp.AddMessage("Added NetID field....")

               if gp.ListFields(predsFCName, "pid").Next():
                   gp.AddMessage("pid Field exists...")
               else:
                   gp.AddField(predsFCName, "pid", "long")
                   gp.AddMessage("Added pid field....")

               gp.MakeFeatureLayer(predsFCName,"predLyr")                    
               predRows = gp.UpdateCursor("predLyr")
               predRow = predRows.Next()
               while predRow:
                   predRID = predRow.GetValue("rid")
                   predPID = predRow.GetValue("OBJECTID") + siteCount
                    
                   ind2 = FeatureList.index(predRID)
                   netID = NetIdList[ind2]
                    
                   predRow.SetValue("netID", netID)
                   predRow.SetValue("pid", predPID)
                   predRows.UpdateRow(predRow)
                   predRow = predRows.Next()

               #Clean up
               predCount = gp.GetCount("predLyr")
               siteCount = siteCount + predCount
               gp.Delete("predLyr")
               i = i + 1
            

            del(NetIdList,FeatureList)
            del(predRows, predRow, i)
                        

        ###########################################################################
        # Export feature classes to shapefiles
        ###########################################################################
        gp.AddMessage("Converting feature classes to shapefiles")
        gp.AddMessage("Be patient, this may take awhile.....")
        gp.AddMessage(" ")
        print("Converting feature classes to shapefiles")
        print("Be patient, this may take awhile.....")
        print(" ")
        
        gp.FeatureClassToShapefile(EdgesFCName + ";" + SitesFCName,OutputFilePath)
        if SitesFCName != "sites":    
            gp.rename(OutputFilePath + "\\" + SitesFCName + ".shp", OutputFilePath + "\\sites.shp")

        coordsys = OutputFilePath + "\\" + "edges.prj"

        coordExists = os.path.exists(coordsys)
        if coordExists:
            gp.defineprojection_management(OutputFilePath + "\\sites.shp", coordsys)        
       
        gp.AddMessage("Edges and observed sites converted successfully")

        if predsFCList: 
            gp.AddMessage("Converting prediction sites to shapefiles.....")
            gp.AddMessage(" ")
       
            i = 0
            while i < len(predsFCList):
                if i == 0:
                    string = predsFCList[i]
                else:
                    string = string + ";" + predsFCList[i]
                i = i + 1
                
            gp.FeatureClassToShapefile(string,OutputFilePath)

            predNames=[]
            predNames = string.split(';')

            i = 0
            if coordExists:
                while i < len(predNames):
                    tmp = []
                    tmp = predNames[i].split('\\')
                    predsShpName = tmp[len(tmp)-1] + ".shp"
                    gp.defineprojection_management(OutputFilePath + "\\" + predsShpName, coordsys)
                    i = i + 1

        gp.AddMessage("Prediction sites converted successfully")           

        
        ############################################################################
        # Finish up
        ############################################################################
        #endTime = datetime.datetime.now()
        
        gp.AddMessage(" ")
        gp.AddMessage(" ")
        gp.AddWarning("Successfully Finished Create SSN Object Script")
        print("Successfully Finished Create SSN Object Script")
        print(" ")
    #    print("Start time = " + startTime.strftime("%Y-%m-%d %H:%M:%S"))
     #   print("End time = " + endTime.strftime("%Y-%m-%d %H:%M:%S"))
        gp.AddMessage(" ")
        gp.AddMessage(" ")
        gp.AddMessage(" ")
    else:
        gp.AddMessage("Relationship table doesn't exist")

    
except:
    gp.AddWarning("ERROR: FAILED TO CREATE SSN OBJECT")
    print("ERROR: FAILED TO CREATE SSN OBJECT")
    if gp.Exists("edgeLyr"):
        gp.Delete("edgeLyr")
    if gp.Exists("siteLyr"):
        gp.Delete("siteLyr")
    if gp.Exists("predLyr"):
        gp.Delete("predLyr")
        
    print gp.GetMessages(0)
    print conn1.GetMessages()
    








    
    
    
