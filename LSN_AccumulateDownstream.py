
#######################################################################################
# This script iterates through table columns from and input and feed it to 
# the ACCUMULATE VALUE DOWNSTREAM script that was copied from the STARS 2.0.0 toolbox.
# 
# v1.0
# Ryan Michie
#######################################################################################

import arcgisscripting
import sys 
import string
import os
import re
import time
import win32com.client
import win32api
from time import *
from collections import defaultdict
import arcpy

#edgetable = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN04\Tables.mdb\edges"
edgefc = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN04\lsn.mdb\edges"

def AccumulateDownstream(InputFC, edgefields):
        
    # Create the Geoprocessor object
    gp = arcgisscripting.create()
    conn = win32com.client.Dispatch(r'ADODB.Connection')    


    for OutField in edgefields:
        
        AccField = "A" + str(OutField.name)
        SplitWeightField = "#"
        
        try:
    
            Path = gp.Describe(InputFC).Path    # Get the full path of the featureclass this includes PGDB name
            FeatureclassPath = Path
            PGDBName = os.path.basename(Path)                               # Get the PGDB full name from Featureclasspath
            FullFeatureclassPath = Path
            gp.AddMessage(Path)
        
        
            gp.Workspace = Path                                            #set work space = to featureclass path
            DSN = 'PROVIDER=Microsoft.Jet.OLEDB.4.0;DATA SOURCE=' + Path
            conn.Open(DSN)
        
            FeatureclassName = gp.Describe(InputFC).Name
            RelTableName = "relationships"
            # AccField = "shape_length"
        
            # look and see if the table valence exists, if it does then delete it    
            tbs = gp.ListTables(RelTableName)
            tb = tbs.next()
        
            if tb: # IF ReltableName exists then 
                rs = win32com.client.Dispatch(r'ADODB.Recordset')
                rs1 = win32com.client.Dispatch(r'ADODB.Recordset')
                # rs_name = RelTableName
                if SplitWeightField <> "#":
                    querystring = "SELECT First(relationships.OBJECTID) AS FirstOfOBJECTID, relationships.fromfeat, Sum(" + FeatureclassName + "." + AccField + ") AS from_value, relationships.tofeat, Sum(" + FeatureclassName + "_1." + AccField + ") AS to_value, Min(" + FeatureclassName + "." + SplitWeightField + ") AS split FROM (relationships LEFT JOIN " + FeatureclassName + " ON relationships.fromfeat = " + FeatureclassName + ".rid) LEFT JOIN " + FeatureclassName + " AS " + FeatureclassName + "_1 ON relationships.tofeat = " + FeatureclassName + "_1.rid GROUP BY relationships.fromfeat, relationships.tofeat ORDER BY First(relationships.OBJECTID);"
                else:
                    querystring = "SELECT First(relationships.OBJECTID) AS FirstOfOBJECTID, relationships.fromfeat, Sum(" + FeatureclassName + "." + AccField + ") AS from_value, relationships.tofeat, Sum(" + FeatureclassName + "_1." + AccField + ") AS to_value FROM (relationships LEFT JOIN " + FeatureclassName + " ON relationships.fromfeat = " + FeatureclassName + ".rid) LEFT JOIN " + FeatureclassName + " AS " + FeatureclassName + "_1 ON relationships.tofeat = " + FeatureclassName + "_1.rid GROUP BY relationships.fromfeat, relationships.tofeat ORDER BY First(relationships.OBJECTID);"
                #gp.AddMessage(querystring)
                rs.Open(querystring, conn, 1) 
                rs.MoveFirst
                count = 0
                # loop through the recordset and accumulate value down stream.  This can be done because the table is sorted downstream
                FeatureList = [] # this list holds feature IDs that have been add or accumulated
                AccumulateValueList = [] # this list holds add or accumulated feature values
                gp.AddMessage(" ")
                gp.AddMessage("Accumulating Downstream....")
                gp.AddMessage(" ")
                splitweight = 1
                while not rs.EOF:
                    if SplitWeightField <> "#":
                        splitweight = rs.Fields.Item("split").Value
                        if not splitweight:
                            if splitweight <> 0:splitweight = 1
        
                    fromfeat = rs.Fields.Item("fromfeat").Value
                    tofeat = rs.Fields.Item("tofeat").Value
                    fromvalue = rs.Fields.Item("from_value").Value
        
                    #gp.AddMessage(str(fromfeat) + " " + str(fromvalue))
        
                    if not fromvalue:
                        fromvalue = 0
                    tovalue = rs.Fields.Item("to_value").Value
                    if not tovalue:
                        tovalue = 0
                    toexists = tofeat in FeatureList
                    fromexists = fromfeat in FeatureList
                    if fromexists == 0: # if fromfeature not in list add it and add its weight value to accumulate list
                        FeatureList.append(fromfeat)
                        AccumulateValueList.append(fromvalue)
                    if toexists == 1: # if tofeature exists in list accumulate it
                        ind = FeatureList.index(tofeat)
                        if fromexists == 1: # if fromfeature and tofeature exist in list add fromfeature's list value to to node value
                            ind2 = FeatureList.index(fromfeat)
                            AccumulateValueList[ind] = (float(AccumulateValueList[ind2] * splitweight) + AccumulateValueList[ind])
                        else:
                            AccumulateValueList[ind] = AccumulateValueList[ind] + float(fromvalue * splitweight)
                    else:
                        FeatureList.append(tofeat)
                        if fromexists == 1:
                            ind2 = FeatureList.index(fromfeat)
                            AccumulateValueList.append(float(AccumulateValueList[ind2] * splitweight) + tovalue)
                        else:
                            AccumulateValueList.append(tovalue + float(fromvalue * splitweight))
                    rs.MoveNext()
                rs.Close()
                rs = "Nothing"
                #time.sleep(4.0)
                conn.Close()
        
                if gp.ListFields(FeatureclassName, OutField).Next():
                    gp.AddMessage("Populating Field " + OutField + "...")
                else:
                    gp.AddMessage("Populating Field " + OutField + "....")
                    gp.AddField(FeatureclassName, OutField, "double")
                    #gp.AddMessage("field added")
                gp.AddMessage(" ")
                string = AccField + " IS NOT NULL"
                gp.SelectLayerByAttribute(FeatureclassName, "ADD_TO_SELECTION", string)
                calcfield =  "[" + AccField + "]"
                gp.CalculateField(FeatureclassName, OutField, calcfield)
                gp.SelectLayerByAttribute(FeatureclassName, "CLEAR_SELECTION")
                #gp.CalculateField(FeatureclassName, OutField, "0")
                gp.AddMessage("Field Calculated")
        
                Rows = gp.UpdateCursor(FeatureclassName)
                Row = Rows.Next()
                while Row:
                    rid = Row.rid
                    exists = rid in FeatureList
                    if exists > 0:
                        ind = FeatureList.index(rid)
                        Row.SetValue(OutField, AccumulateValueList[ind])
                        #gp.AddMessage(str(rid) + "   " + str(AccumulateValueList[ind]))
                        del FeatureList[ind]
                        del AccumulateValueList[ind]
                        Rows.UpdateRow(Row)
                    Row = Rows.Next()
        
                gp.AddMessage("  ")
                gp.AddMessage("  ")
                gp.AddWarning("Finished Accumulate Values Downstream Script")
                gp.AddMessage("  ")
                gp.AddMessage("  ")
                gp.AddMessage("  ")
            else:
                gp.AddMessage("Relationship table doesn't exist")
        except:
            print gp.GetMessages(0)
            print conn.GetMessages()

fields = arcpy.ListFields(edgefc,"*","All")

excludefields = [u"OBJECTID", u"Shape", u"arcid", u"from_node", u"to_node", u"HydroID", u"GridID", 
                 u"NextDownID", u"DrainID", u"rid", u"Shape_Length", u"fishpres",
                 u"RCASQM", u"RSASQM", u"RCACOUNT", u"RSACOUNT", u"RCANASQM", u"RCANACOUNT", u"EDGELEN",
                 u"ARCASQM", u"ARSASQM", u"ARCACOUNT", u"ARSACOUNT", u"ARCANASQM", u"ARCANACOUNT", u"AEDGELEN",
                 ]
edgefields = []

for field in fields:
    if field.name not in excludefields:
        edgefields.append(field)  

AccumulateDownstream(edgefc, edgefields)