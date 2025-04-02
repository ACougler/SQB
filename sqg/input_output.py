import csv
from typing import Dict, List, Set, Tuple, Optional


def read_csv_with_autodetect(file_path: str) -> List[Dict[str, str]]:
    """
    Reads a CSV file with auto-detected encoding and delimiter.

    Args:
        file_path: Path to the CSV file

    Returns:
        List of dictionaries representing each row

    Raises:
        UnicodeDecodeError: If no supported encoding works
        csv.Error: If CSV parsing fails
    """
    encodings = ["utf-8", "utf-8-sig", "windows-1252", "latin-1"]

    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding) as f:
                sample = f.read(2048)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(f, dialect=dialect)
                return [row for row in reader]
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(f"Could not decode {file_path} with tried encodings: {encodings}")


def read_terms_grouped(file_path: str) -> Dict[str, Set[str]]:
    """
    Read CSV file and return terms grouped by column.

    Args:
        file_path: Path to the CSV file

    Returns:
        Dictionary mapping column names to sets of unique terms
    """
    rows = read_csv_with_autodetect(file_path)
    group_terms: Dict[str, Set[str]] = {}

    for row in rows:
        for key, value in row.items():
            value = value.strip()
            if value:
                group_terms.setdefault(key, set()).add(value)

    return group_terms


def write_queries(
        queries: List[Tuple[str, str]],
        output_path: str,
        main_group: Optional[str] = None,
        metadata_path: Optional[str] = None
) -> None:
    """
    Write queries to output files in both text and optional metadata CSV format.

    Args:
        queries: List of (value, query) tuples
        output_path: Path for the main query output file
        main_group: Name of the main group column (for labeling)
        metadata_path: Optional path for metadata CSV output
    """
    # Write main query file
    _write_queries_txt(queries, output_path, main_group)

    # Write metadata if requested
    if metadata_path:
        _write_metadata_csv(queries, metadata_path, main_group)


def _write_queries_txt(
        queries: List[Tuple[str, str]],
        output_path: str,
        main_group: Optional[str] = None
) -> None:
    """
    Internal function to write queries to a text file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for val, query in sorted(queries):
            if main_group:
                f.write(f"-- {main_group}: {val} --\n{query}\n\n")
            else:
                f.write(f"{query}\n\n")


def _write_metadata_csv(
        queries: List[Tuple[str, str]],
        output_path: str,
        main_group: Optional[str] = None
) -> None:
    """
    Internal function to write query metadata to CSV.
    """
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "group_name", "term_value", "query_string"])

        for i, (val, query) in enumerate(sorted(queries), start=1):
            writer.writerow([i, main_group if main_group else "", val, query])