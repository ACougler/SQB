import argparse
import hashlib
import secrets
import time
from sqg.sqg import (
    read_csv_terms,
    build_query,
    build_queries_by_main_group,
    write_queries,
    write_summary_metadata
)


def prompt_group_settings(headers):
    settings = {}
    print("\nConfigure settings for each column:")

    for header in headers:
        print(f"\nColumn: {header}")
        quote = input("  - Wrap terms in quotes? [y/n]: ").strip().lower() == "y"

        while True:
            operator = input("  - How should this group connect to others? [AND/OR/NOT]: ").strip().upper()
            if operator in {"AND", "OR", "NOT"}:
                break
            print("    ❌ Invalid input. Please enter AND, OR, or NOT.")

        while True:
            internal_operator = input("  - How should values inside this group be joined? [OR/AND]: ").strip().upper()
            if internal_operator in {"OR", "AND"}:
                break
            print("    ❌ Invalid input. Please enter OR or AND.")

        settings[header] = {
            "quote": quote,
            "operator": operator,
            "internal_operator": internal_operator
        }

    return settings



def select_main_group(headers):
    print("\nWhich column should be used to generate one query per value?")
    print("  0. Single combined query (all values together)")

    for i, header in enumerate(headers, start=1):
        print(f"  {i}. {header}")

    while True:
        try:
            choice = input("\nEnter your choice (number): ").strip()
            choice = int(choice)

            if choice == 0:
                return None
            if 1 <= choice <= len(headers):
                return headers[choice - 1]

        except ValueError:
            pass

        print("❌ Invalid choice. Please enter a number between 0 and", len(headers))


def generate_sq_id(file_path: str) -> str:
    """Generate a short unique identifier for the query run."""
    timestamp = str(time.time())
    salt = secrets.token_hex(4)
    hash_input = (file_path + timestamp + salt).encode("utf-8")
    return hashlib.sha1(hash_input).hexdigest()[:10]


def main():
    parser = argparse.ArgumentParser(
        description="Search Query Generator - Build complex search queries from CSV data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to input CSV file"
    )
    parser.add_argument(
        "-o", "--output",
        default="queries.txt",
        help="File to save generated query/queries"
    )
    parser.add_argument(
        "-m", "--metadata",
        help="Optional path to save summary metadata CSV"
    )

    args = parser.parse_args()

    try:
        group_terms = read_csv_terms(args.input)
        headers = list(group_terms.keys())

        if not headers:
            print("❌ Error: No columns found in the input file")
            return

        group_settings = prompt_group_settings(headers)
        main_group = select_main_group(headers)

        # ✅ Generate unique sq_id
        sq_id = generate_sq_id(args.input)

        if main_group:
            queries = build_queries_by_main_group(group_terms, group_settings, main_group)
        else:
            queries = [(None, build_query(group_terms, group_settings))]

        write_queries(queries, args.output, main_group)

        if args.metadata:
            write_summary_metadata(
                sq_id=sq_id,
                input_file=args.input,
                main_group=main_group,
                group_terms=group_terms,
                group_logic=group_settings,
                num_queries=len(queries),
                metadata_path=args.metadata
            )
            print(f"✅ Metadata appended to {args.metadata} [Run ID: {sq_id}]")

        print(f"✅ {len(queries)} query{'ies' if len(queries) != 1 else ''} saved to {args.output}")

    except FileNotFoundError:
        print(f"❌ Error: Input file not found - {args.input}")
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")


if __name__ == "__main__":
    main()