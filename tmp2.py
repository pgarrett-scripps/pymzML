from xsdata.formats.dataclass.parsers import XmlParser
from mzml.generated import MzML

parser = XmlParser()
mzml = parser.parse("file.mzML", MzML)

# Fully typed access
print(mzml.run.spectrum_list.count)