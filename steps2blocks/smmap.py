import logging
from enum import Enum
from io import StringIO
from typing import NamedTuple

TICKS_PER_MEASURE = 192
BEATS_PER_MEASURE = 4
TICKS_PER_BEAT = TICKS_PER_MEASURE / BEATS_PER_MEASURE


class BPMChange(NamedTuple):
    beat: float
    new_bpm: float


class ChartType(Enum):
    DANCE_SINGLE = "dance-single"
    UNKNOWN = "???"  # TODO

    @classmethod
    def _missing_(cls, value: object) -> "ChartType":
        return cls.UNKNOWN


class Difficulty(Enum):
    BEGINNER = "Beginner"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    CHALLENGE = "Challenge"
    EDIT = "Edit"


class NoteType(Enum):
    # NONE = "0"
    NORMAL = "1"
    START_HOLD = "2"
    STOP_HOLD_ROLL = "3"
    START_ROLL = "4"
    MINE = "M"
    KEYSOUND = "K"
    LIFT = "L"
    FAKE = "F"


class Note(NamedTuple):
    tick: int
    column: int
    note_type: NoteType


class SMChart:
    chart_type: ChartType
    description: str
    difficulty: Difficulty
    meter: int  # TODO
    notes: list[Note]

    def __init__(self):
        self.chart_type = ChartType.DANCE_SINGLE
        self.description = ""
        self.difficulty = Difficulty.BEGINNER
        self.meter = 0
        self.notes = []


class SMSong:
    title: str
    sub_title: str
    artist: str
    credit: str
    music_path: str
    start_offset: float
    sample_start: float
    sample_duration: float
    bpm_changes: list[BPMChange]
    charts: list[SMChart]

    def __init__(self):
        self.title = ""
        self.sub_title = ""
        self.artist = ""
        self.credit = ""
        self.music_path = ""
        self.start_offset = 0.0
        self.sample_start = 0.0
        self.sample_duration = 0.0
        self.bpm_changes = []
        self.charts = []


def read_msd_from_string(s: str, escape_chars: bool) -> list[list[str]]:
    """Based on the stepmania implementation.

    https://github.com/stepmania/stepmania/blob/5_1-new/src/MsdFile.h
    https://github.com/stepmania/stepmania/blob/5_1-new/src/MsdFile.cpp
    """

    values = []
    param_buffer = StringIO()
    reading_value = False
    i = 0

    while i < len(s):
        if s[i:i + 2] == "//":
            # skip comments entirely
            i = i + 2
            while i < len(s) and s[i] != "\n":
                i += 1
            i += 1
            continue

        # The SM implementation corrects for missing semicolons here,
        # but for now I'm going to assume files are structured correctly.
        # TODO?

        if s[i] == "#" and not reading_value:
            values.append([])
            reading_value = True

        if not reading_value:
            if escape_chars and s[i] == "\\":
                # we're skipping escaped characters, probably to avoid
                # starting a new value when the escaped character is a '#'.
                # This suggests we're treating anything outside a value
                # as a comment, ignoring it.
                i += 2
            else:
                i += 1
            continue

        if s[i] in ":;":
            values[-1].append(param_buffer.getvalue())
            param_buffer = StringIO()

        if s[i] in "#:":
            i += 1
            continue

        if s[i] == ";":
            reading_value = False
            i += 1
            continue

        if escape_chars and s[i] == "\\":
            i += 1

        if i < len(s):
            param_buffer.write(s[i])

        i += 1

    if reading_value:
        raise ValueError("Reached EOF while parsing a value.")

    return values


def process_bpm_changes(sm_song: SMSong, msd_value: list[str]):
    for change_str in msd_value[1].split(","):
        beat_str, new_bpm_str = change_str.split("=")
        # SM does a conversion for values with 'r' in them
        # not sure what that's about, so I'll assume the values are floats
        beat, new_bpm = float(beat_str), float(new_bpm_str)
        if new_bpm <= 0.0:
            raise ValueError(f"invalid BPM value: {new_bpm}")
        sm_song.bpm_changes.append(BPMChange(beat, new_bpm))


def process_notes(sm_song: SMSong, msd_value: list[str]):
    sm_chart = SMChart()
    sm_chart.chart_type = ChartType(msd_value[1].strip())
    sm_chart.description = msd_value[2].strip()
    sm_chart.difficulty = Difficulty(msd_value[3].strip())
    sm_chart.meter = int(msd_value[4])

    for measure_idx, measure_str in enumerate(msd_value[6].split(',')):
        rows = measure_str.strip().split('\n')
        ticks_per_row, remainder = divmod(TICKS_PER_MEASURE, len(rows))
        if remainder != 0:
            raise ValueError(f"Invalid number of rows in measure {measure_idx}: {len(rows)}")
        for row_idx, row_str in enumerate(rows):
            tick = measure_idx * TICKS_PER_MEASURE + row_idx * ticks_per_row
            for col_idx, note_val in enumerate(row_str):
                if note_val != '0':
                    sm_chart.notes.append(Note(tick, col_idx, NoteType(note_val)))

    sm_song.charts.append(sm_chart)


def load_sm(fp: str) -> SMSong:
    with open(fp, "rt", encoding="utf-8") as f:
        data = f.read()

    sm_song = SMSong()

    for msd_value in read_msd_from_string(data, True):
        tag_name = msd_value[0].upper()

        if tag_name == "TITLE":
            sm_song.title = msd_value[1]
        elif tag_name == "SUBTITLE":
            sm_song.sub_title = msd_value[1]
        elif tag_name == "ARTIST":
            sm_song.artist = msd_value[1]
        elif tag_name == "CREDIT":
            sm_song.credit = msd_value[1]
        elif tag_name == "MUSIC":
            sm_song.music_path = msd_value[1]
        elif tag_name == "OFFSET":
            sm_song.start_offset = float(msd_value[1])
        elif tag_name == "SAMPLESTART":
            sm_song.sample_start = float(msd_value[1])  # TODO, see HHMMSSToSeconds in SM
        elif tag_name == "SAMPLELENGTH":
            sm_song.sample_duration = float(msd_value[1])  # TODO ^
        elif tag_name == "BPMS":
            process_bpm_changes(sm_song, msd_value)
        elif tag_name == "NOTES":
            process_notes(sm_song, msd_value)
        else:
            logging.warning(f"Ignoring tag {tag_name}")

    return sm_song
