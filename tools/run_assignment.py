"""Execute the assignment without launching a Jupyter server; save real outputs."""
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
import os
import sys

import nbformat as nbf
import pandas as pd
from dotenv import dotenv_values

from build_report import build_report

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "48_Aadit_Rangnekar_CaseStudyB.ipynb"


def verify(namespace):
    """Check actual results and cross-table business rules before closing MySQL."""
    show = namespace["show"]
    expected = {
        "Customers": 5, "Restaurants": 5, "MenuItems": 6, "DeliveryAgents": 5,
        "Orders": 6, "OrderItems": 8, "Payments": 6, "Reviews": 5,
    }
    for table, count in expected.items():
        assert show(f"SELECT COUNT(*) FROM {table}").iat[0, 0] == count, table
        columns = show(f"SHOW COLUMNS FROM {table}")["Field"].tolist()
        assert columns == [c[0] for c in namespace["schema"][table]], table
    constraints = show("""SELECT CONSTRAINT_TYPE, COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
                          WHERE CONSTRAINT_SCHEMA = DATABASE() GROUP BY CONSTRAINT_TYPE""")
    assert dict(constraints.itertuples(index=False, name=None)) == {
        "PRIMARY KEY": 8, "FOREIGN KEY": 9, "CHECK": 9, "UNIQUE": 4
    }, "Required database constraints are missing"
    wanted = [
        [("Harbour Bowl", 2, "250.00"), ("Ember Slice", 1, "350.00"),
         ("Pune Wok", 1, "280.00"), ("Godavari Kitchen", 1, "150.00"),
         ("Leaf and Ladle", 1, "120.00")],
        [("UPI", "1050.00"), ("Card", "700.00")],
        [("Anaya Deshmukh", 2), ("Vihaan Shah", 2)],
        [("Omkar Jadhav", 2), ("Rhea Naik", 2), ("Dev More", 1),
         ("Meera Kale", 1), ("Adil Khan", 0)],
        [("Non-Veg", 2, "300.00"), ("Veg", 4, "350.00")],
    ]
    for i, rows in enumerate(wanted, 1):
        actual = namespace[f"q{i}"].astype(str).values.tolist()
        assert actual == [[str(v) for v in row] for row in rows], f"Q{i} mismatch"
    checks = [
        """SELECT COUNT(*) FROM OrderItems oi
           JOIN Orders o ON oi.order_id = o.order_id
           JOIN MenuItems m ON oi.item_id = m.item_id
           WHERE o.restaurant_id <> m.restaurant_id""",
        """SELECT COUNT(*) FROM Reviews r JOIN Orders o ON r.order_id = o.order_id
           WHERE r.customer_id <> o.customer_id OR o.order_status <> 'Delivered'""",
        """SELECT COUNT(*) FROM Orders o
           JOIN Customers c ON o.customer_id = c.customer_id
           JOIN Restaurants r ON o.restaurant_id = r.restaurant_id
           JOIN DeliveryAgents a ON o.agent_id = a.agent_id
           WHERE c.city <> r.city OR a.city <> r.city OR o.order_date < c.join_date""",
        """SELECT COUNT(*) FROM Payments p WHERE p.amount <>
           (SELECT SUM(oi.quantity * m.price) FROM OrderItems oi
            JOIN MenuItems m ON oi.item_id = m.item_id WHERE oi.order_id = p.order_id)""",
    ]
    assert all(show(sql).iat[0, 0] == 0 for sql in checks), "Business-rule mismatch"


def run():
    os.chdir(ROOT)
    settings = dotenv_values(ROOT / ".env")
    password = settings.get("MYSQL_PASSWORD", os.environ.get("MYSQL_PASSWORD"))
    if password is None or password == "REPLACE_WITH_YOUR_MYSQL_PASSWORD":
        print("Fill in MYSQL_PASSWORD in .env, then run this command again.")
        return 1
    notebook = nbf.read(NOTEBOOK, as_version=4)
    namespace, count = {"schema": notebook.metadata.assignment.schema}, 0
    buffer, outputs = StringIO(), []

    def flush():
        if buffer.getvalue():
            outputs.append(nbf.v4.new_output("stream", name="stdout", text=buffer.getvalue()))
            buffer.seek(0)
            buffer.truncate(0)

    def display(value):
        flush()
        plain = value.to_string(index=False) if isinstance(value, pd.DataFrame) else str(value)
        data = {"text/plain": plain}
        if isinstance(value, pd.DataFrame):
            data["text/html"] = value.to_html(index=False)
        outputs.append(nbf.v4.new_output("display_data", data=data))

    namespace["display"] = display
    try:
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            count += 1
            outputs = []
            print(f"Running cell {count}: {cell.metadata.get('role', 'code')}")
            if cell.metadata.get("role") == "close":
                verify(namespace)
            with redirect_stdout(buffer):
                exec(compile(cell.source, f"notebook-cell-{count}", "exec"), namespace)
            flush()
            cell.outputs, cell.execution_count = outputs, count
        today = date.today().strftime("%d %B %Y")
        notebook.cells[0].source = notebook.cells[0].source.replace("21 October 2026", today)
        notebook.metadata.assignment.update(status="passed", executed_on=date.today().isoformat())
        nbf.validate(notebook)
        nbf.write(notebook, NOTEBOOK)
        report = build_report(NOTEBOOK)
        print(f"Verified all 5 queries, 8 row counts, and business rules.\nNotebook: {NOTEBOOK}\nPDF: {report}")
        return 0
    except Exception as exc:
        # Do not save failed/partial outputs over an existing successful notebook.
        print(f"Stopped ({type(exc).__name__}): {exc}", file=sys.stderr)
        print("Notebook outputs were not replaced. Check .env and that MySQL is running.", file=sys.stderr)
        return 1
    finally:
        connection = namespace.get("conn")
        if connection is not None and connection.is_connected():
            connection.rollback()
            connection.close()


if __name__ == "__main__":
    sys.exit(run())
