import argparse
import json
import math
import datetime
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from geopy.distance import vincenty
from datetime import timedelta

def getx(s):
  i = s.find(',') + 1
  s = s[i:]
  return float(s)

def gety(s):
  i = s.find(',')
  s = s[:i]
  return float(s)

def get_time(timestr):
  return datetime.datetime.strptime(timestr, "%H:%M:%S.%f")

def get_point(p):
  i = p.find(",")
  lat = float(p[:i])
  lon = float(p[i+1:])
  return (lat,lon)

def point_to_str(p):
  lat = p[0]
  lon = p[1]
  return str(lat) + ',' + str(lon)

def get_route(nodeid, origintime, start, end):
  if nodeid == 101:
    return [nodepaths[101][0]]

  path = nodepaths[nodeid]
  route = []

  origintime = get_time(origintime)
  start = get_time(start)
  end = get_time(end)
  
  print "start", start, "end", end, "origintime", origintime

  v = nodevelocities[nodeid]

  time_to_receive = start - origintime
  print "finding point at ttr", time_to_receive, "for node", nodeid

  i = 0
  while time_to_receive > timedelta(seconds=0):
    if i+1 == len(path):
      route.append(path[i])
      break

    p1 = get_point(path[i])
    p2 = get_point(path[i+1])
    d = vincenty(p1,p2).km
    t = timedelta(seconds=(d/v))

    if time_to_receive == t: #receive message at next point
      route.append(point_to_str(p2))
    elif time_to_receive < t: #receive message before next point
      origin_lat = p1[0]
      origin_lon = p1[1]
      diff_lat = p2[0]-p1[0]
      diff_lon = p2[1]-p1[1]
      dt = time_to_receive.total_seconds() / t.total_seconds()
      lat = origin_lat + diff_lat * dt
      lon = origin_lon + diff_lon * dt
      print "received at lat",lat,"lon",lon
      route.append(point_to_str((lat,lon)))

    i += 1
    time_to_receive -= t

  # now route is the first point at which the message is received 

  time_to_transfer = end - start

  print "ttt", time_to_transfer
  
  # deal with between receive and next point in path
  p1 = get_point(route[0])
  p2 = get_point(path[i])
  d = vincenty(p1,p2).km
  t = timedelta(seconds=(d/v))

  print "finding point at ttt", time_to_transfer, "for node", nodeid

  if time_to_transfer < t:
    origin_lat = p1[0]
    origin_lon = p1[1]
    diff_lat = p2[0]-p1[0]
    diff_lon = p2[1]-p1[1]
    dt = time_to_transfer.total_seconds() / t.total_seconds()
    lat = origin_lat + diff_lat * dt
    lon = origin_lon + diff_lon * dt
    route.append(point_to_str((lat,lon)))
  else:
    route.append(path[i])

  time_to_transfer -= t

  while time_to_transfer > timedelta(seconds=0):
    if i+1 == len(path):
      route.append(path[i])
      break

    p1 = get_point(path[i])
    p2 = get_point(path[i+1])
    d = vincenty(p1,p2).km
    t = timedelta(seconds=(d/v))

    if time_to_transfer == t:
      route.append(point_to_str(p2))
    elif time_to_transfer < t:
      origin_lat = p1[0]
      origin_lon = p1[1]
      diff_lat = p2[0]-p1[0]
      diff_lon = p2[1]-p1[1]
      dt = time_to_transfer.total_seconds() / t.total_seconds()
      lat = origin_lat + diff_lat * dt
      lon = origin_lon + diff_lon * dt
      route.append(point_to_str((lat,lon)))
    else:
      route.append(path[i+1])

    i += 1
    time_to_transfer -= t

  return route

# Using Mercator Projection: https://matplotlib.org/basemap/users/merc.html
m = Basemap(projection='merc',llcrnrlat=51.520691,urcrnrlat=51.543877,\
            llcrnrlon=-0.168904,urcrnrlon=-0.144668,resolution='c')
m.drawcoastlines()
m.fillcontinents(color='coral',lake_color='aqua')
m.drawparallels(np.arange(-90.,91.,30.))
m.drawmeridians(np.arange(-180.,181.,60.))
m.drawmapboundary(fill_color='aqua')

