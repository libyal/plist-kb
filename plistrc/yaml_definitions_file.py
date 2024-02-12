# -*- coding: utf-8 -*-
"""YAML-based property list definitions file."""

import yaml

from plistrc import resources


class YAMLPropertyListDefinitionsFile(object):
  """YAML-based property list definitions file.

  A YAML-based property list definitions file contains one or more property list
  definitions. A property list definition consists of:

  artifact_definition: MacOSAirportPreferencesPlistFile
  property_list_identifier: com.apple.airport.preferences.plist

  Where:
  * artifact_definition, name of the corresponding Digital Forensics Artifact
      definition.
  * property_list_identifier, identifier of the property list.
  """

  _SUPPORTED_KEYS = frozenset([
      'artifact_definition',
      'property_list_identifier'])

  def _ReadPropertyListDefinition(self, yaml_property_list_definition):
    """Reads a property list definition from a dictionary.

    Args:
      yaml_property_list_definition (dict[str, object]): YAML property list
           definition values.

    Returns:
      PropertyListDefinition: property list definition.

    Raises:
      RuntimeError: if the format of the formatter definition is not set
          or incorrect.
    """
    if not yaml_property_list_definition:
      raise RuntimeError('Missing property list definition values.')

    different_keys = set(yaml_property_list_definition) - self._SUPPORTED_KEYS
    if different_keys:
      different_keys = ', '.join(different_keys)
      raise RuntimeError('Undefined keys: {0:s}'.format(different_keys))

    artifact_definition = yaml_property_list_definition.get(
        'artifact_definition', None)
    if not artifact_definition:
      raise RuntimeError(
          'Invalid property list definition missing format identifier.')

    property_list_identifier = yaml_property_list_definition.get(
        'property_list_identifier', None)
    if not property_list_identifier:
      raise RuntimeError(
          'Invalid property list definition missing property list identifier.')

    property_list_definition = resources.PropertyListDefinition()
    property_list_definition.artifact_definition = artifact_definition
    property_list_definition.property_list_identifier = property_list_identifier

    return property_list_definition

  def _ReadFromFileObject(self, file_object):
    """Reads the event formatters from a file-like object.

    Args:
      file_object (file): formatters file-like object.

    Yields:
      PropertyListDefinition: property list definition.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    for yaml_property_list_definition in yaml_generator:
      yield self._ReadPropertyListDefinition(yaml_property_list_definition)

  def ReadFromFile(self, path):
    """Reads the event formatters from a YAML file.

    Args:
      path (str): path to a formatters file.

    Yields:
      PropertyListDefinition: property list definition.
    """
    with open(path, 'r', encoding='utf-8') as file_object:
      for yaml_property_list_definition in self._ReadFromFileObject(
          file_object):
        yield yaml_property_list_definition
