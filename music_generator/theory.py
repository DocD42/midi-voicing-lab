from __future__ import annotations

from dataclasses import dataclass, field
import re

NOTE_TO_PC = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}

PC_TO_NOTE = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}

BUILTIN_PROGRESSIONS = [
    "Dm7 G7 Cmaj7 A7",
    "Am7 D7 Gmaj7 Em7",
    "Fm7 Bb7 Ebmaj7 C7",
    "Em7 A7 Dmaj7 Bm7",
    "Cm7 F7 Bbmaj7 G7",
    "Am7 Cmaj7 Fmaj7 G7",
    "Em7 Bm7 Cmaj7 D7",
]

CHORD_RE = re.compile(r"^\s*([A-G](?:#|b)?)([^\s/]*)(?:/([A-G](?:#|b)?))?\s*$")


@dataclass(frozen=True)
class ChordSymbol:
    symbol: str
    root_name: str
    root_pc: int
    quality: str
    extensions: set[str] = field(default_factory=set)
    alterations: set[str] = field(default_factory=set)
    bass_pc: int | None = None


def parse_progression(text: str) -> list[ChordSymbol]:
    if not text or not text.strip():
        raise ValueError("Bitte gib mindestens einen Akkord ein.")

    tokens = [
        token.strip()
        for token in re.split(r"[|,;\n\t\r ]+", text)
        if token.strip()
    ]
    if not tokens:
        raise ValueError("Es wurden keine gültigen Akkorde erkannt.")

    return [parse_chord(token) for token in tokens]


def parse_chord(token: str) -> ChordSymbol:
    match = CHORD_RE.match(token)
    if not match:
        raise ValueError(f"Ungültiges Akkordformat: {token}")

    root_name, descriptor, bass_name = match.groups()
    if root_name not in NOTE_TO_PC:
        raise ValueError(f"Unbekannter Grundton: {root_name}")

    quality = classify_quality(descriptor)
    extensions, alterations = parse_color_tones(descriptor)
    bass_pc = NOTE_TO_PC[bass_name] if bass_name else None

    return ChordSymbol(
        symbol=token,
        root_name=root_name,
        root_pc=NOTE_TO_PC[root_name],
        quality=quality,
        extensions=extensions,
        alterations=alterations,
        bass_pc=bass_pc,
    )


def classify_quality(descriptor: str) -> str:
    d = descriptor.lower()

    if "m7b5" in d or "ø" in d:
        return "half_dim"
    if "dim7" in d or "o7" in d:
        return "dim7"
    if "dim" in d or "o" in d:
        return "dim"
    if "sus2" in d:
        return "sus2"
    if "sus" in d:
        return "sus4"
    if d in {"5", "(5)"}:
        return "power"
    if "maj7" in d or "ma7" in d or "∆7" in d:
        return "maj7"

    minor_markers = ("m", "min", "-")
    is_minor = d.startswith(minor_markers) and "maj" not in d
    contains_seventh = any(n in d for n in ("7", "9", "11", "13"))

    if is_minor and contains_seventh:
        return "min7"
    if is_minor:
        return "min"
    if contains_seventh:
        return "dom7"
    return "maj"


def parse_color_tones(descriptor: str) -> tuple[set[str], set[str]]:
    d = descriptor.lower()

    alterations = set(re.findall(r"(b9|#9|#11|b13|b5|#5)", d))

    extension_tokens = {
        "add9": "9",
        "add11": "11",
        "add13": "13",
    }

    extensions: set[str] = set()

    for literal, mapped in extension_tokens.items():
        if literal in d:
            extensions.add(mapped)

    for token in ("13", "11", "9", "6"):
        if token in d:
            extensions.add(token)

    return extensions, alterations


def chord_tone_intervals(quality: str) -> list[int]:
    quality_map = {
        "maj": [0, 4, 7],
        "min": [0, 3, 7],
        "maj7": [0, 4, 7, 11],
        "min7": [0, 3, 7, 10],
        "dom7": [0, 4, 7, 10],
        "half_dim": [0, 3, 6, 10],
        "dim": [0, 3, 6],
        "dim7": [0, 3, 6, 9],
        "sus2": [0, 2, 7, 10],
        "sus4": [0, 5, 7, 10],
        "power": [0, 7],
    }
    if quality not in quality_map:
        raise ValueError(f"Unbekannte Akkordqualität: {quality}")
    return quality_map[quality]


def degree_to_semitone(token: str) -> int:
    mapping = {
        "6": 9,
        "9": 14,
        "11": 17,
        "13": 21,
        "b9": 13,
        "#9": 15,
        "#11": 18,
        "b13": 20,
        "b5": 6,
        "#5": 8,
    }
    if token not in mapping:
        raise ValueError(f"Unbekannter Degree: {token}")
    return mapping[token]


def quality_bucket(quality: str) -> str:
    if quality in {"min", "min7", "half_dim"}:
        return "minor"
    if quality in {"dom7", "sus2", "sus4"}:
        return "dominant"
    return "major"


def is_minor_quality(quality: str) -> bool:
    return quality in {"min", "min7", "half_dim"}


def is_dominant_quality(quality: str) -> bool:
    return quality in {"dom7", "sus2", "sus4"}


def pc_name(pc: int) -> str:
    return PC_TO_NOTE[pc % 12]
