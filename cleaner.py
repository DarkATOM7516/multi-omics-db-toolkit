'''This module deals with cleaning and normalising input data before it is loaded into the database.'''

import re


def clean_value(value):
    # if the input data contains 'NA', 'Unknown' or is empty, convert it to None - otherwise return it as-is
    if value in ('NA', 'Unknown', 'unknown', ''):
        return None
    return value


assert clean_value('') is None
assert clean_value('F') == 'F'


# This function parses and cleans a single row from Subject.csv
def clean_data_subject(row):
    SubjectID = row[0]

    Sex = clean_value(row[2])
    Age = clean_value(row[3])
    if Age is not None:
        Age = float(Age)

    BMI = clean_value(row[4])
    if BMI is not None:
        BMI = float(BMI)

    Insulin_Class = clean_value(row[6])

    return (SubjectID, Age, Sex, BMI, Insulin_Class)


# testing the clean_data_subject function
assert clean_data_subject(['ZJOSZHK', 'C', 'M', '41.43', '19.42', 'NA', 'Unknown']) == ('ZJOSZHK', 41.43, 'M', 19.42, None)
assert clean_data_subject(['ZJOSZH', '', 'M', '41', '', '', '']) == ('ZJOSZH', 41, 'M', None, None)


# This function cleans metabolite names by removing numeric suffixes like "(1)"
def clean_metabolite_name(name):
    return re.sub(r"\(\d+\)", "", name).strip()


# testing clean_metabolite_name
assert clean_metabolite_name("2,3-Dihydroxyvaleric acid(1)") == "2,3-Dihydroxyvaleric acid"
assert clean_metabolite_name("2,3-Dihydroxyvaleric acid(2)") == "2,3-Dihydroxyvaleric acid"


# This function strips whitespace and converts empty/missing annotation values to None
def clean_data_annotation(value):
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    return value


# testing clean_data_annotation
assert clean_data_annotation(None) is None
assert clean_data_annotation("   ") is None
assert clean_data_annotation("  Pathway Name  ") == "Pathway Name"
