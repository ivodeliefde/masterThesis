# Discovery, Integration and Aggregation of Sensor Data Using the Semantic Web
Master thesis by Ivo de Liefde (student MSc. Geomatics at Delft University of Technology)

## Background
Sensor data can be retrieved online in a standardized way from so-called Sensor Observation Services (SOS). Requests can be send to these services to get data from them, as defined by the [OGC Sensor Web Enablement standards](http://www.opengeospatial.org/projects/groups/sensorwebdwg). 

However, every SOS has a certain spatial, thematic and temporal extent. Sensor observation services could therefore complement each other. Especially when different kinds of sensor data are required for data fusion this is the case.   

## Goal
This thesis aims to explore to what extent the semantic web can add usefull functionality to Sensor Observation Services. The focus lies on three functionalities: discovery of sensor data sources, integration of sensor data and aggregation of sensor data. The goal is to create two automated processes: 
1. Generate linked data from metadata inside a SOS and publish it in a SPARQL endpoint
2. Retrieve, integrate and aggregate data from all relevant sources for a sensor data request.    

## Methods
A catalogue service can be used to discover a SOS, but the semantic web has a number of characteristics that make could make a good alternative. The metadata is explicitly defined on the web, with a multitude of links to related data. The semantic web can therefore be crawled to find the data sources that are relevant, instead of making a specific request to a catalogue service at a specific URL. 

When different data sources are being used the data needs to be integrated. From the multiple responses a single data set has to be created to work return to the user. The semantics make sure that data about the same observed properties or data created by the same procedure are grouped together. 

The aggregation of sensor data can be simplified using semantics. For spatial aggregation users don't have to provide a geometry in the query, a name or other descriptive term suffices. For example, aggregation per [EEA](http://www.eea.europa.eu/data-and-maps/data/eea-reference-grids) reference grid cell of 10km<sup>2</sup> covering the Netherlands can be translated to a SPARQL query to retrieve the required geometry.

## Data
A number of data sets are converted to linked data. They will be used for the proof of concept implementation. 
1. Dataset of municipalities in the Netherlands and Belgium
2. Dataset of Provinces in the Netherlands and Belgium
3. Dataset of land cover in the Netherlands and Belgium (from [CORINE 2012](http://land.copernicus.eu/pan-european/corine-land-cover/clc-2012)  
4. Dataset of [EEA](http://www.eea.europa.eu/data-and-maps/data/eea-reference-grids) reference grid cells covering the Netherlands and Belgium with a resolution of 100km<sup>2</sup> and 10km<sup>2</sup>.

Two sensor observation services are being used for the proof of concept implementation: the air quality SOS by the [RIVM](http://www.lml.rivm.nl/) and the air quality sos by [ircel-celine](http://www.irceline.be/). 
