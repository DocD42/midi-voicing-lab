import io
import unittest

import mido

from music_generator.midi_export import arrangement_to_midi
from music_generator.theory import parse_progression
from music_generator.voicings import generate_arrangement


class VoicingIntegrationTests(unittest.TestCase):
    def test_arrangement_splits_left_and_right_hand(self):
        chords = parse_progression("Dm7 G7 Cmaj7 A7")
        arrangement = generate_arrangement(
            chords=chords,
            style="jazz",
            complexity=0.72,
            beats_per_chord=4,
            tempo=96,
            seed=123,
        )

        self.assertGreater(len(arrangement.events), 0)
        for event in arrangement.events:
            self.assertGreater(len(event.left_hand), 0)
            self.assertGreater(len(event.right_hand), 0)
            self.assertLess(max(event.left_hand), min(event.right_hand))

    def test_midi_export_contains_lh_and_rh_tracks(self):
        chords = parse_progression("Am7 D7 Gmaj7")
        arrangement = generate_arrangement(
            chords=chords,
            style="soul",
            complexity=0.65,
            beats_per_chord=4,
            tempo=92,
            seed=77,
        )
        midi_bytes = arrangement_to_midi(arrangement, tempo=92)

        midi = mido.MidiFile(file=io.BytesIO(midi_bytes))
        self.assertEqual(len(midi.tracks), 3)

        track_names = []
        for track in midi.tracks:
            for message in track:
                if message.type == "track_name":
                    track_names.append(message.name)

        self.assertIn("Piano LH", track_names)
        self.assertIn("Piano RH", track_names)

    def test_humanize_changes_timing_and_velocity_with_seed(self):
        chords = parse_progression("Dm7 G7 Cmaj7 A7")
        plain = generate_arrangement(
            chords=chords,
            style="jazz",
            complexity=0.7,
            beats_per_chord=4,
            tempo=100,
            seed=111,
            humanize=False,
            humanize_amount=0.6,
        )
        humanized = generate_arrangement(
            chords=chords,
            style="jazz",
            complexity=0.7,
            beats_per_chord=4,
            tempo=100,
            seed=111,
            humanize=True,
            humanize_amount=0.6,
        )

        self.assertEqual(len(plain.events), len(humanized.events))
        timing_different = any(
            abs(base.start_beat - mod.start_beat) > 1e-9
            for base, mod in zip(plain.events, humanized.events)
        )
        velocity_different = any(
            base.velocity != mod.velocity for base, mod in zip(plain.events, humanized.events)
        )
        self.assertTrue(timing_different or velocity_different)


if __name__ == "__main__":
    unittest.main()
