import unittest
import pytest

from magicmovie.lib.spreadsheet import Sheet




def test_sheet():

    sheet = Sheet(rows=[["Foo", "Bar"], ["a", "b"], ["c", "d"]])

    assert sheet.get_cell(2, "Foo") ==  "a"
    assert sheet.get_cell(3, "Bar") == "d"


