Usage: 
`python combined_viz.py <infections-data-path> <recovered-data-path> <density-path> <max-climate-path> <min-climate-path> countries.csv <migration-data-path>`

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
