import argparse
import json
import os
import random
import csv

import requests
import pandas as pd
import tqdm

from dataget import fetch_file, create_dataframe, get_column_names, clean_dataframe, dataset_report
from utils import save_json
from config import SCHEMA_URL, REGISTRY_URL
from schema import field_to_title_from_schema


def fetch(args):

    # create the data directory if it doesn't already exist
    if not os.path.exists(args.data_dir):
        os.makedirs(args.data_dir)

    # get the registry
    registry = requests.get(args.registry).json()

    # set up debugging
    include_files = None
    if args.test:
        include_files = random.sample(range(len(registry)), args.test_number)

    # go through the registry and download the files
    for k, i in enumerate(registry):

        # if we're testing then ignore a selection of files
        if include_files:
            if k not in include_files:
                continue

        print(i.get('publisher', {}).get('name'))
        for k, j in enumerate(i.get('distribution', [])):
            j["download"] = fetch_file(
                j['downloadURL'], 
                "{}-{}".format(i["identifier"], k),
                args.data_dir,
                request_type='HEAD' if args.test else 'GET'
            )

    # save the amended registry
    save_json(os.path.join(args.data_dir, args.registry_file), registry)


def combine(args):

    # fetch the JSON schema
    schema = requests.get(args.schema).json()

    # get the registry
    with open(os.path.join(args.data_dir, args.registry_file), 'r') as a:
        registry = json.load(a)

    # get the list of column names
    column_names, date_fields = get_column_names(schema)
    field_lookups = field_to_title_from_schema(schema)
    
    # go through the registry and make the dataframes
    dfs = []
    report = {}
    for k, i in tqdm.tqdm(enumerate(registry), unit=" files"):
        pub_name = i.get('publisher', {}).get('name')
        report[pub_name] = {}

        for k, j in enumerate(i.get('distribution', [])):
            if j.get('download'):
                df = create_dataframe(j["download"]["file_location"], j["download"]["file_type"], field_lookups=field_lookups)
                original_columns = df.columns.tolist()
                df = clean_dataframe(df, column_rename=column_names, date_fields=date_fields)
                if args.report:
                    report[pub_name]["{}-{}".format(i["identifier"], k)] = dataset_report(df, original_columns, schema)
                
                # add licence and source columns
                df.loc[:, "source"] = j.get("accessURL", j.get("downloadURL"))
                df.loc[:, "publisher"] = i.get('publisher', {}).get('name')
                df.loc[:, "license"] = i.get('license')

                dfs.append(df)

    # turn into a single combined dataframe
    print("Combining data from {} files".format(len(dfs)))
    dfs = pd.concat(dfs, sort=False)

    # save the outputted dataframe
    print("Saving dataset to {}".format(args.output))
    if args.output_format == 'csv':
        dfs.to_csv(args.output, quoting=csv.QUOTE_NONNUMERIC)
    elif args.output_format == 'csv.gz':
        dfs.to_csv(args.output, compression="gzip", quoting=csv.QUOTE_NONNUMERIC)
    elif args.output_format == 'csv.zip':
        dfs.to_csv(args.output, compression="zip", quoting=csv.QUOTE_NONNUMERIC)
    elif args.output_format in ('xlsx', 'xls', 'excel'):
        dfs.to_excel(args.output)
    elif args.output_format == 'sql':
        dfs.to_sql(args.output, args.db_uri)

    if args.report:
        print("Saving report to {}".format(args.report_name))
        save_json(args.report_name, report)



def main():
    parser = argparse.ArgumentParser(description='Import data from three sixty giving')
    parser.add_argument('--data-dir', default='data', help='Directory to store the data in')
    parser.add_argument('--registry-file', default='data_registry.json', help='Filename for local copy of data registry (relative to data-dir)')
    parser.add_argument('--test', action='store_true', help='Test download (just sends a HEAD request)')
    parser.add_argument('--test-number', default=1, type=int, help='If testing then how many random downloads to request')

    subparsers = parser.add_subparsers(help='Available commands')

    fetch_parser = subparsers.add_parser('fetch', help='Fetch data from the 360 Giving registry')
    fetch_parser.add_argument('--registry', default=REGISTRY_URL, help='Data registry for three sixty giving data')
    fetch_parser.set_defaults(func=fetch)

    fetch_parser = subparsers.add_parser('combine', help='Combine downloaded data from the 360 Giving registry into one file')
    fetch_parser.add_argument('--schema', default=SCHEMA_URL, help='URL of 360 Giving data schema')
    fetch_parser.add_argument('--output', default='threesixty_all.csv', help='Output file location (or table name for SQL output)')
    fetch_parser.add_argument('--output-format', default='csv', choices=['csv', 'xlsx', 'sql', 'csv.gz', 'csv.zip'], help='Format of output')
    fetch_parser.add_argument('--db-uri', default=None, help='URI for accessing the database if sql output format selected')
    fetch_parser.add_argument('--report', action='store_true', help='Output a report with details about the data')
    fetch_parser.add_argument('--report-name', default='report.json', help='File name for report output')
    fetch_parser.set_defaults(func=combine)

    args = parser.parse_args()
    args.func(args)

if __name__=="__main__":
    main()
