QGIS Cartogram
==============

[![Code Climate](https://codeclimate.com/github/informeren/qgis-cartogram/badges/gpa.svg)](https://codeclimate.com/github/informeren/qgis-cartogram)

A QGIS plugin for creating cartograms based on polygon layers.

This plugin is an updated version of the [cartogram plugin](https://github.com/carsonfarmer/cartogram) by Carson Farmer which is based on an algorithm proposed in the following paper:

> Dougenik, J. A, N. R. Chrisman, and D. R. Niemeyer. 1985. "An algorithm to construct continuous cartograms." Professional Geographer 37:75-81 

![Cartogram created from the included demo data](https://github.com/informeren/qgis-cartogram/raw/develop/assets/cartogram.png)

This plugin is based on the template provided by the [Plugin Builder](https://plugins.qgis.org/plugins/pluginbuilder/) QGIS plugin.


Try it out
----------

To see the plugin in action simply import the demo data included with the plugin (*Vector → Cartogram → Add demo layer*). Then you can click the Cartogram button on the toolbar or select *Vector → Cartogram → Create cartogram*.

![Configure the cartogram creator](https://github.com/informeren/qgis-cartogram/raw/develop/assets/screenshot-setup.png)

Select the newly added demo layer and the *VOTERS* field and set the number of iterations to 5. When you click OK the cartogram will be generated in the background.

![Cartogram being generated](https://github.com/informeren/qgis-cartogram/raw/develop/assets/screenshot-working.png)

When the cartogram has been generated it is automatically added to your canvas so you can continue working with it or export it in any of the file formats supported by QGIS.


Further reading
---------------

* [Search for 'An algorithm to construct continuous cartograms' on Google Scholar](https://scholar.google.dk/scholar?q=an+algorithm+to+construct+continuous+area+cartograms)
* [Constructing Contiguous Area Cartogram uUsing ArcView Avenue](http://proceedings.esri.com/library/userconf/proc99/proceed/papers/pap489/p489.htm)
* [def CreateRubberSheetCartogram](http://indiemaps.com/blog/2008/03/def-createrubbersheetcartogram/)


License
-------

QGIS Cartogram – a plugin for creating cartograms from polygon layers  
Copyright (C) 2015  Morten Wulff
Copyright (C) 2013  Carson Farmer

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
