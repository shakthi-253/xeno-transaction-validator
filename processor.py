"""
Processes an uploaded transaction CSV:
- Validates every row using validator.py
- Splits rows into valid / invalid
- Produces a cleaned output (valid rows only)
- Splits large outputs into chunks of CHUNK_SIZE rows
"""
import pandas as pd
import io
import zipfile
from validator import validate_row

CHUNK_SIZE = 500  # rows per output file before splitting


def process_dataframe(df: pd.DataFrame):
    """
    Takes a raw DataFrame from the uploaded CSV.
    Returns: (valid_df, invalid_df_with_errors, summary_dict)
    """
    valid_rows = []
    invalid_rows = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        is_valid, errors = validate_row(row_dict)

        if is_valid:
            valid_rows.append(row_dict)
        else:
            row_dict["_row_number"] = idx + 2  # +2: 1-index + header row
            row_dict["_errors"] = "; ".join(errors)
            invalid_rows.append(row_dict)

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)

    summary = {
        "total_rows": len(df),
        "valid_rows": len(valid_df),
        "invalid_rows": len(invalid_df),
        "success_rate": round((len(valid_df) / len(df)) * 100, 1) if len(df) > 0 else 0,
    }

    return valid_df, invalid_df, summary


def split_into_chunks(df: pd.DataFrame, chunk_size: int = CHUNK_SIZE):
    """
    Splits a DataFrame into a list of smaller DataFrames,
    each with at most `chunk_size` rows.
    """
    chunks = []
    for start in range(0, len(df), chunk_size):
        chunks.append(df.iloc[start:start + chunk_size])
    return chunks


def build_download_package(valid_df: pd.DataFrame) -> bytes:
    """
    Builds a downloadable package for the cleaned data.
    - If small enough (<= CHUNK_SIZE rows): returns a single CSV as bytes.
    - If large: returns a ZIP file containing multiple chunked CSVs.
    Returns: (file_bytes, filename, mime_type)
    """
    if len(valid_df) <= CHUNK_SIZE:
        csv_bytes = valid_df.to_csv(index=False).encode("utf-8")
        return csv_bytes, "cleaned_transactions.csv", "text/csv"

    # Large file -> split into chunks and zip them
    chunks = split_into_chunks(valid_df, CHUNK_SIZE)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, chunk in enumerate(chunks, start=1):
            chunk_csv = chunk.to_csv(index=False)
            zf.writestr(f"cleaned_transactions_part{i}.csv", chunk_csv)

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), "cleaned_transactions_chunks.zip", "application/zip"
