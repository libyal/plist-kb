#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Property List file schema extractor."""

import io
import os
import unittest

import artifacts

from plistrc import schema_extractor

from tests import test_lib


class PropertyListSchemaExtractorTest(test_lib.BaseTestCase):
  """Tests for the Property List file schema extractor."""

  # pylint: disable=protected-access

  _ARTIFACT_DEFINITIONS_PATH = os.path.join(
        os.path.dirname(artifacts.__file__), 'data')
  if not os.path.isdir(_ARTIFACT_DEFINITIONS_PATH):
    _ARTIFACT_DEFINITIONS_PATH = os.path.join(
        '/', 'usr', 'share', 'artifacts')

  def testInitialize(self):
    """Tests the __init__ function."""
    test_extractor = schema_extractor.PropertyListSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)
    self.assertIsNotNone(test_extractor)

  # TODO: add tests for _CheckByteOrderMark

  def testCheckSignature(self):
    """Tests the _CheckSignature function."""
    test_extractor = schema_extractor.PropertyListSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)

    file_object = io.BytesIO(b'bplist0')
    result = test_extractor._CheckSignature(file_object)
    self.assertTrue(result)

    file_object = io.BytesIO(b'\xff' * 16)
    result = test_extractor._CheckSignature(file_object)
    self.assertFalse(result)

  # TODO: add tests for _GetPropertyListSchemaFromFileObject
  # TODO: add tests for GetDisplayPath
  # TODO: add tests for ExtractSchemas
  # TODO: add tests for FormatSchema


if __name__ == '__main__':
  unittest.main()
