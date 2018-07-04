

def get_fields_from_schema(properties, schema=None, parent="", get=None):
    """
    For a given JSON schema file, extract the names of all fields

    If `get` is set to "datetime" then only fields which are in a date format are extracted
    """
    fields = []

    if schema is None:
        schema = properties
    if get is not None:
        get = get.lower()

    for i, p in properties.get("properties", {}).items():
        field_title = p.get("title", i)
        if parent!="":
            field_title = "{}:{}".format(parent, field_title)
        if p.get('items', {}).get("$ref"):
            ref = p.get('items', {}).get("$ref").split("/")
            fields.extend(
                get_fields_from_schema(
                    schema.get(ref[1], {}).get(ref[2]),
                    schema,
                    field_title,
                    get
                )
            )
        else:
            if get in ("date", "datetime", "date-time"):
                if p.get("format")=="date-time":
                    fields.append(field_title)
                else:
                    for f in p.get("oneOf", []):
                        if f.get("format")=="date-time":
                            fields.append(field_title)
            else:
                fields.append(field_title)
    return fields

def field_to_title_from_schema(schema):
    """
    For a JSON schema file, extract a dictionary of {field key: field titles}, for use in lookups

    @TODO: this should probably change to use the full field key rather than conflating all
    the ones from definitions in the same dictionary.
    """
    fields = {}
    for i, p in schema.get("properties").items():
        fields[i] = p.get("title", i)
    for _, d in schema.get("definitions", {}).items():
        for i, p in d.get("properties", {}).items():
            fields[i] = p.get("title", i)
    return fields

def get_date_fields_from_schema(schema):
    """
    Wrapper around get_fields_from_schema to just get the date fields.
    """
    return get_fields_from_schema(schema, get='datetime')
