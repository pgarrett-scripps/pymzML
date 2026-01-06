"""
Interface for uncompressed mzML files.

@author: Manuel Koesters
"""

from collections import OrderedDict
import bisect
import re
import os
from xml.etree.ElementTree import XML, iterparse
from typing import BinaryIO, TextIO, Pattern, Match, Iterator

from .. import spec
from .. import chromatogram
from .. import regex_patterns


class StandardMzml(object):
    """ """

    def __init__(
        self,
        path: str,
        encoding: str,
        build_index_from_scratch: bool = False,
        index_regex: Pattern[bytes] | None = None,
    ) -> None:
        """
        Initalize Wrapper object for standard mzML files.

        Arguments:
            path (str)     : path to the file
            encoding (str) : encoding of the file
        """
        self.index_regex: Pattern[bytes] | None = index_regex
        self.path: str = path
        self.file_handler: TextIO = self.get_file_handler(encoding)
        self.offset_dict: OrderedDict[int | str, int | tuple[int, ...] | None] = OrderedDict()
        self.spec_open: Pattern[bytes] = regex_patterns.SPECTRUM_OPEN_PATTERN
        self.spec_close: Pattern[bytes] = regex_patterns.SPECTRUM_CLOSE_PATTERN

        self.seek_list: list[tuple[int, int]] = self._read_extremes()
        self._build_index(from_scratch=build_index_from_scratch)

    def get_binary_file_handler(self) -> BinaryIO:
        return open(self.path, "rb")

    def get_file_handler(self, encoding: str) -> TextIO:
        return open(self.path, mode="r", encoding=encoding)

    def __getitem__(
        self, identifier: int | str
    ) -> spec.Spectrum | chromatogram.Chromatogram | None:
        """
        Access the item with id 'identifier'.

        Either use linear, binary or interpolated search.

        Arguments:
            identifier (str): native id of the item to access

        Returns:
            data (str): text associated with the given identifier
        """
        self.file_handler.seek(0)

        spectrum: spec.Spectrum | chromatogram.Chromatogram | None = None
        if str(identifier).upper() == "TIC":
            mzmliter = iterparse(self.file_handler, events=["end"])
            for event, element in mzmliter:
                if event == "end":
                    if element.tag.endswith("}chromatogram"):
                        if element.get("id") == "TIC":
                            spectrum = chromatogram.Chromatogram(element, measured_precision=5e-6)
                            break

        elif identifier in self.offset_dict:
            start_data = self.offset_dict[identifier]
            # Handle both int and tuple formats
            if start_data is None:
                return None
            start_offset = start_data[0] if isinstance(start_data, tuple) else start_data

            seeker = self.get_binary_file_handler()
            seeker.seek(start_offset)
            start, end = self._read_to_spec_end(seeker)

            self.file_handler.seek(start, 0)
            data = self.file_handler.read(end)
            if data.startswith("<spectrum"):
                spectrum = spec.Spectrum(XML(data), measured_precision=5e-6)
            elif data.startswith("<chromatogram"):
                spectrum = chromatogram.Chromatogram(XML(data))
        elif isinstance(identifier, str):
            return self._search_string_identifier(identifier)
        else:
            spectrum = self._binary_search(identifier)

        return spectrum

    def _binary_search(self, target_index: int) -> spec.Spectrum:
        """
        Retrieve spectrum for a given spectrum ID using binary jumps

        Args:
            target_index (int): native id of the spectrum to access

        Returns:
            Spectrum (pymzml.spec.Spectrum): pymzML spectrum
        """
        chunk_size = 12800
        offset_scale = 1
        jump_history = {"forwards": 0, "backwards": 0}

        with open(self.path, "rb") as seeker:
            if target_index not in self.offset_dict.keys():
                for _ in range(40):
                    scan: int | None = None
                    # Cast to satisfy type checker - seek_list has compatible tuple structure
                    insert_position = bisect.bisect_left(self.seek_list, (target_index, 0))  # type: ignore[arg-type]
                    if target_index < self.seek_list[0][0] or target_index > self.seek_list[-1][0]:
                        raise Exception(
                            f"Spectrum ID should be between {self.seek_list[0][0]} and {self.seek_list[-1][0]}"
                        )

                    element_before = self.seek_list[insert_position - 1]
                    spec_offset_m1 = target_index - element_before[0]

                    element_after = self.seek_list[insert_position]
                    spec_offset_p1 = element_after[0] - target_index

                    byte_diff_m1_p1 = element_after[1] - element_before[1]
                    scan_diff_m1_p1 = element_after[0] - element_before[0]

                    average_spec_between_m1_p1 = int(round(byte_diff_m1_p1 / scan_diff_m1_p1))

                    if spec_offset_m1 < spec_offset_p1:
                        jump_direction = "forwards"
                        jump_history["backwards"] = 0
                        jump_history["forwards"] += 1
                        byte_offset = element_before[1] + jump_history["forwards"] * (
                            offset_scale * average_spec_between_m1_p1 * spec_offset_m1
                        )
                        if (target_index - element_before[0]) < 10:
                            byte_offset = element_before[1]
                    else:
                        jump_direction = "backwards"
                        jump_history["forwards"] = 0
                        jump_history["backwards"] += 1
                        byte_offset = element_after[1] - jump_history["backwards"] * (
                            offset_scale * average_spec_between_m1_p1 * spec_offset_p1
                        )

                    byte_offset = int(byte_offset)
                    found_scan = False
                    chunk = b""
                    break_outer = False

                    for x in range(100):
                        seeker.seek(max([os.SEEK_SET + byte_offset + x * chunk_size, 1]))
                        chunk += seeker.read(chunk_size)

                    matches: Iterator[Match[bytes]] = re.finditer(
                        regex_patterns.SPECTRUM_OPEN_PATTERN, chunk
                    )
                    for _, match in enumerate(matches):
                        spec_info = match.groups()
                        spec_info_dict = dict(zip(spec_info[0::2], spec_info[1::2]))
                        id_match = re.search(b"[0-9]*$", spec_info_dict[b"id"])
                        if id_match:
                            scan = int(id_match.group())

                        if jump_direction == "forwards":
                            if scan is not None and scan > target_index:
                                offset_scale = 0.1
                                jump_history["forwards"] = 0
                            else:
                                offset_scale = 1
                        if jump_direction == "backwards":
                            if scan is not None and scan < target_index:
                                offset_scale = 0.1
                                jump_history["backwards"] = 0
                            else:
                                offset_scale = 1

                        if scan in self.offset_dict.keys():
                            continue
                        found_scan = True
                        if scan is not None:
                            new_entry = (
                                scan,
                                byte_offset + match.start(),
                            )
                            new_pos = bisect.bisect_left(self.seek_list, new_entry)
                            self.seek_list.insert(new_pos, new_entry)
                            self.offset_dict[scan] = (byte_offset + match.start(),)
                            if scan == target_index:
                                break_outer = True
                                break
                    if break_outer:
                        break
                    if found_scan:
                        offset_scale = 1
                    else:
                        offset_scale += 1
                    if target_index in self.offset_dict.keys():
                        break

            start_data = self.offset_dict[target_index]
            if start_data is None:
                raise Exception(f"No offset found for spectrum {target_index}")
            start_offset = start_data[0] if isinstance(start_data, tuple) else start_data

            seeker.seek(start_offset)
            data = b""
            while b"</spectrum>" not in data:
                data += seeker.read(chunk_size)
            end = data.find(b"</spectrum>")
            seeker.seek(start_offset)
            spec_string = seeker.read(end + len("</spectrum>"))
            spec_string_decoded = spec_string.decode("utf-8")
            spectrum = spec.Spectrum(XML(spec_string_decoded), measured_precision=5e-6)
            return spectrum

    def _build_index(self, from_scratch: bool = False) -> None:
        """
        Build an index.

        A list of offsets to which a file pointer can seek
        directly to access a particular spectrum or chromatogram without
        parsing the entire file.

        Args:

            from_scratch(bool): Whether or not to force building the index from
                             scratch, by parsing the file, if no existing
                             index can be found.

        Returns:
            A file-like object used to access the indexed content by
            seeking to a particular offset for the file.
        """
        # Declare the pre-seeker
        seeker = self.get_binary_file_handler()
        self.offset_dict["TIC"] = None
        seeker.seek(0, 2)
        index_found = False
        index_list_offset = None

        spectrum_index_pattern: Pattern[bytes] = regex_patterns.SPECTRUM_INDEX_PATTERN
        for _ in range(1, 10):  # max 10kbyte
            # some converters fail in writing a correct index
            # we found
            # a) the offset is always the same (silent fail hurray!)
            sanity_check_set: set[int] = set()
            try:
                seeker.seek(-1024 * _, 1)
            except:
                break
                # File is smaller than 10kbytes ...
            for line in seeker:
                match = regex_patterns.CHROMATOGRAM_OFFSET_PATTERN.search(line)
                if match:
                    self.offset_dict["TIC"] = int(bytes.decode(match.group("offset")))

                match_spec = spectrum_index_pattern.search(line)
                if match_spec is not None:
                    spec_byte_offset = int(bytes.decode(match_spec.group("offset")))
                    sanity_check_set.add(spec_byte_offset)

                match = regex_patterns.INDEX_LIST_OFFSET_PATTERN.search(line)
                if match:
                    index_found = True
                    index_list_offset = int(match.group("indexListOffset").decode("utf-8"))

            if index_found is True and self.offset_dict["TIC"] is not None:
                break

        if index_found is True:
            # Jumping to index list and slurpin all specOffsets
            if index_list_offset is None:
                raise Exception("Index list offset not found although index found")
            seeker.seek(index_list_offset, 0)
            spectrum_index_pattern: Pattern[bytes] = regex_patterns.SPECTRUM_INDEX_PATTERN
            sim_index_pattern: Pattern[bytes] = regex_patterns.SIM_INDEX_PATTERN

            for line in seeker:
                match_spec = spectrum_index_pattern.search(line)
                if match_spec and match_spec.group("nativeID") == b"":
                    match_spec = None
                match_sim = sim_index_pattern.search(line)
                if self.index_regex is None:
                    if match_spec:
                        offset = int(bytes.decode(match_spec.group("offset")))
                        native_id = int(bytes.decode(match_spec.group("nativeID")))
                        self.offset_dict[native_id] = offset
                    elif match_sim:
                        offset = int(bytes.decode(match_sim.group("offset")))
                        native_id = bytes.decode(match_sim.group("nativeID"))
                        try:
                            id_match = regex_patterns.SPECTRUM_ID_PATTERN2.search(native_id)
                            if id_match:
                                native_id = int(id_match.group(2))
                        except (AttributeError, ValueError):
                            # match is None and has no attribute group,
                            # so use the whole string as ID
                            pass
                        self.offset_dict[native_id] = (offset,)
                else:
                    match: Match[bytes] | None = self.index_regex.search(line)
                    if match:
                        native_id_raw = match.group("ID")
                        native_id: int | str
                        try:
                            native_id = int(native_id_raw)
                        except (ValueError, TypeError):
                            native_id = (
                                native_id_raw.decode()
                                if isinstance(native_id_raw, bytes)
                                else str(native_id_raw)
                            )
                        offset_bytes = match.group("offset")
                        # Decode bytes to string first, then convert to int
                        offset_str = (
                            offset_bytes.decode()
                            if isinstance(offset_bytes, bytes)
                            else str(offset_bytes)
                        )
                        offset = int(offset_str)
                        self.offset_dict[native_id] = (offset,)

        elif from_scratch is True:
            seeker.seek(0)
            self._build_index_from_scratch(seeker)
        else:
            print("[Warning] Not index found and build_index_from_scratch is False")

        seeker.close()

    def _build_index_from_scratch(self, seeker: BinaryIO) -> None:
        """Build an index of spectra/chromatogram data with offsets by parsing the file."""

        def get_data_indices(
            fh: BinaryIO, chunksize: int = 8192, lookback_size: int = 100
        ) -> dict[str, int]:
            """Get a dictionary with binary file indices of spectra and
            chromatograms in an mzML file.

            Will parse quickly through the file and find all occurences of
            <chromatogram ... id="..." and <spectrum ... id="..." using a
            regex.
            We dont use an XML parser here because we need to know the
            exact location of the filepointer which is usually not possible
            with common xml parsers.
            """
            chrom_positions: dict[str, int] = {}
            spec_positions: dict[str, int] = {}
            chromcnt = 0
            speccnt = 0
            # regexes to be used
            chromexp: Pattern[bytes] = re.compile(b'<\\s*chromatogram[^>]*id="([^"]*)"')
            chromcntexp: Pattern[bytes] = re.compile(b'<\\s*chromatogramList\\s*count="([^"]*)"')
            specexp: Pattern[bytes] = re.compile(b'<\\s*spectrum[^>]*id="([^"]*)"')
            speccntexp: Pattern[bytes] = re.compile(b'<\\s*spectrumList\\s*count="([^"]*)"')
            # go to start of file
            fh.seek(0)
            prev_chunk = ""
            while True:
                # read a chunk of data
                offset: int = fh.tell()
                chunk: bytes = fh.read(chunksize)
                if not chunk:
                    break

                # append a part of the previous chunk since we have cut in the middle
                # of the text (to make sure we dont miss anything, prev_chunk
                # is analyzed twice).
                if len(prev_chunk) > 0:
                    chunk = prev_chunk[-lookback_size:] + chunk
                    offset -= lookback_size

                prev_chunk = chunk

                # find all occurences of the expressions and add to the dictionary
                for m in chromexp.finditer(chunk):
                    chrom_positions[m.group(1).decode("utf-8")] = offset + m.start()
                for m in specexp.finditer(chunk):
                    spec_positions[m.group(1).decode("utf-8")] = offset + m.start()

                # also look for the total count of chromatograms and spectra
                # -> must be the same as the content of our dict!
                m = chromcntexp.search(chunk)
                if m is not None:
                    chromcnt = int(m.group(1))
                m = speccntexp.search(chunk)
                if m is not None:
                    speccnt = int(m.group(1))
            # Check if everything is ok (e.g. we found the right number of
            # chromatograms and spectra) and then return the dictionary.
            if chromcnt == len(chrom_positions) and speccnt == len(spec_positions):
                positions: dict[str, int] = {}
                positions.update(chrom_positions)
                positions.update(spec_positions)
            else:
                print(
                    "[ Warning ] Found {spec_count} spectra "
                    "and {chrom_count} chromatograms\n"
                    "[ Warning ] However Spectrum index list shows {speccnt} and "
                    "Chromatogram index list shows {chromcnt} entries".format(
                        spec_count=len(spec_positions),
                        chrom_count=len(chrom_positions),
                        speccnt=speccnt,
                        chromcnt=chromcnt,
                    )
                )
                print(
                    "[ Warning ] Updating offset dict with found offsets "
                    "but some might be still missing\n"
                    "[ Warning ] This may happen because your is file truncated"
                )
                positions: dict[str, int] = {}
                positions.update(chrom_positions)
                positions.update(spec_positions)
            return positions

        indices: dict[str, int] = get_data_indices(seeker)
        tmp_dict: OrderedDict[str, tuple[int, ...]] = OrderedDict()

        item_list: list[tuple[str, int]] = sorted(indices.items(), key=lambda x: x[1])
        for i in range(len(item_list)):
            key = item_list[i][0]
            tmp_dict[key] = (item_list[i][1],)

        self.offset_dict.update(tmp_dict)

        # make sure the list is sorted (for bisect)
        # self.info['offsetList'] = sorted(self.info['offsetList'])
        # self.info['seekable'] = True

        return

    def _interpol_search(
        self, target_index: int, chunk_size: int = 8, fallback_cutoff: int = 100
    ) -> spec.Spectrum | None:
        """
        Use linear interpolation search to find spectra faster.

        Arguments:
            target_index (str or int) : native id of the item to access

        Keyword Arguments:
            chunk_size (int)        : size of the chunk to read in one go in kb

        """
        # print('target ', target_index)
        seeker: BinaryIO = self.get_binary_file_handler()
        seeker.seek(0, 2)
        chunk_size = chunk_size * 512
        upper_bound = seeker.tell()
        mid = int(upper_bound / 2)
        seeker.seek(mid, 0)
        current_position = seeker.tell()
        used_indices: set[int] = set()
        spectrum_found = False
        spectrum = None
        while spectrum_found is False:
            jumper_scaling = 1
            file_pointer = seeker.tell()
            data = seeker.read(chunk_size)
            spec_start = self.spec_open.search(data)
            if spec_start is not None:
                spec_start_offset = file_pointer + spec_start.start()
                seeker.seek(spec_start_offset)
                spec_info = spec_start.groups()
                spec_info = dict(zip(spec_info[0::2], spec_info[1::2]))
                id_match = re.search(b"[0-9]*$", spec_info[b"id"])
                if not id_match:
                    continue
                current_index = int(id_match.group())

                self.offset_dict[current_index] = (spec_start_offset,)
                if current_index in used_indices:
                    if current_index > target_index:
                        jumper_scaling -= 0.1
                    else:
                        jumper_scaling += 0.1

                used_indices.add(current_index)

                dist = current_index - target_index
                if dist < -1 and dist > -(fallback_cutoff):
                    spectrum = self._search_linear(seeker, target_index)
                    spectrum_found = True
                    break
                elif dist > 0 and dist < fallback_cutoff:
                    while current_index > target_index:
                        offset = int(current_position - chunk_size)
                        seeker.seek(offset if offset > 0 else 0)
                        current_position = seeker.tell()
                        data = seeker.read(chunk_size)
                        spec_match = self.spec_open.search(data)
                        if spec_match:
                            spec_info = spec_match.groups()
                            spec_info = dict(zip(spec_info[0::2], spec_info[1::2]))
                            id_match = re.search(b"[0-9]*$", spec_info[b"id"])
                            if id_match:
                                current_index = int(id_match.group())
                    seeker.seek(current_position)
                    spectrum = self._search_linear(seeker, target_index)
                    spectrum_found = True
                    break

                if int(current_index) == target_index:
                    seeker.seek(spec_start_offset)
                    start, end = self._read_to_spec_end(seeker)
                    seeker.seek(start)
                    self.offset_dict[current_index] = (start, end)
                    xml_string = seeker.read(end - start)
                    spectrum = spec.Spectrum(XML(xml_string), measured_precision=5e-6)
                    spectrum_found = True
                    break

                elif int(current_index) > target_index:
                    scaling = target_index / current_index
                    seeker.seek(int(current_position * scaling * jumper_scaling))
                    upper_bound = current_position
                    current_position = seeker.tell()
                elif int(current_index) < target_index:
                    scaling = target_index / current_index
                    seeker.seek(int(current_position * scaling * jumper_scaling))
                    current_position = seeker.tell()

            elif len(data) == 0:
                sorted_int_keys = {k: v for k, v in self.offset_dict.items() if isinstance(k, int)}
                sorted_keys = sorted(sorted_int_keys.keys())
                pos = bisect.bisect_left(sorted_keys, target_index) - 2  # dat magic number :)
                try:
                    key = sorted_keys[pos]
                    offset_data = self.offset_dict[key]
                    if offset_data is None or isinstance(offset_data, int):
                        raise Exception(f"Invalid offset data for key {key}")
                    spec_start_offset = offset_data[0]
                except:
                    key = sorted_keys[pos]
                    offset_data = self.offset_dict[key]
                    if offset_data is None or isinstance(offset_data, int):
                        raise Exception(f"Invalid offset data for key {key}")
                    spec_start_offset = offset_data[0]
                seeker = self.get_binary_file_handler()
                seeker.seek(spec_start_offset)
                spectrum = self._search_linear(seeker, target_index)
                # seeker.close()
                spectrum_found = True
                break

        return spectrum

    def _read_to_spec_end(self, seeker: BinaryIO, chunks_to_read: int = 8) -> tuple[int, int]:
        """
        Read from current seeker position to the end of the
        next spectrum tag and return start and end postition

        Args:
            seeker (_io.BufferedReader): Reader instance used in calling function

        Returns:
            positions (tuple): tuple with start and end postion of the spectrum
        """
        # start_pos = seeker.tell()
        chunk_size = 512 * chunks_to_read
        end_found = False
        start_pos = seeker.tell()
        data_chunk = seeker.read(chunk_size)
        end_pos: int | None = None
        while end_found is False:
            data_chunk += seeker.read(chunk_size)
            tag_end, seeker = self._read_until_tag_end(seeker)
            data_chunk += tag_end
            match = regex_patterns.SPECTRUM_CLOSE_PATTERN.search(data_chunk)
            if match:
                end_pos = match.end()
                end_found = True
            else:
                match = regex_patterns.CHROMATOGRAM_CLOSE_PATTERN.search(data_chunk)
                if match:
                    end_pos = match.end()
                    end_found = True
        if end_pos is None:
            raise Exception("Could not find end of spectrum or chromatogram")
        return (start_pos, end_pos)

    def _read_extremes(self) -> list[tuple[int, int]]:
        """
        Read min and max spectrum ids. Required for binary jumps.

        Returns:
            seek_list (list): list of tuples containing spec_id and file_offset
        """
        chunk_size = 128000
        first_scan = 0
        last_scan = 0
        seek_list: list[tuple[int, int]] = []

        with open(self.path, "rb") as seeker:
            buffer = b""
            for x in range(100):
                try:
                    seeker.seek(os.SEEK_SET + x * chunk_size)
                except OSError:
                    break
                chunk = seeker.read(chunk_size)
                buffer += chunk
                match = regex_patterns.SPECTRUM_OPEN_PATTERN_SIMPLE.search(buffer)
                if match is not None:
                    id_match = regex_patterns.SPECTRUM_ID_PATTERN_SIMPLE.search(buffer)
                    if id_match:
                        id_group = id_match.group("id")
                        num_match = re.search(b"[0-9]*$", id_group)
                        if num_match:
                            try:
                                first_scan = int(num_match.group())
                            except ValueError:
                                first_scan = 0
                    seek_list.append((first_scan, seeker.tell() - chunk_size + match.start()))
                    break

            buffer = b""
            seeker.seek(0, os.SEEK_END)
            for x in range(1, 100):
                try:
                    seeker.seek(-x * chunk_size, os.SEEK_END)
                except OSError:
                    break
                chunk = seeker.read(chunk_size)
                buffer = chunk + buffer

                matches = list(regex_patterns.SPECTRUM_OPEN_PATTERN_SIMPLE.finditer(buffer))
                if len(matches) != 0:
                    id_match = regex_patterns.SPECTRUM_ID_PATTERN_SIMPLE.search(
                        buffer[matches[-1].start() :]
                    )
                    if id_match:
                        id_group = id_match.group("id")
                        num_match = re.search(b"[0-9]*$", id_group)
                        if num_match:
                            last_scan = int(num_match.group())
                    seek_list.append((last_scan, seeker.tell() - chunk_size + matches[-1].start()))
                    break
        return seek_list

    def _search_linear(self, seeker: BinaryIO, index: int, chunk_size: int = 8) -> spec.Spectrum:
        """
        Fallback to linear search if interpolated search fails.
        """
        total_chunk_size = chunk_size * 512

        while True:
            file_pointer = seeker.tell()
            data = seeker.read(total_chunk_size)
            string, seeker = self._read_until_tag_end(seeker)
            data += string

            spec_start = self.spec_open.search(data)
            if spec_start:
                spec_start_offset = file_pointer + spec_start.start()
                seeker.seek(spec_start_offset)
                spec_info = spec_start.groups()
                spec_info_dict = dict(zip(spec_info[0::2], spec_info[1::2]))

                id_match = re.search(b"[0-9]*$", spec_info_dict[b"id"])
                current_index = int(id_match.group()) if id_match else 0

                spec_end = self.spec_close.search(data[spec_start.start() :])
                spec_end_offset: int | None = None
                if spec_end:
                    spec_end_offset = file_pointer + spec_end.end() + spec_start.start()
                    seeker.seek(spec_end_offset)
                else:
                    # spec_end is None, search for it in subsequent chunks
                    while spec_end is None:
                        file_pointer = seeker.tell()
                        data = seeker.read(total_chunk_size)
                        string, seeker = self._read_until_tag_end(seeker)
                        data += string

                        spec_end = self.spec_close.search(data)
                        if spec_end:
                            spec_end_offset = file_pointer + spec_end.end()
                            seeker.seek(spec_end_offset)
                            break

                # Store the offset information
                if spec_end_offset is None:
                    raise Exception("Could not find end of spectrum during linear search")
                self.offset_dict[current_index] = (
                    spec_start_offset,
                    spec_end_offset,
                )

                if current_index == index:
                    seeker.seek(spec_start_offset)
                    spec_string: bytes = seeker.read(spec_end_offset - spec_start_offset)
                    xml_element = XML(spec_string)
                    return spec.Spectrum(xml_element, measured_precision=5e-6)

    def _search_string_identifier(
        self, search_string: str, chunk_size: int = 8
    ) -> spec.Spectrum | chromatogram.Chromatogram:
        with self.get_binary_file_handler() as seeker:
            data = None
            total_chunk_size = chunk_size * 512
            spec_start = None

            # NOTE: This needs to go intp regex_patterns.py

            regex_string = re.compile(
                '<\\s*spectrum[^>]*index="[0-9]+"\\sid="({0})"\\sdefaultArrayLength="[0-9]+">'.format(
                    "".join([".*", search_string, ".*"])
                ).encode()
            )

            search_string_bytes = search_string.encode()

            while True:
                file_pointer = seeker.tell()

                data = seeker.read(total_chunk_size)
                string, seeker = self._read_until_tag_end(seeker)
                data += string
                spec_start = regex_string.search(data)
                chrom_start = regex_patterns.CHROMO_OPEN_PATTERN.search(data)
                if spec_start:
                    spec_start_offset = file_pointer + spec_start.start()
                    current_index = spec_start.group(1)
                    if search_string_bytes in current_index:
                        seeker.seek(spec_start_offset)
                        start, end = self._read_to_spec_end(seeker)
                        seeker.seek(start)
                        spec_string = seeker.read(end)
                        xml_string = XML(spec_string)
                        return spec.Spectrum(xml_string, measured_precision=5e-6)
                elif chrom_start:
                    chrom_start_offset = file_pointer + chrom_start.start()
                    if search_string_bytes == chrom_start.group(1):
                        seeker.seek(chrom_start_offset)
                        start, end = self._read_to_spec_end(seeker)
                        seeker.seek(start)
                        chrom_string = seeker.read(end)
                        xml_string = XML(chrom_string)
                        return chromatogram.Chromatogram(xml_string)
                elif len(data) == 0:
                    raise Exception("cant find specified string")

    def _read_until_tag_end(
        self, seeker: BinaryIO, max_search_len: int = 12
    ) -> tuple[bytes, BinaryIO]:
        """
        Help make sure no splitted text appear in chunked data, so regex always find
        <spectrum ...>
        and
        </spectrum>
        """
        count = 0
        string = b""
        curr_byte = ""
        while (
            count < max_search_len and curr_byte != b">" and curr_byte != b"<" and curr_byte != b" "
        ):
            curr_byte = seeker.read(1)
            string += curr_byte
            count += 1
        return string, seeker

    def read(self, size: int = -1) -> str:
        """
        Read binary data from file handler.

        Keyword Arguments:
            size (int): Number of bytes to read from file, -1 to read to end of file

        Returns:
            data (str): byte string of len size of input data
        """
        return self.file_handler.read(size)

    def close(self) -> None:
        """ """
        self.file_handler.close()


if __name__ == "__main__":
    print(__doc__)
