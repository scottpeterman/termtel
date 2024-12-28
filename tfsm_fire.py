import sqlite3
import textfsm
from typing import Dict, List, Tuple, Optional
import io
import time
import click
from multiprocessing import Process, Queue
import multiprocessing
import sys


def parse_template(template_content: str, device_output: str, result_queue: Queue):
    """Helper function to run in separate process."""
    try:
        template = textfsm.TextFSM(io.StringIO(template_content))
        parsed = template.ParseText(device_output)
        result_queue.put((template.header, parsed))
    except Exception as e:
        result_queue.put(None)


class TextFSMAutoEngine:
    def __init__(self, db_path: str, verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self.connection = None
        self._connect_db()

    def _connect_db(self) -> None:
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            if self.verbose:
                click.echo(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    def _calculate_template_score(
            self,
            parsed_data: List[Dict],
            template: sqlite3.Row,
            raw_output: str
    ) -> float:
        score = 0.0

        # Bail out if no data parsed
        if not parsed_data:
            return score

        # Factor 1: Number of records parsed (0-30 points)
        num_records = len(parsed_data)
        if num_records > 0:
            # For show version, we expect 1 record
            if 'version' in template['cli_command'].lower():
                score += 30 if num_records == 1 else 15
            else:
                # For neighbor discovery, scale based on typical counts
                score += min(30, num_records * 10)

        # Factor 2: Field population (0-40 points)
        first_record = parsed_data[0]
        if first_record:
            if 'neighbors' in template['cli_command'].lower():
                # Neighbor discovery critical fields
                critical_fields = {
                    'LOCAL_INTERFACE', 'NEIGHBOR_PORT_ID', 'NEIGHBOR_NAME',
                    'MGMT_ADDRESS', 'NEIGHBOR_DESCRIPTION'
                }
            else:
                # Show version critical fields
                critical_fields = {
                    'VERSION', 'MODEL', 'HARDWARE', 'OS', 'HOSTNAME',
                    'UPTIME', 'SERIAL'
                }

            # Count populated critical fields
            populated_critical = sum(
                1 for field in critical_fields
                if field in first_record and first_record[field] and str(first_record[field]).strip()
            )

            # Calculate percentage of critical fields populated
            if critical_fields:
                critical_score = (populated_critical / len(critical_fields)) * 40
                score += critical_score

        # Factor 3: Data quality (0-30 points)
        if first_record:
            quality_score = 0

            if 'neighbors' in template['cli_command'].lower():
                # Neighbor discovery quality checks
                if 'LOCAL_INTERFACE' in first_record:
                    if any(x in str(first_record['LOCAL_INTERFACE']) for x in ['Gi', 'Eth', 'Te']):
                        quality_score += 10

                if 'MGMT_ADDRESS' in first_record:
                    if str(first_record['MGMT_ADDRESS']).count('.') == 3:
                        quality_score += 10

                if 'NEIGHBOR_NAME' in first_record:
                    if not any(x in str(first_record['NEIGHBOR_NAME']).lower() for x in ['show', 'invalid', 'total']):
                        quality_score += 10
            else:
                # Show version quality checks
                if 'VERSION' in first_record:
                    if len(str(first_record['VERSION'])) > 3:
                        quality_score += 10

                if 'MODEL' in first_record:
                    if len(str(first_record['MODEL'])) > 3:
                        quality_score += 10

                if 'OS' in first_record:
                    if len(str(first_record['OS'])) > 3:
                        quality_score += 10

            score += quality_score

        if self.verbose:
            click.echo(f"\nScore breakdown for template {template['cli_command']}:")
            click.echo(f"  Records score: {min(30, num_records * 10)}")
            click.echo(f"  Field population score: {critical_score}")
            click.echo(f"  Quality score: {quality_score}")

        return score

    def find_best_template(self, device_output: str, filter_string: Optional[str] = None) -> Tuple[
        Optional[str], Optional[List[Dict]], float]:
        """Try filtered templates against the output and return the best match."""
        best_template = None
        best_parsed_output = None
        best_score = 0

        # Get filtered templates from database
        templates = self.get_filtered_templates(filter_string)
        total_templates = len(templates)

        if self.verbose:
            click.echo(f"Found {total_templates} matching templates for filter: {filter_string}")

        # Try each template
        for idx, template in enumerate(templates, 1):
            if self.verbose:
                percentage = (idx / total_templates) * 100
                click.echo(f"\nTemplate {idx}/{total_templates} ({percentage:.1f}%): {template['cli_command']}",
                           nl=False)

            try:
                # Direct parsing without timeout
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
                    click.echo(" -> Failed to parse")
                continue

        # Remove debug prints
        return best_template, best_parsed_output, best_score

    def get_filtered_templates(self, filter_string: Optional[str] = None):
        """Get filtered templates from database."""
        cursor = self.connection.cursor()
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
        if self.connection:
            self.connection.close()

# Add this at the start of your script
if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
