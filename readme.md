# Extract and load data from 360 Giving

These scripts can be used to download files from the 360 Giving data registry
and transform them into one large file.

The scripts draw heavily on the [360 Giving "datagetter" code](https://github.com/ThreeSixtyGiving/datagetter)
which is used to fetch data for [GrantNav](http://grantnav.threesixtygiving.org/) and other tools.
The main difference is that this script uses Pandas to combine all the downloaded data and turn
it into a single flat file, rather than producing hierarchical JSON data.

The code is designed to be run through the command line, using the `dataget_cli.py` file.

## Downloading the files

The first step is to download the files using the `dataget_cli.py fetch` command.

```bash
python dataget_cli.py fetch
```

This will download the latest registry file, go through the registry and download
the files. By default these files are saved to the `data/` directory, which may
need to be created.

If run with the `--test` command it will randomly select a file and just run a 
`HEAD` HTTP request to get details about the file.

Details of the files downloaded are saved to a copy of the registry, adding fields
to the distribution record for each publisher. By default this is saved to 
`data/data_registry.json`. An example of the fields added:

```json
"download": {
    "url": "https://data.birmingham.gov.uk/dataset/bb896f0b-10d7-403d-bad4-cc147349c380/resource/6ff023e2-947a-4eb9-bd67-0cdd2c7163dc/download/ssystemsgovernancetransparencygrants360-giving-bcc-data_2014-17-v2.xlsx",
    "identifier": "a002400000sg7fjAAA-0",
    "datetime_downloaded": "2018-07-04T17:24:21.621207",
    "downloaded": true,
    "errors": [],
    "file_type": "xlsx",
    "file_name": "a002400000sg7fjAAA-0.xlsx",
    "file_location": "data\\a002400000sg7fjAAA-0.xlsx",
    "file_size": 0
}
```

### Command line options

```
usage: dataget_cli.py fetch [-h] [--registry REGISTRY]

optional arguments:
  -h, --help           show this help message and exit
  --registry REGISTRY  Data registry for three sixty giving data
  --data-dir DATA_DIR   Directory to store the data in
  --registry-file REGISTRY_FILE
                        Filename for local copy of data registry (relative to
                        data-dir)
  --test                Test download (just sends a HEAD request)
  --test-number TEST_NUMBER
                        If testing then how many random downloads to request

```

## Transform and combine the files

The next step is to load all the files using python pandas, clean some
of the data (mainly changing column names) and combine them into one 
large file.

This is done by running

```bash
python dataget_cli.py combine
```

By default this command will load the registry from `data/data_registry.json`
and load all the files with a valid `download` record into a pandas dataframe.

Column names are standardised against those found in the data standard, and
date columns are transformed into date values.

### Reporting

The `combine` process can output a report on the data found in each file, by
adding a `--report` flag to the command:

```bash
python dataget_cli.py combine --report
```

This outputs a JSON file to `report.json`. For each file a list of the columns
included is returned, alongside some details about the values in those columns.

### Command line options

```
usage: dataget_cli.py combine [-h] [--schema SCHEMA] [--output OUTPUT]
                              [--output-format {csv,xlsx,sql,csv.gz,csv.zip,pickle}]
                              [--db-uri DB_URI] [--report]
                              [--report-name REPORT_NAME]

optional arguments:
  -h, --help            show this help message and exit
  --schema SCHEMA       URL of 360 Giving data schema
  --output OUTPUT       Output file location (or table name for SQL output)
  --output-format {csv,xlsx,sql,csv.gz,csv.zip,pickle}
                        Format of output
  --db-uri DB_URI       URI for accessing the database if sql output format
                        selected
  --report              Output a report with details about the data
  --report-name REPORT_NAME
                        File name for report output
  --data-dir DATA_DIR   Directory to store the data in
  --registry-file REGISTRY_FILE
                        Filename for local copy of data registry (relative to
                        data-dir)
  --test                Test download (just sends a HEAD request)
  --test-number TEST_NUMBER
                        If testing then how many random downloads to request
```

## Installation

The easiest way to run the code is through a python virtual environment. Set it
up by running

```bash
python3 -m venv env
```

Then activate the environment:

```bash
source env/bin/activate # linux
# or 
env\Scripts\activate    # windows
```

Install the requirements

```bash
pip install -r requirements.txt
```

Then the commands above are ready to run. Next time you run the files you only need to 
do the middle `activate` step to enter the virtual environment.
