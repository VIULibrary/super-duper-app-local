
1. Transforms Dpsace metadata export csv to Datacite metadata import csv
2. Submits records to Datacite for DOI creation
3. Merges the newly created DOIs back into the Dspace csv for importing


Combines the CLI versions of 

- csv-merger-1
- Datacite Bulk DOI Generator from .LINK . . . with some additions: improved error handling, and automated suffix assignment
- csv-merger-2 

into one flet GUI app


todo: 


screenshot
link to demo

documentation: 


TESTED with

Python 3.10.12
Python 3.11.0
Ubuntu 22.04.5 LTS
Sonoma 14.4.1


REQUIREMENTS

## Installation
1. [Install Python 3](https://www.python.org/about/gettingstarted/)
2. [Install Request sand flet library](https://requests.readthedocs.io/en/latest/user/install/)

 - ```pip install flet requests```




USAGE

run with ```python super-duper-app-local.py```


ATTRIBUTION

    converter  
