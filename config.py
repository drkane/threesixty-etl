acceptable_licenses = [
    'http://www.opendefinition.org/licenses/odc-pddl',
    'https://creativecommons.org/publicdomain/zero/1.0/',
    'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/',
    'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
    'https://creativecommons.org/licenses/by/4.0/',
    'https://creativecommons.org/licenses/by-sa/3.0/',
    'https://creativecommons.org/licenses/by-sa/4.0/',
]

unacceptable_licenses = [
    '',
    # Not relicenseable as CC-BY
    'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/1/', 
    'https://creativecommons.org/licenses/by-nc/4.0/',
    'https://creativecommons.org/licenses/by-nc-sa/4.0/',
]

SCHEMA_URL = 'https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json'
REGISTRY_URL = 'http://data.threesixtygiving.org/data.json'

CONTENT_TYPE_MAP = {
    'application/json': 'json',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'text/csv': 'csv'
}

typos = {
    'Benificiary Location:Name': 'Beneficiary Location:Name',
    'Charity Number (England/Wales)': 'Recipient Org:Charity Number',
    'dateModified': 'Last Modified',
    'Beneficiary location:geographic code (from GIFTS)': 'Beneficiary Location:Geographic Code'
}

# nicer names for pandas datatypes
pandas_types = {
    "object": "string", 
    "float64": "float", 
    "datetime64[ns]": "datetime",
    "int64": "integer"
}
