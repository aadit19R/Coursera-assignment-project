# Roll 48 - QuickBite Online Food Delivery

The submission notebook is `48_Aadit_Rangnekar_CaseStudyB.ipynb`.
It demonstrates all required outcomes: schema design, Python-MySQL connectivity,
joins, aggregation, GROUP BY, and HAVING. It contains 46 original fictional
records across all eight required tables.

## 1. Configure MySQL

Your local connection settings are stored in `.env`. Update the password,
host, port, or user there if needed. Keep the password in
quotes, especially if it contains `#` or spaces. Never submit `.env`.
It is excluded from Git. The password is never printed or embedded in the notebook.

The assignment database is `quickbite_roll48`. The separate reset cell drops
and recreates this database before creating the tables. The guard refuses to
reset any other database named in `.env`. Older coursework databases are not
touched. The selected user needs permission to create/drop the assignment
database, create its tables, and read/insert data.

## 2. Run the notebook yourself

Start MySQL as you normally do. Install the dependencies from this project folder:

```sh
python3 -m pip install -r requirements.txt
```

Open `48_Aadit_Rangnekar_CaseStudyB.ipynb` in VS Code, select the Python
environment with these dependencies, and choose **Run All**. Save the notebook
with its outputs. Successful outputs are already saved in the supplied notebook.

Every full run executes the reset cell, recreates the eight tables, and inserts
46 fresh sample rows. Use Run All for each new screenshot session. Any edits to
the assignment database are deleted by that reset. Settings in `.env` are
reloaded on each full run, including password changes. Keep MYSQL_DATABASE set
to quickbite_roll48 so the guarded reset can run.

The final cell closes the database connection. After that, use Run All again
for a fresh execution. To rerun queries against the current data, rerun only
the connection cell first, then the query cells; skip the reset and insertion.
Running only the insertion cell twice without resetting would cause duplicate
primary-key errors.

You can also run `python3 tools/run_assignment.py`. It executes the same notebook,
checks all five query results and the data relationships, saves the outputs, and
invokes the report builder. This also executes the database reset.

## 3. Report, diagram and screenshots

The completed report is `output/pdf/48_Aadit_Rangnekar_CaseStudyB.pdf`.
It follows the reference report's plain academic layout, with Times New Roman
11 pt body text, larger headings, and separate monospace code blocks.

`er_diagram.png` shows all eight entities, their primary and foreign keys, and
the relationship cardinalities. It is embedded in both the notebook and PDF.
`ER_DIAGRAM_GUIDE.md` explains the relationships and includes importable MySQL DDL
if you later choose an online editor. To regenerate the supplied diagram, run
`python3 tools/make_er_diagram.py`.

The report contains actual screenshots of the successful VS Code notebook
outputs. The 18 cropped output PNGs, original full-window captures, and capture
manifest are saved in `output/screenshots/`. A ZIP of the cropped images is
available as `output/VSCode_Output_Screenshots.zip`.

Rebuild the PDF from the saved notebook and screenshots with:

```sh
python3 tools/build_report.py
```

This command does not connect to MySQL or reset the database. It embeds
`er_diagram.png` and the saved screenshots. If notebook code or output changes,
the screenshots need to be recaptured and their manifest refreshed; until they
match, the builder produces a clearly marked `_DRAFT.pdf`.

## Submission

Submit only the executed `.ipynb` and the final `.pdf`, using the required names.
Keep `.env` and its password out of your submission.
