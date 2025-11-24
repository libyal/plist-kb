#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the property list decoders."""

import plistlib
import unittest

from plistrc import decoders

from tests import test_lib


class NSKeyedArchiverDecoderTest(test_lib.BaseTestCase):
  """Tests for the decoder for NSKeyedArchiver encoded plists."""

  # TODO: add tests for _DecodeCompositeObject.
  # TODO: add tests for _DecodeNSArray.
  # TODO: add tests for _DecodeNSData.
  # TODO: add tests for _DecodeNSDate.
  # TODO: add tests for _DecodeNSDictionary.
  # TODO: add tests for _DecodeNSHashTable.
  # TODO: add tests for _DecodeNSNull.
  # TODO: add tests for _DecodeNSObject.
  # TODO: add tests for _DecodeNSString.
  # TODO: add tests for _DecodeNSURL.
  # TODO: add tests for _DecodeNSUUID.
  # TODO: add tests for _DecodeObject.
  # TODO: add tests for _GetClassName.
  # TODO: add tests for _GetPlistUID.

  def testDecode(self):
    """Tests the Decode function."""
    test_file_path = self._GetTestFilePath(['NSKeyedArchiver.plist'])
    self._SkipIfPathNotExists(test_file_path)

    test_decoder = decoders.NSKeyedArchiverDecoder()

    with open(test_file_path, 'rb') as file_object:
      encoded_plist = plistlib.load(file_object)

    decoded_plist = test_decoder.Decode(encoded_plist)
    self.assertIsNotNone(decoded_plist)
    self.assertIn('MyString', decoded_plist)
    self.assertEqual(decoded_plist['MyString'], 'Some string')

  def testIsEncoded(self):
    """Tests the IsEncoded function."""
    test_file_path = self._GetTestFilePath(['NSKeyedArchiver.plist'])
    self._SkipIfPathNotExists(test_file_path)

    test_decoder = decoders.NSKeyedArchiverDecoder()

    with open(test_file_path, 'rb') as file_object:
      encoded_plist = plistlib.load(file_object)

    result = test_decoder.IsEncoded(encoded_plist)
    self.assertTrue(result)


if __name__ == '__main__':
  unittest.main()
