import datetime
import re
import json

import numpy


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, numpy.integer):
        return int(obj)
    elif isinstance(obj, numpy.floating):
        return float(obj)
    elif isinstance(obj, numpy.ndarray):
        return obj.tolist()
    elif numpy.isnan(obj):
        return null

    raise TypeError ("Type %s not serializable" % type(obj))

def column_strip(k):
    """Turn a column name into a slugified version"""
    return re.sub('[^0-9a-zA-Z]+', '', k.lower().strip())

def flatten_json(jsondata, field_lookups={}, separator=":"):
    """
    Recursive function to flatten a JSON object into a one-dimensional dictionary

    Fields that contain lists are flattened into the format "X:0:Y", while fields with
    dictionaries are flattened into "X:Y".

    Example:

    A json object like:

    {
        'a': 'lorem',
        'b': [
            {'c': 'ipsum'}
        ],
        'd': {
            'e': 'dipsy'
        }
    }

    would become:

    {
        'a': 'lorem',
        'b:0:c': 'ipsum',
        'd:e': 'dipsy
    }
    """
    new_row = {}
    for field in jsondata:

        if type(jsondata[field])==list:
            for i, row in enumerate(jsondata[field]):
                for k, v in flatten_json(row, field_lookups).items():
                    new_row["{}{}{}{}{}".format(
                        field_lookups.get(field, field),
                        separator,
                        i,
                        separator,
                        field_lookups.get(k, k)
                    )] = v

        elif type(jsondata[field])==dict:
            for k, v in flatten_json(jsondata[field], field_lookups).items():
                new_row["{}{}{}".format(
                    field_lookups.get(field, field),
                    separator,
                    field_lookups.get(k, k)
                )] = v

        else:
            new_row[field_lookups.get(field, field)] = jsondata[field]

    return new_row

def save_json(filename, data):
    with open(filename, 'w') as a:
        json.dump(data, a, default=json_serial, indent=4)