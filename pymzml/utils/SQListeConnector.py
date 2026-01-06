import sqlite3
from typing import Union
import xml.etree.ElementTree as et
from pymzml import spec
from pymzml import chromatogram
from pymzml.run import Reader


def create_database_from_file(db_name: str, file_path: str):
    conn = sqlite3.connect(db_name + ".db")
    Run = Reader("./tests/data/example.mzML")
    with conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE Spectra(ID INT, xml TEXT)")
        for spectrum in Run:
            params = (spectrum.ID, spectrum.to_string())
            cursor.execute("INSERT INTO Spectra VALUES(?, ?)", params)
    return True


class SQLiteDatabase:
    """
    Example implementation of a database Connector,
    which can be used to make :py:func:`pymzml.run.Reader` accept paths to
    sqlite db files.

    We initialize with a path to a database and implement
    a custom __getitem__ function to retrieve the spectra
    """

    def __init__(self, path: str):
        """ """
        connection = sqlite3.connect(path)
        self.cursor = connection.cursor()

    def __getitem__(self, key: str | int) -> spec.Spectrum | chromatogram.Chromatogram:
        """
        Execute a SQL request, process the data and return a spectrum object.

        Args:
            key (str or int): unique identifier for the given spectrum in the
            database
        """
        self.cursor.execute("SELECT * FROM spectra WHERE id=?", (key,))
        _, element = self.cursor.fetchone()

        element = et.XML(element)
        if "spectrum" in element.tag:
            return spec.Spectrum(element)
        elif "chromatogram" in element.tag:
            return chromatogram.Chromatogram(element)
        raise KeyError(f"No spectrum or chromatogram with id {key} found")

    def get_spectrum_count(self):
        self.cursor.execute("SELECT COUNT(*) from spectra")
        num = self.cursor.fetchone()[0]
        return num

    def read(self, size: int = -1) -> str:
        return '<spectrum index="0" id="controllerType=0 controllerNumber=1 scan=1" defaultArrayLength="917"></spectrum>\n'
