import argparse
import json
import math
import datetime
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

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

# haversine distance: https://www.movable-type.co.uk/scripts/latlong.html
def get_distance(a, b):
  i = a.find(",")
  lat1 = float(a[:i]) 
  lon1 = float(a[i+1:]) 
  i = b.find(",")
  lat2 = float(b[:i]) 
  lon2 = float(b[i+1:]) 

  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)
  dphi = math.radians(lat2 - lat1)
  dlambda = math.radians(lon2 - lon1) 

  a = math.sin(dphi/2) * math.sin(dphi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2) * math.sin(dlambda/2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)) 
  return 6371 * c

def get_route(nodeid, start, end):
  if nodeid == 101:
    return [nodepaths[101][0]]

  print "start", start, "end", end

  start = get_time(start)
  end = get_time(end)
  route = []
  time = (end - start).total_seconds()

  print "get_route", nodeid
  print "start time", start, "end time", end, "diff", time
  print nodepaths[nodeid]

  # time to travel between each point
  i = 0
  while time > 0:
    if i+1 >= len(nodepaths[nodeid]):
      route.append(nodepaths[nodeid][i])
      break

    print "i", i
    print "time left", time
    d = get_distance(nodepaths[nodeid][i], nodepaths[nodeid][i+1])
    print "distance", d
    t = d / nodevelocities[nodeid]
    print "time to travel this distance", t
    route.append(nodepaths[nodeid][i])
    if time - t <= 0:
      actual_d = d * time / t
      # add this distance to the current position in the direction pos_i -> pos_i+1
      # add this new point to the route

    time -= t
    i += 1

  return route

# Using Mercator Projection: https://matplotlib.org/basemap/users/merc.html
m = Basemap(projection='merc',llcrnrlat=51.520691,urcrnrlat=51.543877,\
            llcrnrlon=-0.168904,urcrnrlon=-0.144668,resolution='c')
m.drawcoastlines()
m.fillcontinents(color='coral',lake_color='aqua')
m.drawparallels(np.arange(-90.,91.,30.))
m.drawmeridians(np.arange(-180.,181.,60.))
m.drawmapboundary(fill_color='aqua')

xs = [-0.161837,-0.168247,-0.168230,-0.167499,-0.159788,-0.155579,-0.145723,-0.146355,-0.149200,-0.156022,-0.161837] 
ys = [51.54159,51.539064,51.534368,51.530447,51.526168,51.523623,51.525279,51.53104,51.536116,51.538872,51.54159]

m.plot(xs,ys,'o-', markersize=5, linewidth=1, latlon=True)

parser = argparse.ArgumentParser(description="Simulation Visualiser", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("file", type=argparse.FileType('r'), help="Simulation output to be visualised")
args = parser.parse_args()

nodepaths = {}
nodepaths[101] = ['51.525802,-0.148273'] 
nodepaths[501] = ['51.539107,-0.164588']
nodepaths[502] = ['51.540135,-0.162260']

nodestarttimes = {}
nodevelocities = {}

msgpath = [nodepaths[101][0]]

# Parse and print node paths
for line in args.file:
  line = line.replace("\n","")
  if "'points'" in line:
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
    
#    i = line.find("'start_datetime':"
#    nodestarttimes[nodeid]

    i = line.find("'velocity':") + 12
    j = line.find(",", i)
    velocity = line[:j]
    velocity = velocity[i:]
    nodevelocities[nodeid] = float(velocity)

    # let's say starttime is 0
    
  elif "101 0 gen" in line and not "---msg is" in line:
    k = line.find("path:") + 7
    l = line.find("}", k)
    path = line[:l]
    path = path[k:]

    print "path", path

    route = []
    currentnode = "101"
    receivetime = "08:00:00.000000"
    endofpath = False
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

      print "currentnode", currentnode
      print "transfertime", transfertime

      # now we want to get all points between receivetime and transfertime that currentnode travelled
      route.extend(get_route(int(currentnode), receivetime, transfertime))

      currentnode = nextnode
      receivetime = transfertime

      print "nextnode", nextnode

      if nextnode == "101":
        path = path.replace("101: (101,", "")

      if currentnode == "501" or currentnode == "502":
        route.append(nodepaths[int(currentnode)][0])
        endofpath = True

      # print "route", route

    xs = map(getx, route)
    ys = map(gety, route)
    m.plot(xs,ys,latlon=True) 

plt.title("Mercator Projection")
plt.show()
