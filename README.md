# Super-Duper-App-Local #


1. Transforms Dpsace metadata export csv to Datacite metadata import CSV
2. Submits records to Datacite for DOI creation
3. Merges the newly created DOIs back into the Dspace CSV
4. Provides basic statistics for the DOIs generated


Combines the CLI versions of 

- [csv-merger-1](https://github.com/VIULibrary/csv-merger-1)
- [Datacite Bulk DOI Generator](https://github.com/VIULibrary/datacite-bulk-doi-creator) - forked from [GSU's datacite-bulk-doi-creator](https://github.com/gsu-library/datacite-bulk-doi-creator)
- [csv-merger-2](https://github.com/VIULibrary/csv-merger-2) 

. . . into one flet GUI app

## REQUIREMENTS ##

### Installation
1. [Install Python 3](https://www.python.org/about/gettingstarted/)
2. [Install Request sand flet library](https://requests.readthedocs.io/en/latest/user/install/)

 - ```pip install flet requests```


## USAGE ##


1. In page 2 change the URL pattern to map your 'source' field correctly in this line: `uri_patterns = ["http://hdl.handle.net/10613", "http://hdl.handle.net/10170"]` (in this example we're using 2 possible URL patterns to create a source field)
2. In page 4 change the DOI prefix to your prefix in this line `if any(prefix in existing_uri for prefix in ["10.25316", "https://doi.org"]):` (this prevents the creation and merging multiple DOI for a single item)
3. Save and run with ```python super-duper-app-local.py```
5. Check your downloaded CSV files for errors, and/or items missed by the script. It will not catch everything
4. Dspace metadata import changes are usually capped out at 1K per csv. Keep this in mind as you process through this pipeline :)


### TESTED with:

- Python 3.10.12
- Python 3.11.0
- Sonoma 14.4.1

