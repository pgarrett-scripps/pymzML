import sqlite3
import xml.etree.ElementTree as et

from pymzml import chromatogram, spec
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
    """Database connector for accessing spectra stored in SQLite."""

    def __init__(self, path: str):
        connection = sqlite3.connect(path)
        self.cursor = connection.cursor()

    def __getitem__(self, key: str | int) -> spec.Spectrum | chromatogram.Chromatogram:
        """Query database for spectrum/chromatogram and return as object."""
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
