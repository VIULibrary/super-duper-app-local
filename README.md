# Super-Duper-App-Local #


1. Transforms Dpsace metadata export csv to Datacite metadata import CSV
2. Submits records to Datacite for DOI creation
3. Merges the newly created DOIs back into the Dspace CSV
4. Provides basic statistics for the DOIs generated


Combines the CLI versions of 

- [csv-merger-1](https://github.com/VIULibrary/csv-merger-1)
- [Datacite Bulk DOI Generator](https://github.com/VIULibrary/datacite-bulk-doi-creator) 
- [csv-merger-2](https://github.com/VIULibrary/csv-merger-2) 

. . . into one flet GUI app

## REQUIREMENTS ##

### Installation
1. [Install Python 3](https://www.python.org/about/gettingstarted/)
2. [Install Request sand flet library](https://requests.readthedocs.io/en/latest/user/install/)

 - ```pip install flet requests```


## USAGE ##

run with ```python super-duper-app-local.py```


### TESTED with:

- Python 3.10.12
- Python 3.11.0
- Sonoma 14.4.1

