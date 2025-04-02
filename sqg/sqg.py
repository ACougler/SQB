import csv
import os
from typing import Dict, List, Set, Tuple, Union
from datetime import datetime

def clean_term(term: str, quote: bool) -> str:
    """Format a single term with or without quotes.

    Args:
        term: The term to format
        quote: Whether to wrap in quotes (also wraps if term contains spaces)

    Returns:
        Formatted term or empty string if term is empty
    """
    if not term:
        return ""
    term = term.strip()
    if quote or " " in term:
        return f'"{term}"'
    return term

def format_group(terms: Set[str], quote: bool, internal_operator: str = "OR") -> str:
    """Format a group of terms as an OR group in parentheses.

    Args:
        :param: Set of terms to join
        :param: Whether to quote individual terms
        :param internal_operator: How the terms are handled internally
    Returns:
        Formatted group string or empty string if no terms
    """
    formatted = [clean_term(term, quote) for term in sorted(terms) if term]
    return f"({' {} '.format(internal_operator).join(formatted)})" if formatted else ""

def build_query(group_terms: Dict[str, Set[str]],
                group_logic: Dict[str, Dict[str, Union[bool, str]]]) -> str:
    """Build a query string from grouped terms and logic settings.

         Args:
             group_terms: Dictionary of {group_name: set_of_terms}
             group_logic: Dictionary of {group_name: {"quote": bool, "operator": str}}

         Returns:
             Fully formatted query string

         Example:
             >>> group_terms = {"color": {"red", "blue"}, "size": {"large"}}
             >>> group_logic = {"color": {"quote": False, "operator": "AND"},
                               "size": {"quote": True, "operator": "AND"}}
             >>> build_query(group_terms, group_logic)
             '(red OR blue) AND "large"'
         """
    group_items = [(group, group_terms[group]) for group in group_terms if group_terms[group]]
    parts = []

    for i, (group, terms) in enumerate(group_items):
        quote = group_logic[group]["quote"]
        internal_op = group_logic[group].get("internal_operator", "OR")
        group_str = format_group(terms, quote, internal_op)

        if i < len(group_items) - 1:
            outer_op = group_logic[group]["operator"]
            parts.append(f"{group_str} {outer_op}")
        else:
            parts.append(group_str)

    return " ".join(parts)

def build_queries_by_main_group(
        group_terms: Dict[str, Set[str]],
        group_logic: Dict[str, Dict[str, Union[bool, str]]],
        main_group: str
) -> List[Tuple[str, str]]:
    """Build one query per unique value in the main group column.

      Args:
          group_terms: Dictionary of {group_name: set_of_terms}
          group_logic: Dictionary of group settings
          main_group: The column name to generate individual queries for

      Returns:
          List of (value, query_string) tuples

      Raises:
          ValueError: If main_group doesn't exist in group_terms
      """
    if main_group not in group_terms:
        raise ValueError(f"Main group '{main_group}' not found in group terms.")

    queries = []
    static_groups = [(g, group_terms[g]) for g in group_terms if g != main_group and group_terms[g]]
    main_values = sorted(group_terms[main_group])

    for val in main_values:
        parts = []

        for i, (group, terms) in enumerate(static_groups):
            quote = group_logic[group]["quote"]
            internal_op = group_logic[group].get("internal_operator", "OR")
            group_str = format_group(terms, quote, internal_op)
            op = group_logic[group]["operator"]

            parts.append(f"{group_str} {op}")

        # Add main group value last without trailing operator
        quote = group_logic[main_group]["quote"]
        internal_op = group_logic[main_group].get("internal_operator", "OR")
        main_str = format_group({val}, quote, internal_op)
        parts.append(main_str)

        queries.append((val, " ".join(parts)))

    return queries

def read_csv_terms(file_path: str) -> Dict[str, Set[str]]:
    """Read terms from CSV file with auto-detected encoding/delimiter.

    Args:
        file_path: Path to CSV file

    Returns:
        Dictionary of {column_name: set_of_terms}

    Raises:
        UnicodeDecodeError: If file cannot be read with supported encodings
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
                rows = list(reader)
                return {
                    col: {row[col].strip() for row in rows if row[col].strip()}
                    for col in reader.fieldnames
                }
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(f"Could not decode {file_path} with tried encodings: {encodings}")


def write_queries(
        queries: List[Tuple[str, str]],
        output_path: str,
        main_group: str = None,
) -> None:
    """Write queries to output files.

    Args:
        queries: List of (value, query_string) tuples
        output_path: Path for main output file
        main_group: Name of main group (for labeling)
    """
    # Write main query file
    with open(output_path, "w", encoding="utf-8") as f:
        for val, query in sorted(queries):
            if main_group:
                f.write(f"-- {main_group}: {val} --\n{query}\n\n")
            else:
                f.write(f"{query}\n\n")

def write_summary_metadata(
        sq_id: str,
        input_file: str,
        main_group: Union[str, None],
        group_terms: Dict[str, Set[str]],
        group_logic: Dict[str, Dict[str, Union[bool, str]]],
        num_queries: int,
        metadata_path: str = "query_summary.csv"
) -> None:
    """ Write summary metadata to output file.
    Args:
        :param sq_id: SearchQuery ID-number
        :param input_file: Path to input file
        :param main_group: Name of main group (for labeling)
        :param group_terms: List of remaining group terms
        :param group_logic: Dictionary of group settings
        :param num_queries: Number of queries to generate
        :param metadata_path: Optional path for metadata CSV
        """
    fieldnames = [
        "sq_id", "timestamp", "input_file", "main_group",
        "group_count", "terms_total", "query_count", "group_logic"
    ]

    data_row = {
        "sq_id": sq_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input_file": input_file,
        "main_group": main_group or "(combined)",
        "group_count": len(group_terms),
        "terms_total": sum(len(terms) for terms in group_terms.values()),
        "query_count": num_queries,
        "group_logic": "; ".join(
            f"{g}:{group_logic[g]['operator']}/{group_logic[g].get('internal_operator', 'OR')}"
            for g in group_terms if g != main_group
        )
    }

    file_exists = os.path.exists(metadata_path)

    with open(metadata_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_row)