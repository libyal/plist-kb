#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YAML-based property list definitions file."""

import unittest

from plistrc import yaml_definitions_file

from tests import test_lib


class YAMLPropertyListDefinitionsFileTest(test_lib.BaseTestCase):
  """Tests for the YAML-based property list definitions file."""

  # pylint: disable=protected-access

  _TEST_YAML = {
      'artifact_definition': 'MacOSAirportPreferencesPlistFile',
      'property_list_identifier': 'com.apple.airport.preferences.plist'}

  def testReadPropertyListDefinition(self):
    """Tests the _ReadPropertyListDefinition function."""
    test_definitions_file = (
        yaml_definitions_file.YAMLPropertyListDefinitionsFile())

    definitions = (
        test_definitions_file._ReadPropertyListDefinition(self._TEST_YAML))

    self.assertIsNotNone(definitions)
    self.assertEqual(
        definitions.artifact_definition, 'MacOSAirportPreferencesPlistFile')
    self.assertEqual(
        definitions.property_list_identifier,
        'com.apple.airport.preferences.plist')

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadPropertyListDefinition({})

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadPropertyListDefinition({
          'artifact_definition': 'MacOSAirportPreferencesPlistFile'})

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadPropertyListDefinition({
          'property_list_identifier': 'com.apple.airport.preferences.plist'})

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadPropertyListDefinition({
          'bogus': 'test'})

  def testReadFromFileObject(self):
    """Tests the _ReadFromFileObject function."""
    test_file_path = self._GetTestFilePath(['known_property_lists.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_definitions_file = (
        yaml_definitions_file.YAMLPropertyListDefinitionsFile())

    with open(test_file_path, 'r', encoding='utf-8') as file_object:
      definitions = list(test_definitions_file._ReadFromFileObject(file_object))

    self.assertEqual(len(definitions), 1)

  def testReadFromFile(self):
    """Tests the ReadFromFile function."""
    test_file_path = self._GetTestFilePath(['known_property_lists.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_definitions_file = (
        yaml_definitions_file.YAMLPropertyListDefinitionsFile())

    definitions = list(test_definitions_file.ReadFromFile(test_file_path))

    self.assertEqual(len(definitions), 1)

    self.assertEqual(
        definitions[0].artifact_definition,
        'MacOSAirportPreferencesPlistFile')


if __name__ == '__main__':
  unittest.main()
