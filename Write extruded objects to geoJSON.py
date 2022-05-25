
import os
import json
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import ghpythonlib.components as gh
import itertools as iter


basePlane = rs.CreatePlane(rs.CreatePoint(0,0,0),rs.CreateVector(1,0,0),rs.CreateVector(0,1,0))

#Fix mesh to move down to 0.01 m
meshFixed = []
for i in mesh:
    meshFixed.append(rs.MoveObject(i,rs.CreateVector(0,0,-0.001)))

#join mesh function to extract height parameter of the common bounding box
def BoundingBoxHeight (meshList):
    joinedMesh = gh.MeshJoin(mesh)
    commonBBox = gh.BoundingBox(joinedMesh,basePlane)[0]
    deconstructedBox = gh.DeconstructBrep(commonBBox)[2]
    distance = rs.Distance(deconstructedBox[0],deconstructedBox[4])
    return distance

commonMeshHeight = int(BoundingBoxHeight(mesh))
#print (commonMeshHeight)

planeArray = []
for i in range(0,commonMeshHeight,4):
    planeArray.append(rs.CreatePlane(rs.CreatePoint(0,0,i),rs.CreateVector(1,0,0),rs.CreateVector(0,1,0)))

#Nested loops for intersect each mesh with plane array
sections = []
for m in mesh:
    for p in planeArray:
        sections.append(rg.Intersect.Intersection.MeshPlane(m,p))

#Remove None (Nulls in Grasshopper) from sections list
sectionList = list(filter(lambda x:x is not None, sections))

#Get points to write mesh
points = []
for i in sectionList:
    points.append(gh.Explode(i,True)[1])

#Polyline is just for visualize
polylineCurve = []
for i in points:
    polylineCurve.append(gh.PolyLine(i,True))

upperPoint = []
projectedPoint = []
for i in polylineCurve:
    point = gh.PolygonCenter(i)[0]
    deconstructX = gh.Deconstruct(point)[0]
    deconstructY = gh.Deconstruct(point)[1]
    projected = rs.CreatePoint(deconstructX,deconstructY,0)
    upperPoint.append(point)
    projectedPoint.append(projected)

#--------------------------------------------------------------------------------------------------------------

baseHeightToOperateOn = []
baseHeight = []
for uP,pP in zip(upperPoint,projectedPoint):
    distance = rs.Distance(uP,pP)
    baseHeightToOperateOn.append(distance)
    baseHeight.append(distance)
#print baseHeight

roundedBaseHeight = []
for i in baseHeight:
    roundedBaseHeight.append(round(i,2))


heightPolygons = []
for i in roundedBaseHeight:
    heightPolygons.append(i + 3.7)


roundedHeight = []
for i in heightPolygons:
    rounded = round(i,1)
    roundedHeight.append(rounded)
#print (roundedHeight)


#EAP should be gotten from reading geojson file
earthAncorPoint = gh.Heron.SetEarthAnchorPoint(True,lat,lon)

latPointsSections = []
lonPointsSections = []
for i in points:
    latPointsSections.append(gh.Heron.XYtoDecimalDegrees(i)[0])
    lonPointsSections.append(gh.Heron.XYtoDecimalDegrees(i)[1])

#Merge points to write it to GeoJSON
def merge_list(listA, listB):
    merged_list = []
    for i1, els1 in enumerate(listA):
        merged_list_ = []
        for i2, el1 in enumerate(els1):
            merged_list_.append([el1, listB[i1][i2]])
        merged_list.append(merged_list_)
    return merged_list

unitedPoints = merge_list(lonPointsSections,latPointsSections)

#--------------------------------------------------------------------------------------------------------------
#Writing parameters from geometry to geojson file

#unitedPoints to GeoJSON:

polygonPointCoordiantes = []
for point,h,bH in zip(unitedPoints,heightPolygons,baseHeight):
    result = {
            "type" : "Feature",
            "geometry" : {
            "type": "Polygon",
            "coordinates":
                        [point]
            },
            "properties": {
            "height":h,
            "base_height":bH,
            "color": "#c7c7c7"
            }
        }
    polygonPointCoordiantes.append(result)


#5.0. Сборка перед функцией dumps в GeoJSON:
result = {
        "type": "FeatureCollection",
        "features":
                polygonPointCoordiantes
        }

#6.0. Сборка файла GeoJSON
result = json.dumps(result)
#print (result)

#7.0 Директория для сохранения файла
completeName = os.path.join(pathToWrite, fileName + ".geojson")

#8.0 Запись файла в формат GeoJSON
file = open(completeName,'w')
file.write(result)
file.close()
