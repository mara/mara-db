"""Different formats for piping"""
from typing import Optional


class Format:
    """Base format definition"""

    def __repr__(self) -> str:
        return (f'<{self.__class__.__name__}'
                + (': ' if any(var for var in vars(self)) else '')
                + ', '.join([f'{var}={getattr(self, var)}'
                             for var in vars(self) if getattr(self, var)])
                + '>')


class NativeFormat(Format):
    """Use the native format of e.g. a database."""
    def __init__(self):
        pass


class CsvFormat(Format):
    """
    CSV file format. See https://tools.ietf.org/html/rfc4180
    """
    def __init__(self, delimiter_char: str = ',', quote_char: Optional[str] = None, header: bool = False, footer: bool = False, null_value_string: Optional[str] = None):
        """
        CSV file format. See https://tools.ietf.org/html/rfc4180

        Args:
            delimiter_char: The character that separates columns
            quote_char: The character for quoting strings
            header: Whether a csv header with the column name(s) is part of the CSV file.
            footer: Whether a footer will be included or not. False by default.
            null_value_string: The string used to indicate NULL.
        """
        self.delimiter_char = delimiter_char or ','
        self.quote_char = quote_char
        self.header = header or False
        self.footer = footer or False
        self.null_value_string = null_value_string


class JsonlFormat(Format):
    """New line delimited JSON stream. See https://en.wikipedia.org/wiki/JSON_streaming"""
    def __init__(self):
        pass


class AvroFormat(Format):
    """Apache Avro"""
    def __init__(self):
        pass


class ParquetFormat(Format):
    """Apache Parquet"""
    def __init__(self):
        pass


class OrcFormat(Format):
    """Apache ORC"""
    def __init__(self):
        pass


def _check_format_with_args_used(pipe_format: Format, header: Optional[bool] = None, footer: Optional[bool] = None, delimiter_char: Optional[str] = None,
                                 csv_format: Optional[bool] = None, quote_char: Optional[str] = None, null_value_string: Optional[str] = None):
    if pipe_format:
        assert all(v is None for v in [header, footer, delimiter_char, csv_format, quote_char, null_value_string]), "You cannot pass format and an old parameter (header, footer, delimiter, csv_format, quote_char, null_value_string) at the same time"


def _get_format_from_args(header: Optional[bool] = None, footer: Optional[bool] = None, delimiter_char: Optional[str] = None, csv_format: Optional[bool] = None,
                          quote_char: Optional[str] = None, null_value_string: Optional[str] = None) -> Format:
    """A internal method handling old parameter settings"""
    if csv_format or delimiter_char and csv_format is None:
        return CsvFormat(delimiter_char=delimiter_char,
                         quote_char=quote_char,
                         header=header,
                         footer=footer,
                         null_value_string=null_value_string)
    else:
        return NativeFormat()
