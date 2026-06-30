'''
This module (db_util) handles all database management work, including creating
the database from scratch, loading the parsed data into it, and running the
predefined queries against it.
'''

import logging
import sqlite3

# Imports all necessary functions from cleaner.py
from cleaner import clean_data_subject, clean_metabolite_name, clean_data_annotation

# Setting up the logger
logger = logging.getLogger('logger')
logger.setLevel(logging.WARNING)
shandler = logging.StreamHandler()
shandler.setFormatter(logging.Formatter('%(levelname)s - %(asctime)s - {%(pathname)s:%(lineno)d} - %(message)s'))
logger.addHandler(shandler)

# matplotlib is only required for Query 9's scatter plot, so it is imported
# separately and the program can still run the rest of its functionality
# without it installed.
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None
    logger.warning("matplotlib is not installed; Query 9's scatter plot will not be generated.")


class DatabaseManager:
    """
    Wraps a single SQLite connection and provides simple execute/fetch/script
    methods, so callers don't need to open and close a connection for every
    statement they run.
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def execute(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        self.conn.commit()
        return cur

    def executescript(self, script):
        cur = self.conn.cursor()
        cur.executescript(script)
        self.conn.commit()

    def fetch(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        return cur.fetchall()

    def close(self):
        self.conn.close()


def create_database(db_path):
    """Creates the database schema by running the DDL script in sql_file.sql."""
    db = DatabaseManager(db_path)

    try:
        with open("sql_file.sql") as f:
            script = f.read()
    except FileNotFoundError:
        logger.error(
            'The SQL DDL file necessary for building the database structure is missing '
            'from the current directory. Either change your working directory or add '
            'the required file to the current directory.'
        )
        db.close()
        raise SystemExit(1)

    try:
        db.executescript(script)
    except sqlite3.Error as e:
        logger.error(f'The database could not be created due to this exception: {e}')
        db.close()
        raise SystemExit(1)

    db.close()


# This function loads the data of Subjects into the Subject table in the database
def load_subjects(db: DatabaseManager, filename):
    try:
        with open(filename) as f:
            next(f)  # skips the header
            for line in f:
                # since it's a csv file we separate the columns by ','
                row = line.strip().split(",")
                # cleans the data and returns None for Unknown or empty values - see cleaner.py
                cleaned = clean_data_subject(row)
                db.execute("INSERT OR IGNORE INTO Subject VALUES (?,?,?,?,?)", cleaned)
    except FileNotFoundError:
        logger.error(
            'The Subject.csv file is missing from the current directory or has a different '
            'name. Add the file or update the filename in load_database() and try again.'
        )


'''
This function stores the SubjectID, VisitID and SampleID combinations in the Sample table.

We initially use HMP_transcriptome_abundance.tsv to extract SampleIDs. As the additional
omics files (proteome and metabolome) are processed, any new SampleIDs encountered are
added to the Sample table using INSERT OR IGNORE, ensuring the table represents the union
of all samples across datasets.
'''
def load_samples(db, filename):
    try:
        with open(filename) as f:
            next(f)  # skips the header
            for line in f:
                parts = line.strip().split('\t')  # since it's a tab-separated file
                SampleID = parts[0]

                # SampleID format: SubjectID-VisitID
                if "-" not in SampleID:
                    logger.error(f'The sample id {SampleID} is not in the correct format, skipping it.')
                    continue

                SubjectID, VisitID = SampleID.split("-")
                # inserts a new sample into the Sample table, or skips it if it's a duplicate
                db.execute("INSERT OR IGNORE INTO Sample VALUES (?,?,?)", (SampleID, SubjectID, VisitID))
    except FileNotFoundError:
        logger.error(
            'The HMP_transcriptome_abundance.tsv file is missing from the current directory '
            'or has a different name. Add the file or update the filename and try again.'
        )


# This function loads the data from HMP_transcriptome_abundance.tsv into the Transcriptome_Abundance table
def load_transcriptome_abundance(db, filename):
    try:
        with open(filename) as f:
            next(f)
            for line in f:
                parts = line.strip().split("\t")
                SampleID = parts[0]
                A1BG = float(parts[1])

                if "-" not in SampleID:
                    continue
                # SampleID format: SubjectID-VisitID
                SubjectID, VisitID = SampleID.split("-")

                # ensures that any leftover sample ids are added to the Sample table
                db.execute("INSERT OR IGNORE INTO Sample VALUES (?,?,?)", (SampleID, SubjectID, VisitID))
                # inserts the abundance value into its corresponding column
                db.execute(
                    "INSERT OR IGNORE INTO Transcriptome_Abundance VALUES (?,?,?,?)",
                    (SampleID, SubjectID, VisitID, A1BG)
                )
    except FileNotFoundError:
        logger.error(
            'The HMP_transcriptome_abundance.tsv file is missing from the current directory '
            'or has a different name. Add the file or update the filename and try again.'
        )


def load_proteome_abundance(db, filename):
    try:
        with open(filename) as f:
            next(f)
            for line in f:
                parts = line.strip().split("\t")
                SampleID = parts[0]

                if "-" not in SampleID:
                    continue
                # SampleID format: SubjectID-VisitID
                SubjectID, VisitID = SampleID.split("-")

                # ensures that any leftover sample ids are added to the Sample table
                db.execute("INSERT OR IGNORE INTO Sample VALUES (?,?,?)", (SampleID, SubjectID, VisitID))
                db.execute("INSERT OR IGNORE INTO Proteome_Abundance VALUES (?,?,?)", (SampleID, SubjectID, VisitID))
    except FileNotFoundError:
        logger.error(
            'The HMP_proteome_abundance.tsv file is missing from the current directory '
            'or has a different name. Add the file or update the filename and try again.'
        )


def load_metabolome_abundance(db, filename):
    try:
        with open(filename) as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split('\t')  # splits the row by tab
                SampleID = parts[0]

                if "-" not in SampleID:
                    continue
                # SampleID format: SubjectID-VisitID
                SubjectID, VisitID = SampleID.split("-")

                # ensures that any leftover sample ids are added to the Sample table
                db.execute("INSERT OR IGNORE INTO Sample VALUES (?,?,?)", (SampleID, SubjectID, VisitID))
                db.execute(
                    "INSERT OR IGNORE INTO Metabolome_Abundance VALUES (?,?,?)",
                    (SampleID, SubjectID, VisitID)
                )
    except FileNotFoundError:
        logger.error(
            'The HMP_metabolome_abundance.tsv file is missing from the current directory '
            'or has a different name. Add the file or update the filename and try again.'
        )


def load_metabolome_annotation(db, filename):
    try:
        with open(filename) as f:
            next(f)  # skips the header
            for line in f:
                parts = line.strip().split(",")  # since it's a comma-separated file

                PeakID = parts[0]
                metabolites = parts[1].split("|")  # '|' separates multiple values for the same peak
                kegg_ids = parts[2].split("|")
                pathways = parts[5].split("|")

                # processes each metabolite annotation linked to the current peak into a separate row
                for i in range(len(metabolites)):
                    # clean_metabolite_name removes any suffix, e.g. "(1)"
                    Metabolite_Name = clean_metabolite_name(metabolites[i])

                    # retrieves and cleans the corresponding KEGG ID / pathway, handling missing values safely
                    KEGGID = clean_data_annotation(kegg_ids[i] if i < len(kegg_ids) else None)
                    Pathway = clean_data_annotation(pathways[i] if i < len(pathways) else None)

                    db.execute(
                        "INSERT INTO Metabolome_Annotation VALUES (?,?,?,?)",
                        (PeakID, KEGGID, Pathway, Metabolite_Name)
                    )
    except FileNotFoundError:
        logger.error(
            'The HMP_metabolome_annotation.csv file is missing from the current directory '
            'or has a different name. Add the file or update the filename and try again.'
        )


# This function creates a single DatabaseManager and calls all the functions
# necessary for loading data from the input files into the database.
def load_database(db_path):
    db = DatabaseManager(db_path)
    load_subjects(db, 'Subject.csv')
    load_samples(db, 'HMP_transcriptome_abundance.tsv')
    load_transcriptome_abundance(db, 'HMP_transcriptome_abundance.tsv')
    load_proteome_abundance(db, 'HMP_proteome_abundance.tsv')
    load_metabolome_abundance(db, 'HMP_metabolome_abundance.tsv')
    load_metabolome_annotation(db, 'HMP_metabolome_annotation.csv')
    db.close()


def run_query(db_path, query_number):
    db = DatabaseManager(db_path)

    if query_number == 1:
        rows = db.fetch("SELECT SubjectID, Age FROM Subject WHERE Age > 70;")

    elif query_number == 2:
        rows = db.fetch(
            "SELECT SubjectID FROM Subject WHERE Sex='F' AND BMI BETWEEN 18.5 AND 24.9 "
            "ORDER BY SubjectID DESC;"
        )

    elif query_number == 3:
        rows = db.fetch("SELECT DISTINCT VisitID FROM Sample WHERE SubjectID='ZNQOVZV';")

    elif query_number == 4:
        rows = db.fetch(
            "SELECT DISTINCT Subject.SubjectID FROM Metabolome_Abundance, Subject "
            "WHERE Metabolome_Abundance.SubjectID = Subject.SubjectID AND Subject.Insulin_Class='IR';"
        )

    elif query_number == 5:
        rows = db.fetch(
            "SELECT DISTINCT KEGGID FROM Metabolome_Annotation WHERE PeakID IN "
            "('nHILIC_121.0505_3.5','nHILIC_130.0872_6.3','nHILIC_133.0506_2.3','nHILIC_133.0506_4.4');"
        )

    elif query_number == 6:
        rows = db.fetch("SELECT MIN(Age), MAX(Age), AVG(Age) FROM Subject;")

    elif query_number == 7:
        rows = db.fetch(
            "SELECT Pathway, COUNT(*) FROM Metabolome_Annotation WHERE Pathway IS NOT NULL "
            "GROUP BY Pathway HAVING COUNT(*) > 9 ORDER BY COUNT(*) DESC;"
        )

    elif query_number == 8:
        rows = db.fetch("SELECT MAX(A1BG) FROM Transcriptome_Abundance WHERE SubjectID = 'ZOZOW1T';")

    elif query_number == 9:
        rows = db.fetch('SELECT Age, BMI FROM Subject WHERE Age IS NOT NULL AND BMI IS NOT NULL;')

        if plt is None:
            logger.warning("Skipping scatter plot generation because matplotlib is not installed.")
        else:
            age = [row[0] for row in rows]
            bmi = [row[1] for row in rows]

            plt.figure()
            plt.scatter(age, bmi)
            plt.xlabel("Age")
            plt.ylabel("BMI")
            plt.title("Age vs BMI")
            plt.savefig("age_bmi_scatterplot.png")
            plt.close()

    else:
        print("Invalid query number")
        db.close()
        return

    print_rows(rows)
    db.close()


def print_rows(rows):
    for row in rows:
        print("\t".join(str(col) for col in row))
