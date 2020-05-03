Please view the project report for project information. Below is information on the datasets we used.

Usage: 
`python combined_viz.py <infections-data-path> <recovered-data-path> <deaths-data-path> <density-path> <max-climate-path> <min-climate-path> <countries-csv-path> <migration-data-path> <satellite-image-path>`

For infection data, we used global recoveries, infections, and deaths time series from Johns Hopkins Univeristy:
https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series

For population density, we used data from the Socioeconomic Data and Applications Center (SEDAC) with the following settings:
Year: 2020
FileFormat: GeoTIFF
Resolution: 2.5 minute

https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-rev11/data-download

For climate data, we used data from WorldClim:
https://www.worldclim.org/data/monthlywth.html

We specifically used the tmin_2010-2018 and tmax_2010-2018 datasets from this page, and manually removed 2010-2017 years from the datasets.

The path for <max-climate-path> and <min-climate-path> should also include the beginning portion of each file up to the "-XX.tif in the climate data directory. For example, if the path is /climate/climate-max-01.tif for the January file, use /climate/climate-max for the path.

For migration data, use the provided migration directory, the data was converted to csv from Excel from:
https://www.un.org/en/development/desa/population/migration/data/empirical2/migrationflows.asp#

Example call: 

`python .\combined_viz.py ..\data\time_series\time_series_covid19_confirmed_global.csv ..\data\time_series\time_series_covid19_recovered_global.csv ..\data\time_series\time_series_covid19_deaths_global.csv ..\data\density.tif ..\data\climate-max\climate ..\data\climate-min\climate ..\data\countries.csv ..\data\migration  ..\data\satellite.jpg`


The satellite image is the same one provided for Project 1, download and use one of those images for the <satellite-image-path>
