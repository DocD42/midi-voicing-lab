import unittest

from music_generator.theory import parse_chord, parse_progression
from music_generator.voicings import analyze_cadences


class TheoryTests(unittest.TestCase):
    def test_parse_basic_chord(self):
        chord = parse_chord("Cmaj7")
        self.assertEqual(chord.root_pc, 0)
        self.assertEqual(chord.quality, "maj7")

    def test_parse_extensions(self):
        chord = parse_chord("G7b9#11")
        self.assertEqual(chord.quality, "dom7")
        self.assertIn("b9", chord.alterations)
        self.assertIn("#11", chord.alterations)

    def test_parse_progression(self):
        progression = parse_progression("Dm7 G7 Cmaj7")
        self.assertEqual(len(progression), 3)

    def test_detect_ii_v_i(self):
        progression = parse_progression("Dm7 G7 Cmaj7")
        roles = analyze_cadences(progression)
        self.assertEqual(roles, ["ii", "V", "I"])


if __name__ == "__main__":
    unittest.main()