# regents park area
xs = [-0.161838,-0.168605,-0.164353,-0.167499,-0.159788,-0.155579,-0.145723,-0.146355,-0.149200,-0.155167,-0.161838]
ys = [51.541598,51.540245,51.534663,51.530447,51.526168,51.523623,51.525279,51.531048,51.536116,51.539630,51.541598]

m.plot(xs,ys,'o-', markersize=5, linewidth=1, latlon=True)

parser = argparse.ArgumentParser(description="Simulation Visualiser", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("file", type=argparse.FileType('r'), help="Simulation output to be visualised")
args = parser.parse_args()

# points of interest locations
nodepaths = {}
nodepaths[101] = ['51.525802,-0.148273'] 
nodepaths[501] = ['51.538216,-0.160815']
nodepaths[502] = ['51.538285,-0.159524']
nodepaths[503] = ['51.538300,-0.158339']
nodepaths[504] = ['51.538338,-0.156965'] 
nodepaths[505] = ['51.538360,-0.156011'] 

# destination area
xs = [-0.161500,-0.155266,-0.155266,-0.161500,-0.161500]
ys = [51.538882,51.538882,51.537620,51.537620,51.538882]

m.plot(xs,ys,'o-',markersize=5,linewidth=1,latlon=True)

nodestarttimes = {}
nodevelocities = {}

msgpath = [nodepaths[101][0]]

for line in args.file:
  line = line.replace("\n","")
  if "'points'" in line:
    # now inspecting node paths
    g = line.find("'rental_id'") + 13
    h = line.find(",", g)
    nodeid = line[:h]
    nodeid = nodeid[g:]
    nodeid = int(nodeid)
 
    i = line.find("'points':") + 11
    j = line.find(", '", i) - 1
    points = line[:j]
    points = points[i:]
    points = points.replace(", -", ",-").replace(")","").replace("(","")
    coords = points.split(", ")
    nodepaths[nodeid] = coords
    
    i = line.find("'velocity':") + 12
    j = line.find(",", i)
    velocity = line[:j]
    velocity = velocity[i:]
    nodevelocities[nodeid] = float(velocity)

  elif "101 0 gen" in line and not "---msg is" in line:
    # now inspecting msg hop output
    k = line.find("path:") + 7
    l = line.find("}", k)
    path = line[:l]
    path = path[k:]

    print "path", path

    route = []
    currentnode = "101"
    origintime = "08:00:00.000000"
    receivetime = origintime
    endofpath = False
    index = 0
    while not endofpath:
      if not currentnode + "," in path:
        break

      i = path.find(currentnode + ",") - 3
      nextnode = path[:i]
      j = nextnode.rfind(", ") + 2
      if j == 1:
        j = 0
      nextnode = nextnode[j:]

      i = path.find(",", i) + 2
      j = path.find(")", i)
      transfertime = path[:j]
      transfertime = transfertime[i:]

      partroute = get_route(int(currentnode), origintime, receivetime, transfertime)
      if index > 0:
        prevroute = route[index-1]
        nextpoint = [partroute[0]]
        prevroute = prevroute + nextpoint
        route[index-1] = prevroute

      index = index + 1
      route.append(partroute)
    
      currentnode = nextnode
      receivetime = transfertime

      # fix parse issue where we keep getting 101 as next node due to msg creation
      if nextnode == "101":
        path = path.replace("101: (101,", "")

      if currentnode in ["501", "502", "503", "504", "505"]:
        print "arrived at basestation", currentnode
        prevpoint = route[index-1][len(route[index-1])-1]
        partroute = [prevpoint, nodepaths[int(currentnode)][0]]
        route.append(partroute)
        endofpath = True

    # print single coloured message
    wholeroute = []
    for partroute in route:
      wholeroute.extend(partroute) 
    xs = map(getx, wholeroute)
    ys = map(gety, wholeroute)
    #m.plot(xs,ys,latlon=True)

    # print multicoloured message
    for partroute in route:
      while len(partroute) < 3:
        partroute = partroute + [partroute[len(partroute)-1]]
      xs = map(getx, partroute)
      ys = map(gety, partroute)
      m.plot(xs,ys,latlon=True) 

plt.title("Mercator Projection")
plt.show()
