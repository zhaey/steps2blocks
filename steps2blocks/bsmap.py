import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union, NamedTuple, Any


class Environment(Enum):
    DEFAULT = "DefaultEnvironment"
    ORIGINS = "OriginsEnvironment"
    TRIANGLE = "TriangleEnvironment"
    NICE = "NiceEnvironment"
    BIG_MIRROR = "BigMirrorEnvironment"
    IMAGINE_DRAGONS = "DragonsEnvironment"
    KDA = "KDAEnvironment"
    MONSTERCAT = "MonstercatEnvironment"
    CRAB_RAVE = "CrabRaveEnvironment"
    PANIC = "PanicEnvironment"
    ROCKET = "RocketEnvironment"
    GREEN_DAY = "GreenDayEnvironment"
    GREEN_DAY_GRENADE = "GreenDayGrenadeEnvironment"
    TIMBALAND = "TimbalandEnvironment"
    FITBEAT = "FitBeatEnvironment"
    LINKIN_PARK = "LinkinParkEnvironment"
    BTS = "BTSEnvironment"
    EDM = "EDMEnvironment"
    KALEIDOSCOPE = "KaleidoscopeEnvrionemnt"
    INTERSCOPE = "InterscopeEnvironment"
    SKRILLEX = "SkrillexEnvironment"
    BILLIE = "BillieEnvironment"
    SPOOKY = "HalloweenEnvironment"
    GAGA = "GagaEnvironment"
    WEAVE = "WeaveEnvironment"
    GLASS_DESERT = "GlassDesertEnvironment"


class Difficulty(Enum):
    EASY = ("Easy", 1)
    NORMAL = ("Normal", 3)
    HARD = ("Hard", 5)
    EXPERT = ("Expert", 7)
    EXPERT_PLUS = ("ExpertPlus", 9)

    def __new__(cls, difficulty: str, rank: int):
        obj = object.__new__(cls)
        obj._value_ = difficulty
        obj.difficulty = difficulty
        obj.rank = rank
        return obj


class Characteristic(Enum):
    STANDARD = "Standard"
    NO_ARROWS = "NoArrows"
    ONE_SABER = "OneSaber"
    ROTATE_360 = "360Degree"
    ROTATE_90 = "90Degree"
    LIGHTSHOW = "Lightshow"  # modded
    LAWLESS = "Lawless"  # modded


class BPMEvent(NamedTuple):
    beat: float
    new_bpm: float


class RotationType(Enum):
    EARLY = 0
    LATE = 1


class RotationEvent(NamedTuple):
    beat: float
    type_: RotationType
    angle: float


class NoteColor(Enum):
    LEFT = 0
    RIGHT = 1


