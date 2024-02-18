#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the property list decoders."""

import plistlib
import unittest

from plistrc import decoders

from tests import test_lib


class NSKeyedArchiverDecoderTest(test_lib.BaseTestCase):
  """Tests for the decoder for NSKeyedArchiver encoded plists."""

  def testDecode(self):
    """Tests the Decode function."""
    test_file_path = self._GetTestFilePath(['NSKeyedArchiver.plist'])
    self._SkipIfPathNotExists(test_file_path)

    test_decoder = decoders.NSKeyedArchiverDecoder()

    with open(test_file_path, 'rb') as file_object:
      encoded_plist = plistlib.load(file_object)

    decoded_plist = test_decoder.Decode(encoded_plist)
    self.assertIsNotNone(decoded_plist)
    self.assertIn('root', decoded_plist)

    root_item = decoded_plist['root']
    self.assertIn('MyString', root_item)
    self.assertEqual(root_item['MyString'], 'Some string')


if __name__ == '__main__':
  unittest.main()
