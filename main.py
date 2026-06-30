'''
This is the main driver script that coordinates database creation, data loading,
and execution of predefined database queries based on command-line arguments.

Note: input file locations and names can be modified in db_util.py if required.
All input files must follow the expected format for correct execution.
Necessary error handling has been implemented, but malformed input may still
cause unexpected behaviour.
'''

# Imports the argparse module to handle command-line arguments.
import argparse
# Imports all necessary functions from db_util.py
from db_util import create_database, load_database, run_query


def main():
    parser = argparse.ArgumentParser(
        prog='cw2_assignment',
        description='Creates a database from scratch, loads it with data, and runs queries against it.'
    )
    parser.add_argument(
        "--createdb", action="store_true",
        help='Create the database structure.'
    )  # creates database when specified
    parser.add_argument(
        "--loaddb", action="store_true",
        help='Parse the data files and load the database with all required data.'
    )  # loads the database when specified
    parser.add_argument(
        "--querydb", type=int,
        help='Run a specific query, numbered 1-9, e.g. --querydb=1'
    )  # execute specific queries from 1-9
    parser.add_argument("dbfile")

    args = parser.parse_args()  # parses all command line arguments provided by the user

    if args.createdb:
        create_database(args.dbfile)  # creates database if --createdb is entered

    if args.loaddb:
        load_database(args.dbfile)  # database is loaded with all the required information if --loaddb is entered

    if args.querydb:
        run_query(args.dbfile, args.querydb)  # return requested query result, from 1-9


# Ensures that the script runs only when executed directly, not when imported
if __name__ == "__main__":
    main()  # calls the main function to start program execution