class CutDirection(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    UP_LEFT = 4
    UP_RIGHT = 5
    DOWN_LEFT = 6
    DOWN_RIGHT = 7
    ANY = 8


class ColorNote(NamedTuple):
    beat: float
    x: int
    y: int
    color: NoteColor = NoteColor.RIGHT
    direction: CutDirection = CutDirection.ANY
    angle_offset: int = 0


class MidAnchorMode(Enum):
    STRAIGHT = 0
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2


class Slider(NamedTuple):
    beat: float
    x: int
    y: int
    color: NoteColor
    direction: CutDirection
    multiplier: float
    tail_beat: float
    tail_x: int
    tail_y: int
    tail_direction: CutDirection
    tail_multiplier: float
    mid_anchor_mode: MidAnchorMode


class BurstSlider(NamedTuple):
    beat: float
    x: int
    y: int
    color: NoteColor
    direction: CutDirection
    tail_beat: float
    tail_x: int
    tail_y: int
    segment_count: int
    squish_factor: float


class BombNote(NamedTuple):
    beat: float
    x: int
    y: int


class Obstacle(NamedTuple):
    beat: float
    x: int
    y: int
    duration: int  # TODO: check type
    width: int
    height: int


class ColorBoost(NamedTuple):
    beat: float
    enable: bool


class BasicEvent(NamedTuple):
    beat: float
    type_: int  # TODO: make enum? figure out what up
    int_value: int
    float_value: float


@dataclass()
class BPMRegion:
    start_sample_idx: int
    end_sample_idx: int
    start_beat: float
    end_beat: float


@dataclass()
class BPMInfo:
    version: str = "2.0.0"
    sample_count: int = 0
    sample_rate: int = 44100
    regions: list[BPMRegion] = field(default_factory=list)

    @classmethod
    def from_data_dict(cls, data: dict[str, Any]) -> "BPMInfo":
        info = cls()

        if data["_version"] != "2.0.0":
            raise ValueError("Only the 2.0.0 BPMInfo format is currently supported")

        info.version = data["_version"]
        info.sample_count = data["_songSampleCount"]
        info.sample_rate = data["_songFrequency"]
        for region_data in data["_regions"]:
            info.regions.append(BPMRegion(
                region_data["_startSampleIndex"],
                region_data["_endSampleIndex"],
                region_data["_startBeat"],
                region_data["_endBeat"]
            ))

        return info

    def data_dict(self) -> dict[str, Any]:
        data = {
            "_version": self.version,
            "_songSampleCount": self.sample_count,
            "_songFrequency": self.sample_rate,
            "_regions": []
        }

        for region in self.regions:
            data["_regions"].append({
                "_startSampleIndex": region.start_sample_idx,
                "_endSampleIndex": region.end_sample_idx,
                "_startBeat": region.start_beat,
                "_endBeat": region.end_beat
            })

        return data

    def load_regions_from_events(self, events: list[BPMEvent], initial_bpm: Optional[float] = None):
        if initial_bpm is None:
            if events[0].beat != 0.0:
                raise ValueError("Missing bpm at beat 0")
            initial_bpm = events[0].new_bpm

        self.regions.clear()
        self.regions.append(BPMRegion(0, 0, 0.0, 0.0))

        sample_idx = 0.0
        current_bpm = initial_bpm
        for event in events:
            if event.beat == 0.0:
                continue

            sample_idx += self.sample_rate * (event.beat - self.regions[-1].start_beat) / (current_bpm / 60)
            self.regions[-1].end_beat = event.beat
            self.regions[-1].end_sample_idx = int(sample_idx) - 1
            self.regions.append(BPMRegion(int(sample_idx), 0, event.beat, 0.0))

            current_bpm = event.new_bpm

        sample_count = self.sample_count
        if self.sample_count == -1:
            sample_count = sample_idx + self.sample_rate * 5

        self.regions[-1].end_sample_idx = sample_count - 1
        self.regions[-1].end_beat = self.regions[-1].start_beat + (
                sample_count - sample_idx) / self.sample_rate * current_bpm / 60


@dataclass()
class DifficultyBeatmap:
    filename: str = ""
    difficulty: Difficulty = Difficulty.EASY
    note_jump_speed: float = 18.0
    note_jump_offset: float = 0.0

    version: str = ""

    bpm_events: list[BPMEvent] = field(default_factory=list)
    rotation_events: list[RotationEvent] = field(default_factory=list)
    basic_events: list[BasicEvent] = field(default_factory=list)
    colorboost_events: list[ColorBoost] = field(default_factory=list)

    color_notes: list[ColorNote] = field(default_factory=list)
    bomb_notes: list[BombNote] = field(default_factory=list)
    sliders: list[Slider] = field(default_factory=list)
    burst_sliders: list[BurstSlider] = field(default_factory=list)
    obstacles: list[Obstacle] = field(default_factory=list)

    waypoints: list[...] = field(default_factory=list)  # TODO what even is this
    light_color_event_box_groups: list[...] = field(default_factory=list)  # TODO ^
    light_rotation_event_box_groups: list[...] = field(default_factory=list)  # TODO ^
    basic_event_types_with_keywords: ... = None  # TODO ^

    compatible_events: bool = False  # TODO ^

    def load_from_file(self, diff_path: Path) -> None:
        with diff_path.open("rt", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        if data["version"] != "3.0.0":
            raise ValueError("Only the 3.0.0 difficulty format is currently supported")

        self.version = data["version"]

        for bpm_data in data["bpmEvents"]:
            self.bpm_events.append(BPMEvent(bpm_data["b"], bpm_data["m"]))

        for rot_data in data["rotationEvents"]:
            self.rotation_events.append(RotationEvent(
                rot_data["b"],
                RotationType(rot_data["e"]),
                rot_data["r"]
            ))

        for note_data in data["colorNotes"]:
            self.color_notes.append(ColorNote(
                note_data["b"],
                note_data["x"],
                note_data["y"],
                NoteColor(note_data["c"]),
                CutDirection(note_data["d"]),
                note_data["a"]
            ))

        for bomb_data in data["bombNotes"]:
            self.bomb_notes.append(BombNote(
                bomb_data["b"],
                bomb_data["x"],
                bomb_data["y"]
            ))

        for obstacle_data in data["obstacles"]:
            self.obstacles.append(Obstacle(
                obstacle_data["b"],
                obstacle_data["x"],
                obstacle_data["y"],
                obstacle_data["d"],
                obstacle_data["w"],
                obstacle_data["h"],
            ))

        for slider_data in data["sliders"]:
            self.sliders.append(Slider(
                slider_data["b"],
                slider_data["x"],
                slider_data["y"],
                NoteColor(slider_data["c"]),
                CutDirection(slider_data["d"]),
                slider_data["mu"],
                slider_data["tb"],
                slider_data["tx"],
                slider_data["ty"],
                CutDirection(slider_data["tc"]),
                slider_data["tmu"],
                MidAnchorMode(slider_data["m"])
            ))

        for burst_slider_data in data["burstSliders"]:
            self.burst_sliders.append(BurstSlider(
                burst_slider_data["b"],
                burst_slider_data["x"],
                burst_slider_data["y"],
                NoteColor(burst_slider_data["c"]),
                CutDirection(burst_slider_data["d"]),
                burst_slider_data["tb"],
                burst_slider_data["tx"],
                burst_slider_data["ty"],
                burst_slider_data["sc"],
                burst_slider_data["s"]
            ))

        if data["waypoints"]:
            raise ValueError("What even are waypoints?")

        for basic_event_data in data["basicBeatmapEvents"]:
            self.basic_events.append(BasicEvent(
                basic_event_data["b"],
                basic_event_data["et"],
                basic_event_data["i"],
                basic_event_data["f"],
            ))

        for colorboost_event_data in data["colorBoostBeatmapEvents"]:
            self.colorboost_events.append(ColorBoost(
                colorboost_event_data["b"],
                colorboost_event_data["o"]
            ))

        if data["lightColorEventBoxGroups"]:
            raise ValueError("What even are lightColorEventBoxGroups?")

        if data["lightRotationEventBoxGroups"]:
            raise ValueError("What even are lightRotationEventBoxGroups?")

        if data["basicEventTypesWithKeywords"] != {"d": []}:
            raise ValueError("What even are basicEventTypesWithKeywords?")

        self.compatible_events = data["useNormalEventsAsCompatibleEvents"]

    def data_dict(self) -> dict[str, Any]:
        data = {
            "version": self.version,
            "bpmEvents": [],
            "rotationEvents": [],
            "colorNotes": [],
            "bombNotes": [],
            "obstacles": [],
            "sliders": [],
            "burstSliders": [],
            "waypoints": [],
            "basicBeatmapEvents": [],
            "colorBoostBeatmapEvents": [],
            "lightColorEventBoxGroups": [],
            "lightRotationEventBoxGroups": [],
            "basicEventTypesWithKeywords": {
                "d": []
            },
            "useNormalEventsAsCompatibleEvents": self.compatible_events
        }

        for bpm_event in self.bpm_events:
            data["bpmEvents"].append({
                "b": bpm_event.beat,
                "m": bpm_event.new_bpm
            })

        for rot_event in self.rotation_events:
            data["rotationEvents"].append({
                "b": rot_event.beat,
                "e": rot_event.type_.value,
                "r": rot_event.angle
            })

        for note in self.color_notes:
            data["colorNotes"].append({
                "b": note.beat,
                "x": note.x,
                "y": note.y,
                "c": note.color.value,
                "d": note.direction.value,
                "a": note.angle_offset
            })

        for bomb in self.bomb_notes:
            data["bombNotes"].append({
                "b": bomb.beat,
                "x": bomb.x,
                "y": bomb.y
            })

        for obstacle in self.obstacles:
            data["obstacles"].append({
                "b": obstacle.beat,
                "x": obstacle.x,
                "y": obstacle.y,
                "d": obstacle.duration,
                "w": obstacle.width,
                "h": obstacle.height
            })

        for slider in self.sliders:
            data["sliders"].append({
                "b": slider.beat,
                "c": slider.color.value,
                "x": slider.x,
                "y": slider.y,
                "d": slider.direction.value,
                "mu": slider.multiplier,
                "tb": slider.tail_beat,
                "tx": slider.tail_x,
                "ty": slider.tail_y,
                "tc": slider.tail_direction,
                "tmu": slider.tail_multiplier,
                "m": slider.mid_anchor_mode.value
            })

        for burst_slider in self.burst_sliders:
            data["sliders"].append({
                "b": burst_slider.beat,
                "x": burst_slider.x,
                "y": burst_slider.y,
                "c": burst_slider.color.value,
                "d": burst_slider.direction.value,
                "tb": burst_slider.tail_beat,
                "tx": burst_slider.tail_x,
                "ty": burst_slider.tail_y,
                "sc": burst_slider.segment_count,
                "s": burst_slider.squish_factor
            })

        for event in self.basic_events:
            data["basicBeatmapEvents"].append({
                "b": event.beat,
                "et": event.type_,
                "i": event.int_value,
                "f": event.float_value
            })

        for boost_event in self.colorboost_events:
            data["colorBoostBeatmapEvents"].append({
                "b": boost_event.beat,
                "o": boost_event.enable
            })

        return data

    def info_data_dict(self) -> dict[str, Any]:
        return {
            "_difficulty": self.difficulty.difficulty,
            "_difficultyRank": self.difficulty.rank,
            "_beatmapFilename": self.filename,
            "_noteJumpMovementSpeed": self.note_jump_speed,
            "_noteJumpStartBeatOffset": self.note_jump_offset
        }


@dataclass()
class DifficultyBeatmapSet:
    characteristic: Characteristic = Characteristic.STANDARD
    diff_maps: list[DifficultyBeatmap] = field(default_factory=list)

    def data_dict(self) -> dict[str, Any]:
        return {
            "_beatmapCharacteristicName": self.characteristic.value,
            "_difficultyBeatmaps": [dm.info_data_dict() for dm in self.diff_maps]
        }


@dataclass()
class BeatMap:
    version: str = ""
    song_name: str = ""
    song_sub_name: str = ""
    song_author_name: str = ""
    level_author_name: str = ""

    beats_per_minute: float = 120.0
    song_time_offset: float = 0.0
    shuffle: float = 0.0
    shuffle_period: float = 0.0
    preview_start_time: float = 0.0
    preview_duration: float = 0.0

    song_filename: str = ""
    cover_image_filename: str = ""

    environment: Environment = Environment.DEFAULT
    all_directions_environment: Environment = Environment.GLASS_DESERT

    difficulty_beatmap_sets: list[DifficultyBeatmapSet] = field(default_factory=list)

    bpm_info: Optional[BPMInfo] = None

    @classmethod
    def load_from_file(cls, fp: Union[str, Path]) -> "BeatMap":
        if not isinstance(fp, Path):
            fp = Path(fp)

        if fp.is_dir():
            fp /= "Info.dat"

        with fp.open("rt", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        beatmap = BeatMap()
        if data["_version"] != "2.0.0":
            raise ValueError("Only the 2.0.0 Info.dat format is currently supported")

        beatmap.version = data["_version"]
        beatmap.song_name = data["_songName"]
        beatmap.song_sub_name = data["_songSubName"]
        beatmap.song_author_name = data["_songAuthorName"]
        beatmap.level_author_name = data["_levelAuthorName"]
        beatmap.beats_per_minute = data["_beatsPerMinute"]
        beatmap.song_time_offset = data["_songTimeOffset"]
        beatmap.shuffle = data["_shuffle"]
        beatmap.shuffle_period = data["_shufflePeriod"]
        beatmap.preview_start_time = data["_previewStartTime"]
        beatmap.preview_duration = data["_previewDuration"]
        beatmap.song_filename = data["_songFilename"]
        beatmap.cover_image_filename = data["_coverImageFilename"]
        beatmap.environment = Environment(data["_environmentName"])
        beatmap.all_directions_environment = Environment(data["_allDirectionsEnvironmentName"])

        for set_data in data["_difficultyBeatmapSets"]:
            diff_set = DifficultyBeatmapSet(Characteristic(set_data["_beatmapCharacteristicName"]))
            for diff_data in set_data["_difficultyBeatmaps"]:
                diff_map = DifficultyBeatmap(
                    diff_data["_beatmapFilename"],
                    Difficulty(diff_data["_difficulty"]),
                    diff_data["_noteJumpMovementSpeed"],
                    diff_data["_noteJumpStartBeatOffset"]
                )
                diff_path = fp.parent / diff_map.filename
                diff_map.load_from_file(diff_path)
                diff_set.diff_maps.append(diff_map)
            beatmap.difficulty_beatmap_sets.append(diff_set)

        return beatmap

    def data_dict(self) -> dict[str, Any]:
        return {
            "_version": self.version,
            "_songName": self.song_name,
            "_songSubName": self.song_sub_name,
            "_songAuthorName": self.song_author_name,
            "_levelAuthorName": self.level_author_name,
            "_beatsPerMinute": self.beats_per_minute,
            "_songTimeOffset": self.song_time_offset,
            "_shuffle": self.shuffle,
            "_shufflePeriod": self.shuffle_period,
            "_previewStartTime": self.preview_start_time,
            "_previewDuration": self.preview_duration,
            "_songFilename": self.song_filename,
            "_coverImageFilename": self.cover_image_filename,
            "_environmentName": self.environment.value,
            "_allDirectionsEnvironmentName": self.all_directions_environment.value,
            "_difficultyBeatmapSets": [dbs.data_dict() for dbs in self.difficulty_beatmap_sets]
        }

    def save_to_disk(self, path: Union[str, Path]):
        if not isinstance(path, Path):
            path = Path(path)

        path.mkdir(exist_ok=True)

        info_path = path / "Info.dat"
        with info_path.open("wt", encoding="utf-8") as info_file:
            json.dump(self.data_dict(), info_file)

        if self.bpm_info is not None:
            bpm_path = path / "BPMInfo.dat"
            with bpm_path.open("wt", encoding="utf-8") as bpm_file:
                json.dump(self.bpm_info.data_dict(), bpm_file)

        for dbs in self.difficulty_beatmap_sets:
            for dm in dbs.diff_maps:
                diff_path = path / dm.filename
                with diff_path.open("wt", encoding="utf-8") as diff_file:
                    json.dump(dm.data_dict(), diff_file)
