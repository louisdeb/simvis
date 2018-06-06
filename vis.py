import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

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

plt.title("Mercator Projection")
plt.show()
