import sqlite3
import textfsm
from typing import Dict, List, Tuple, Optional
import io
import time
import click
from multiprocessing import Process, Queue
import multiprocessing
import sys
import threading
from contextlib import contextmanager


class ThreadSafeConnection:
    """Thread-local storage for SQLite connections"""

    def __init__(self, db_path: str, verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self._local = threading.local()

    @contextmanager
    def get_connection(self):
        """Get a thread-local connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
            if self.verbose:
                click.echo(f"Created new connection in thread {threading.get_ident()}")

        try:
            yield self._local.connection
        except Exception as e:
            if hasattr(self._local, 'connection'):
                self._local.connection.close()
                delattr(self._local, 'connection')
            raise e

    def close_all(self):
        """Close connection if it exists for current thread"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')


class TextFSMAutoEngine:
    def __init__(self, db_path: str, verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self.connection_manager = ThreadSafeConnection(db_path, verbose)

    def _calculate_template_score(
            self,
            parsed_data: List[Dict],
            template: sqlite3.Row,
            raw_output: str
    ) -> float:
        # Previous scoring logic remains the same
        score = 0.0
        if not parsed_data:
            return score

        # Factor 1: Number of records parsed (0-30 points)
        num_records = len(parsed_data)
        if num_records > 0:
            if 'version' in template['cli_command'].lower():
                score += 30 if num_records == 1 else 15
            else:
                score += min(30, num_records * 10)

        # Rest of your scoring logic remains unchanged...
        return score

    def find_best_template(self, device_output: str, filter_string: Optional[str] = None) -> Tuple[
        Optional[str], Optional[List[Dict]], float]:
        """Try filtered templates against the output and return the best match."""
        best_template = None
        best_parsed_output = None
        best_score = 0

        # Get filtered templates using thread-safe connection
        with self.connection_manager.get_connection() as conn:
            templates = self.get_filtered_templates(conn, filter_string)
            total_templates = len(templates)

            if self.verbose:
                click.echo(f"Found {total_templates} matching templates for filter: {filter_string}")

            # Try each template
            for idx, template in enumerate(templates, 1):
                if self.verbose:
                    percentage = (idx / total_templates) * 100
                    click.echo(f"\nTemplate {idx}/{total_templates} ({percentage:.1f}%): {template['cli_command']}")

                try:
                    textfsm_template = textfsm.TextFSM(io.StringIO(template['textfsm_content']))
                    parsed = textfsm_template.ParseText(device_output)
                    parsed_dicts = [dict(zip(textfsm_template.header, row)) for row in parsed]
                    score = self._calculate_template_score(parsed_dicts, template, device_output)

                    if self.verbose:
                        click.echo(f" -> Score={score:.2f}, Records={len(parsed_dicts)}")

                    if score > best_score:
                        best_score = score
                        best_template = template['cli_command']
                        best_parsed_output = parsed_dicts
                        if self.verbose:
                            click.echo(click.style("  New best match!", fg='green'))

                except Exception as e:
                    if self.verbose:
                        click.echo(f" -> Failed to parse: {str(e)}")
                    continue

        return best_template, best_parsed_output, best_score

    def get_filtered_templates(self, connection: sqlite3.Connection, filter_string: Optional[str] = None):
        """Get filtered templates from database using provided connection."""
        cursor = connection.cursor()
        if filter_string:
            filter_terms = filter_string.replace('-', '_').split('_')
            query = "SELECT * FROM templates WHERE 1=1"
            params = []
            for term in filter_terms:
                if term and len(term) > 2:
                    query += " AND cli_command LIKE ?"
                    params.append(f"%{term}%")
            cursor.execute(query, params)
        else:
            cursor.execute("SELECT * FROM templates")
        return cursor.fetchall()

    def __del__(self):
        """Clean up connections on deletion"""
        self.connection_manager.close_all()


# Example usage
if __name__ == '__main__':
    multiprocessing.freeze_support()


    # Example of using the engine in multiple threads
    def worker(engine, output, filter_str):
        result = engine.find_best_template(output, filter_str)
        print(f"Thread {threading.get_ident()}: Found template: {result[0]}")


    engine = TextFSMAutoEngine("templates.db", verbose=True)
    from termtel.config import db_path

    engine = TextFSMAutoEngine(db_path, verbose=True)
    threads = []

    # Create multiple threads
    for i in range(3):
        t = threading.Thread(target=worker, args=(engine, "sample output", "show version"))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()