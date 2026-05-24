"""
Factory de parsers: dado el tipo de archivo, retorna el parser correcto.
"""

from app.services.parser.base import AbstractParser
from app.services.parser.csv_parser import CSVParser
from app.services.parser.xlsx_parser import XLSXParser
from app.services.parser.pdf_parser import PDFParser


def get_parser(tipo_archivo: str) -> AbstractParser:
    """
    Retorna la instancia del parser correspondiente al tipo de archivo.

    Args:
        tipo_archivo: Extensión del archivo en minúsculas ("csv", "xlsx", "pdf")

    Raises:
        ValueError: Si el tipo no está soportado
    """
    parsers: dict[str, AbstractParser] = {
        "csv": CSVParser(),
        "xlsx": XLSXParser(),
        "pdf": PDFParser(),
    }

    parser = parsers.get(tipo_archivo.lower())
    if parser is None:
        raise ValueError(f"Tipo de archivo no soportado: '{tipo_archivo}'. Use csv, xlsx o pdf.")

    return parser
