"""Different formats for piping"""


class Format:
    """Base format definition"""

    def __repr__(self) -> str:
        return (f'<{self.__class__.__name__}: '
                + ', '.join([f'{var}={getattr(self, var)}'
                             for var in vars(self) if getattr(self, var)])
                + '>')


class CsvFormat(Format):
    """
    CSV file format. See https://tools.ietf.org/html/rfc4180
    """
    def __init__(self, delimiter_char: str = None, quote_char: str = None, header: bool = None):
        """
        CSV file format. See https://tools.ietf.org/html/rfc4180

        Args:
            delimiter_char: The character that separates columns
            quote_char: The character for quoting strings
            header: Whether a csv header with the column name(s) is part of the CSV file.
        """
        self.delimiter_char = delimiter_char
        self.quote_char = quote_char
        self.header = header


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
