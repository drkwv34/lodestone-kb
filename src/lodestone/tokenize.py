# SPDX-License-Identifier: Apache-2.0
"""Unicode tokenization using the same unicode61 rules as the persistent FTS index."""

import sqlite3

TOKENIZER = "unicode61 remove_diacritics 2 tokenchars '_-'"


def tokenize(text: str) -> list[str]:
    """Return lowercase tokens in input order, preserving identifiers and hyphens.

    Let SQLite own Unicode folding and diacritic handling rather than approximating
    unicode61 with Python's different Unicode database. No persistent state is used.
    """
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(f'CREATE VIRTUAL TABLE tokens USING fts5(text, tokenize="{TOKENIZER}")')
        connection.execute("CREATE VIRTUAL TABLE vocabulary USING fts5vocab(tokens, instance)")
        connection.execute(
            "INSERT INTO tokens VALUES (?)",
            (text.replace("\x00", " ").encode("utf-8", errors="replace").decode("utf-8"),),
        )
        return [row[0] for row in connection.execute("SELECT term FROM vocabulary ORDER BY offset")]
    finally:
        connection.close()
