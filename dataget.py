import datetime
import os
import math
import re
import random
import json

import requests
import tqdm
import pandas as pd

from config import CONTENT_TYPE_MAP, typos, pandas_types
from schema import get_fields_from_schema, get_date_fields_from_schema
from utils import column_strip, flatten_json

def fetch_file(url, identifier, datadir='', useragent='360 giving', request_type='get'):
    """
    Fetch and download a 360 giving file
    """

    if request_type.upper() not in ['GET', 'HEAD']:
        raise ValueError("Request type {} not valid".format(request_type))

    # metadata object that will be returned
    metadata = {
        'url': url,
        'identifier': identifier,
        'datetime_downloaded': datetime.datetime.now(),
        'downloaded': False,
        'errors': []
    }
    
    # make the request
    r = requests.request(request_type.upper(),
        url, 
        headers={'User-Agent': useragent},
        stream=True)
    r.raise_for_status()
        
    # work out the content type
    content_type = r.headers.get('content-type', '').split(';')[0].lower()
    if content_type and content_type in CONTENT_TYPE_MAP:
        metadata['file_type'] = CONTENT_TYPE_MAP[content_type]
    elif 'content-disposition' in r.headers:
        metadata['file_type'] = r.headers.get('content-disposition', '').split('.')[-1].strip('"')
    else:
        metadata['file_type'] = url.split('.')[-1]
        
    if metadata['file_type'] not in CONTENT_TYPE_MAP.values():
        raise ValueError("Unrecognised file type {}".format(file_type))

    # set some useful metadata fields
    metadata['file_name'] = "{}.{}".format( identifier, metadata['file_type'] )
    metadata['file_location'] = os.path.join(datadir, metadata['file_name'])
    metadata['file_size'] = r.headers.get('Content-Length', 0)

    total_size = int(metadata['file_size']); 
    block_size = 1024
    
    # if we're getting the data then download it
    if request_type.upper()=="GET":
        with open(metadata['file_location'], 'wb') as fp:
            for data in tqdm.tqdm(r.iter_content(block_size), total=math.ceil(total_size//block_size) , unit='KB', unit_scale=True):
                fp.write(data)
        metadata['downloaded'] = True
    
    return metadata


def get_column_names(schema):
    column_names = get_fields_from_schema(schema)
    column_rename = {
        column_strip(k): k for k in column_names
    }

    for t in typos:
        column_rename[column_strip(t)] = typos[t]

    date_fields = get_date_fields_from_schema(schema)

    return (column_rename, date_fields)


def create_dataframe(file_name, file_type, encoding='utf8', field_lookups={}):
    df = None
    if file_type == 'xlsx':
        try:
            df = pd.read_excel(file_name, index_col='Identifier', parse_dates=False)
        except ValueError as e:
            if str(e)=="Index Identifier invalid":
                df = pd.read_excel(file_name, index_col='identifier', parse_dates=False)
    elif file_type == 'csv':
        try:
            df = pd.read_csv(file_name, index_col='Identifier', encoding=encoding)
        except UnicodeDecodeError:
            df = pd.read_csv(file_name, index_col='Identifier', encoding='latin1')
    elif file_type == 'json':
        with open(file_name, encoding=encoding) as a:
            j = json.load(a)
            df = pd.DataFrame([flatten_json(r, field_lookups) for r in j.get("grants", [])])
    else:
        raise ValueError("Cannot import '{}'. Error: Unknown filetype: {}".format(file_name, file_type))

    return df

def clean_dataframe(df, column_rename={}, date_fields=[]):
    # clean up the columns in the dataframe
    df = df.rename(columns=str.strip)
    df = df.rename(columns=lambda x: x.replace(": ", ":"))
    df = df.rename(columns=lambda x: column_rename.get(column_strip(x), x))
    df = df.rename(columns=lambda x: re.sub('([^0-9]):([^0-9])', r'\1:0:\2', x))

    # rename duplicated columns (https://stackoverflow.com/a/43792894)
    df.columns = pd.io.parsers.ParserBase({'names':df.columns})._maybe_dedup_names(df.columns)

    # sort out date fields
    for f in date_fields:
        if f not in df.columns:
            continue
        
        # check for datetime.time fields which seem to cause issues
        df.loc[df[f].apply(type)==datetime.time, f] = df.loc[df[f].apply(type)==datetime.time, f].apply(str)
        df.loc[:, f] = pd.to_datetime(df[f])

    return df

def dataset_report(df, original_columns=None, schema=None):
    column_names = get_fields_from_schema(schema)
    not_in_schema = [i for i in df.columns.tolist() if re.sub(r':[0-9]+:', ':', i) not in column_names]
    report = {
        "rows": len(df),
        "renamed_columns": df.columns.tolist(),
        "column_description": {
            c: {
                "type": pandas_types.get(df[c].dtype.name, df[c].dtype.name),
                "count": df[c].size,
                "null": df[c].isnull().sum(),
                "blank": (df[c].apply(str)=="").sum(),
                "zero": (df[c].apply(str)=="0").sum(),
                "unique": df[c].nunique(),
                "in_schema": c not in not_in_schema,
                "sample_values": random.sample(
                    df[c].dropna().unique().tolist(), 
                    min(5, df[c].nunique())
                ),
                "common_values": json.loads(df[c].value_counts().head(5).to_json())
            }
            for c in df.columns}
    }

    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c].dtype) and len(df[c].dropna())>0:
            report["column_description"][c]["max"] = df[c].max()
            report["column_description"][c]["min"] = df[c].min()
            report["column_description"][c]["mean"] = df[c].mean()
            report["column_description"][c]["median"] = df[c].median()
            report["column_description"][c]["sum"] = df[c].sum()

        if pd.api.types.is_datetime64_dtype(df[c].dtype) and len(df[c].dropna())>0:
            report["column_description"][c]["max"] = df[c].max()
            report["column_description"][c]["min"] = df[c].min()
            report["column_description"][c]["sample_values"] = random.sample(
                df[c].dropna().dt.strftime('%Y-%m-%d %H:%M:%s').unique().tolist(),
                min(5, df[c].nunique())
            )
            report["column_description"][c]["common_values"] = json.loads(
                df[c].dt.strftime('%Y-%m-%d %H:%M:%s').value_counts().head(5).to_json()
            )
            report["column_description"][c]["count_by_year"] = json.loads(
                df[c].dt.year.value_counts().sort_index().to_json()
            )

    if original_columns:
        report["original_columns"] = original_columns
    return report