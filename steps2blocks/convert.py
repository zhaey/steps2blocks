import logging

from bsmap import Difficulty as BSDiff, BeatMap, BPMEvent, BPMInfo, DifficultyBeatmapSet, DifficultyBeatmap, \
    ColorNote, BombNote
from smmap import Difficulty as SMDiff, SMSong, ChartType, TICKS_PER_BEAT, NoteType

DIFF_MAPPING = {
    SMDiff.BEGINNER: BSDiff.EASY,
    SMDiff.EASY: BSDiff.NORMAL,
    SMDiff.MEDIUM: BSDiff.HARD,
    SMDiff.HARD: BSDiff.EXPERT,
    SMDiff.CHALLENGE: BSDiff.EXPERT_PLUS
}


def beatmap_from_sm(sm: SMSong, sample_count: int = -1, sample_rate: int = 44100) -> BeatMap:
    bm = BeatMap()
    bm.version = "2.0.0"
    bm.song_name = sm.title
    bm.song_sub_name = sm.sub_title
    bm.song_author_name = sm.artist
    bm.level_author_name = sm.credit
    bm.song_filename = sm.music_path
    bm.song_time_offset = sm.start_offset
    bm.preview_start_time = sm.sample_start
    bm.preview_duration = sm.sample_duration

    bpm_events = []
    for bpm_change in sm.bpm_changes:
        bpm_events.append(BPMEvent(bpm_change.beat, bpm_change.new_bpm))

    bm.beats_per_minute = bpm_events[0].new_bpm

    if len(bpm_events) > 1:
        bpm_info = BPMInfo()
        bpm_info.sample_rate = sample_rate
        bpm_info.sample_count = sample_count
        bpm_info.load_regions_from_events(bpm_events)
        bm.bpm_info = bpm_info

    diff_set = DifficultyBeatmapSet()
    for chart in sm.charts:
        if chart.chart_type is not ChartType.DANCE_SINGLE:
            logging.warning(
                f"Skipping {chart.chart_type}:{chart.difficulty} "
                f"because it is not dance-single."
            )

        logging.info(f"Processing {chart.chart_type}:{chart.difficulty}")

        diff_map = DifficultyBeatmap()
        diff_map.version = "3.0.0"
        diff_map.difficulty = DIFF_MAPPING[chart.difficulty]
        diff_map.bpm_events = bpm_events[:]
        diff_map.filename = f"{diff_map.difficulty.difficulty}{diff_set.characteristic.value}.dat"

        for sm_note in chart.notes:
            beat = sm_note.tick / TICKS_PER_BEAT
            if sm_note.note_type is NoteType.NORMAL:
                diff_map.color_notes.append(ColorNote(
                    beat,
                    sm_note.column,
                    0
                ))
            elif sm_note.note_type is NoteType.MINE:
                diff_map.bomb_notes.append(BombNote(
                    beat,
                    sm_note.column,
                    0
                ))
            else:
                logging.warning(
                    f"Ignoring note on beat {beat}: "
                    f"note type {sm_note.note_type} is not supported"
                )

        diff_set.diff_maps.append(diff_map)
    bm.difficulty_beatmap_sets.append(diff_set)
    return bm
