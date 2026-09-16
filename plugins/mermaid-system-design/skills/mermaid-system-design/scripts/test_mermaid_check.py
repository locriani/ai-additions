#!/usr/bin/env python3
"""Tests for the pure parts of mermaid-check: no mmdc, no subprocess, no network."""

import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "mermaid_check", Path(__file__).with_name("mermaid-check.py")
)
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)


class ExtractBlocks(unittest.TestCase):
    def test_single_block_reports_first_content_line(self):
        text = "# Title\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
        self.assertEqual(
            mc.extract_blocks(text), [(4, "flowchart LR\n  A --> B\n")]
        )

    def test_other_fences_are_ignored(self):
        text = "```text\nflowchart LR\n  A --> B\n```\n\n```python\nprint(1)\n```\n"
        self.assertEqual(mc.extract_blocks(text), [])

    def test_line_numbers_survive_preceding_blocks(self):
        text = (
            "```text\nnot a diagram\n```\n"       # lines 1-3
            "\nprose\n\n"                          # lines 4-6
            "```mermaid\nflowchart TB\n  X --> Y\n```\n"  # fence line 7, content line 8
        )
        blocks = mc.extract_blocks(text)
        self.assertEqual([line for line, _ in blocks], [8])
        self.assertEqual(blocks[0][1], "flowchart TB\n  X --> Y\n")

    def test_multiple_blocks_keep_their_own_offsets(self):
        text = (
            "```mermaid\nA\n```\n"        # content line 2
            "between\n"                   # line 4
            "```mermaid\nB\nC\n```\n"     # content line 6
        )
        self.assertEqual(mc.extract_blocks(text), [(2, "A\n"), (6, "B\nC\n")])

    def test_unclosed_fence_is_dropped(self):
        text = "```mermaid\nflowchart LR\n  A --> B\n"
        self.assertEqual(mc.extract_blocks(text), [])

    def test_empty_block_is_dropped(self):
        self.assertEqual(mc.extract_blocks("```mermaid\n\n   \n```\n"), [])

    def test_info_string_is_case_insensitive(self):
        self.assertEqual(mc.extract_blocks("```Mermaid\nA\n```\n"), [(2, "A\n")])

    def test_tilde_fences(self):
        self.assertEqual(mc.extract_blocks("~~~mermaid\nA\n~~~\n"), [(2, "A\n")])

    def test_tildes_do_not_close_backticks(self):
        text = "```mermaid\nA\n~~~\nB\n```\n"
        self.assertEqual(mc.extract_blocks(text), [(2, "A\n~~~\nB\n")])

    def test_longer_fence_survives_inner_triple_backticks(self):
        text = "````mermaid\nA\n```\nB\n````\n"
        self.assertEqual(mc.extract_blocks(text), [(2, "A\n```\nB\n")])

    def test_indented_fence(self):
        self.assertEqual(mc.extract_blocks("  ```mermaid\n  A\n  ```\n"), [(2, "  A\n")])


class TrimTrace(unittest.TestCase):
    def test_stack_frames_are_dropped(self):
        msg = (
            "Error: Parse error on line 3:\n"
            "...A[Svc (v2)] --> D\n"
            "-------^\n"
            "Expecting 'SQE', 'TEXT', got 'PS'\n"
            "Parser.parseError (https://x.invalid/chunk-6HLVECFW.mjs:1523:21)\n"
            "    at #evaluate (file:///x/ExecutionContext.js:402:19)\n"
            "    at async CdpPage.$eval (file:///x/Page.js:462:20)"
        )
        self.assertEqual(
            mc.trim_trace(msg).splitlines(),
            [
                "Error: Parse error on line 3:",
                "...A[Svc (v2)] --> D",
                "-------^",
                "Expecting 'SQE', 'TEXT', got 'PS'",
            ],
        )

    def test_message_with_no_frames_is_kept(self):
        self.assertEqual(mc.trim_trace("Error: browser closed"), "Error: browser closed")

    def test_message_that_is_only_frames_falls_back_to_the_whole_thing(self):
        msg = "    at foo (file:///x.js:1:2)"
        self.assertEqual(mc.trim_trace(msg), msg.strip())


class Absolutize(unittest.TestCase):
    def test_block_relative_line_becomes_file_line(self):
        # Block content starts at file line 10; Mermaid's line 1 is that line.
        self.assertEqual(mc.absolutize("Parse error on line 1:", 10), "Parse error on line 10:")
        self.assertEqual(mc.absolutize("Parse error on line 3:", 10), "Parse error on line 12:")

    def test_first_line_of_first_block_is_identity(self):
        self.assertEqual(mc.absolutize("Parse error on line 1:", 1), "Parse error on line 1:")

    def test_untouched_lines_pass_through(self):
        msg = 'Parse error on line 2:\n...t LR  A["Svc" --> B\n---------^\nExpecting SQE, got CYLINDERSTART'
        out = mc.absolutize(msg, 30).splitlines()
        self.assertEqual(out[0], "Parse error on line 31:")
        self.assertEqual(out[1:], msg.splitlines()[1:])

    def test_message_without_a_line_number_is_unchanged(self):
        self.assertEqual(mc.absolutize("Error: browser closed", 7), "Error: browser closed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
