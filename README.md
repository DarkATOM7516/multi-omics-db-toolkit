# Multi-Omics DB Toolkit

A Python command-line tool that builds a SQLite database from a multi-omics longitudinal cohort dataset, loads the data in, and answers a set of predefined biological queries against it.

The dataset is a subset of the transcriptomic, proteomic, and metabolomic profiling data from [*Personal aging markers and ageotypes revealed by deep longitudinal profiling*](https://www.nature.com/articles/s41591-019-0719-5) (Ahadi et al., 2020) — measurements taken across multiple visits from a cohort of 106 subjects.

## Database Design

<img width="940" height="764" alt="image" src="https://github.com/user-attachments/assets/b1b7e48e-c944-49c5-98c1-80e5387f010e" />

The schema is built around a `Subject` entity (one row per individual, holding demographic and clinical attributes like age, sex, BMI, and insulin resistance class). Each subject can make multiple `Visit`s, and each visit produces a `Sample`, identified by a `SubjectID`-`VisitID` pair.

Each sample can have associated measurements in up to three omics layers:
- **Transcriptome abundance** — gene expression values (e.g. `A1BG`)
- **Proteome abundance**
- **Metabolome abundance**

Metabolome samples are linked to a separate `Metabolome_Annotation` table, which maps peak IDs to metabolite identities (name, KEGG ID, HMDB ID, chemical class, pathway). This is a many-to-many relationship: a single peak can correspond to multiple candidate metabolites (isomers that can't be distinguished from the peak alone), and a single metabolite can be detected as multiple peaks. The annotation table is built as a linking table to represent this correctly, with input data cleaned to merge metabolite name variants (e.g. `Compound(1)`, `Compound(2)`) into a single canonical name.

**Modelling assumption:** the number of visits varies per subject, and not every subject has data in every omics layer, so samples and abundance records are only created for the combinations that actually appear in the input files.

## Requirements

- Python 3, standard library only, **except** for `matplotlib`, which is used to generate the Query 9 scatter plot (the program still runs without it — it just skips plot generation and logs a warning).

## Usage

```bash
python main.py --createdb assignment2.db
python main.py --loaddb assignment2.db
python main.py --querydb=1 assignment2.db
```

These can also be combined in a single command, e.g.:

```bash
python main.py --createdb --loaddb --querydb=6 assignment2.db
```

- `--createdb` builds the schema (via `sql_file.sql`) in the given SQLite file.
- `--loaddb` parses the input data files and loads them into the database.
- `--querydb=N` runs query number `N` (1–9) and prints tab-separated results to the console.

Input files (`Subject.csv`, `HMP_transcriptome_abundance.tsv`, `HMP_proteome_abundance.tsv`, `HMP_metabolome_abundance.tsv`, `HMP_metabolome_annotation.csv`) are expected in the working directory.

## Queries

1. Subjects older than 70 (ID and age)
2. Female subjects with a healthy BMI (18.5–24.9), ordered by subject ID
3. Visit IDs for subject `ZNQOVZV`
4. Distinct subjects with metabolomics samples who are insulin-resistant
5. Unique KEGG IDs annotated for four specific peaks
6. Minimum, maximum, and average subject age
7. Pathways annotated 10+ times, ordered by count
8. Maximum `A1BG` transcript abundance for subject `ZOZOW1T`
9. Subject age vs. BMI (excluding nulls), plus a scatter plot saved as `age_bmi_scatterplot.png`

## Code structure

- `main.py` — CLI entry point, argument parsing
- `db_util.py` — `DatabaseManager` class (wraps a single SQLite connection), data-loading functions, and query execution
- `cleaner.py` — input data cleaning/normalisation functions (missing values, metabolite name suffixes)
- `sql_file.sql` — DDL script defining the database schema
- `docs/erd.png` — entity-relationship diagram

## Context

Originally written for a bioinformatics coursework assignment (BIOL4292, University of Glasgow) covering object-oriented design and programmatic database access. Cleaned up afterward for general readability, including a query ordering fix and consolidating database connection handling into the `DatabaseManager` class.
