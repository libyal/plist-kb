# -*- coding: utf-8 -*-
"""Property list file schema extractor."""

import datetime
import logging
import os
import plistlib
import xml

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfimagetools import definitions as dfimagetools_definitions
from dfimagetools import file_entry_lister

from plistrc import decoders
from plistrc import resources


class PropertyListSchemaExtractor(object):
  """Property list file schema extractor."""

  _COMPOSITE_VALUE_TYPES = frozenset(['array', 'dict'])

  _MAXIMUM_FILE_SIZE = 64 * 1024 * 1024

  _MINIMUM_FILE_SIZE = 8

  _UTF8_BYTE_ORDER_MARK = b'\xef\xbb\xbf'
  _UTF16BE_BYTE_ORDER_MARK = b'\xfe\xff'
  _UTF16LE_BYTE_ORDER_MARK = b'\xff\xfe'
  _UTF32BE_BYTE_ORDER_MARK = b'\x00\x00\xfe\xff'
  _UTF32LE_BYTE_ORDER_MARK = b'\xff\xfe\x00\x00'

  def __init__(self, artifact_definitions, mediator=None):
    """Initializes a property list file schema extractor.

    Args:
      artifact_definitions (str): path to a single artifact definitions
          YAML file or a directory of definitions YAML files.
      mediator (Optional[dfvfs.VolumeScannerMediator]): a volume scanner
          mediator.
    """
    super(PropertyListSchemaExtractor, self).__init__()
    self._artifacts_registry = artifacts_registry.ArtifactDefinitionsRegistry()
    self._mediator = mediator
    self._nskeyedarchiver_decoder = decoders.NSKeyedArchiverDecoder()

    if artifact_definitions:
      reader = artifacts_reader.YamlArtifactsReader()
      if os.path.isdir(artifact_definitions):
        self._artifacts_registry.ReadFromDirectory(reader, artifact_definitions)
      elif os.path.isfile(artifact_definitions):
        self._artifacts_registry.ReadFromFile(reader, artifact_definitions)

  def _CheckByteOrderMark(self, data):
    """Determines if a property list starts with a byte-order-mark.

    Args:
      data (bytes): data.

    Returns:
      tuple[int, str]: size of the byte-order-mark or 0 if no byte-order-mark
          was detected and encoding.
    """
    if data.startswith(self._UTF32BE_BYTE_ORDER_MARK):
      return 4, 'utf-32-be'

    if data.startswith(self._UTF32LE_BYTE_ORDER_MARK):
      return 4, 'utf-32-le'

    if data.startswith(self._UTF16BE_BYTE_ORDER_MARK):
      return 2, 'utf-16-be'

    if data.startswith(self._UTF16LE_BYTE_ORDER_MARK):
      return 2, 'utf-16-le'

    if data.startswith(self._UTF8_BYTE_ORDER_MARK):
      return 3, 'utf-8'

    return 0, 'ascii'

  def _CheckSignature(self, file_object):
    """Checks the signature of a given file-like object.

    Args:
      file_object (dfvfs.FileIO): file-like object of the property list.

    Returns:
      bool: True if the signature matches that of a property list, False
          otherwise.
    """
    if not file_object:
      return False

    file_object.seek(0, os.SEEK_SET)
    file_data = file_object.read()

    if file_data.startswith(b'bplist0'):
      return True

    byte_order_mark_size, encoding = self._CheckByteOrderMark(file_data)

    xml_signature = '<?xml '.encode(encoding)
    is_xml = file_data[byte_order_mark_size:].startswith(xml_signature)
    if not is_xml:
      # Preserve the byte-order-mark for plistlib.
      file_data = b''.join([
          file_data[:byte_order_mark_size],
          file_data[byte_order_mark_size:].lstrip()])
      is_xml = file_data[byte_order_mark_size:].startswith(xml_signature)
      if is_xml:
        logging.info('XML plist file with leading whitespace')

    if is_xml:
      plist_footer = '</plist>'.encode(encoding)
      file_data = file_data.rstrip()

      if not file_data.endswith(plist_footer):
        return False

    return is_xml

  def _FormatSchemaAsYAML(self, schema):
    """Formats a schema into YAML.

    Args:
      schema (PropertyDefinition): schema.

    Returns:
      str: schema formatted as YAML.
    """
    tables = []

    for property_definition in self._GetDictPropertyDefinitions(schema):
      if not property_definition.schema:
        continue

      name = property_definition.key_path or '.'

      table = [
          f'table: {name:s}',
          'columns:']

      for value_property_definition in sorted(
          property_definition.schema, key=lambda definition: definition.name):
        table.append(f'- name: {value_property_definition.name:s}')

        if value_property_definition.value_type != 'array':
          value_type = value_property_definition.value_type
        else:
          array_value_types = ','.join(sorted({
              definition.value_type
              for definition in value_property_definition.schema}))
          value_type = f'array[{array_value_types:s}]'

        table.append(f'  value_type: {value_type:s}')

      if table not in tables:
        tables.append(table)

    lines = [
        '# PList-kb property list schema.',
        '---']

    for table in sorted(tables):
      lines.extend(table)
      lines.append('---')

    return '\n'.join(lines)

  def _GetDictPropertyDefinitions(self, property_definition):
    """Retrieves the dictionary property definitions.

    Yields:
      PropertyDefinition: dict property definition.
    """
    if property_definition.value_type == 'dict':
      yield property_definition

    for value_property_definition in property_definition.schema:
      if value_property_definition.value_type in self._COMPOSITE_VALUE_TYPES:
        yield from self._GetDictPropertyDefinitions(
            value_property_definition)

  def _GetPropertyListKeyPath(self, key_path_segments):
    """Retrieves a property list key path.

    Args:
      key_path_segments (list[str]): property list key path segments.

    Returns:
      str: property list key path.
    """
    # TODO: escape '.' in path segments
    return '.'.join(key_path_segments)

  def _GetPropertyListSchemaFromItem(self, item, key_path_segments):
    """Retrieves schema from given property list item.

    Args:
      item (object): property list item.
      key_path_segments (list[str]): property list key path segments.

    Returns:
      PropertyDefinition: property definition of the item.

    Raises:
      RuntimeError: if the item is not supported.
    """
    property_definition = resources.PropertyDefinition()
    property_definition.key_path = self._GetPropertyListKeyPath(
        key_path_segments)
    property_definition.value_type = self._GetPropertyListValueType(item)

    if isinstance(item, dict):
      for key, value in item.items():
        value_type = self._GetPropertyListValueType(item)
        if value_type not in self._COMPOSITE_VALUE_TYPES:
          value_property_definition = resources.PropertyDefinition()
          value_property_definition.name = key
          value_property_definition.value_type = value_type
        else:
          value_key_path_segments = list(key_path_segments)
          value_key_path_segments.append(key)

          value_property_definition = self._GetPropertyListSchemaFromItem(
              value, value_key_path_segments)
          value_property_definition.name = key

        property_definition.schema.append(value_property_definition)

    elif isinstance(item, list):
      for value in item:
        value_type = self._GetPropertyListValueType(item)
        if value_type not in self._COMPOSITE_VALUE_TYPES:
          value_property_definition = resources.PropertyDefinition()
          value_property_definition.value_type = value_type
        else:
          value_property_definition = self._GetPropertyListSchemaFromItem(
              value, key_path_segments)

        property_definition.schema.append(value_property_definition)

    return property_definition

  def _GetPropertyListValueType(self, item):
    """Retrieves property list value type.

    Args:
      item (object): property list item.

    Yields:
      str: value type.

    Raises:
      RuntimeError: if the value type is not supported.
    """
    if item is None:
      return 'null'
    if isinstance(item, bytes):
      return 'data'
    if isinstance(item, dict):
      return 'dict'
    if isinstance(item, float):
      return 'real'
    if isinstance(item, int):
      return 'int'
    if isinstance(item, list):
      return 'array'
    if isinstance(item, str):
      return 'string'
    if isinstance(item, plistlib.UID):
      return 'UID'
    if isinstance(item, datetime.datetime):
      return 'date'

    value_type = type(item)
    raise RuntimeError(f'Unsupported value type: {value_type!s}')

  def GetDisplayPath(self, path_segments, data_stream_name=None):
    """Retrieves a path to display.

    Args:
      path_segments (list[str]): path segments of the full path of the file
          entry.
      data_stream_name (Optional[str]): name of the data stream.

    Returns:
      str: path to display.
    """
    display_path = ''

    path_segments = [
        segment.translate(
            dfimagetools_definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)
        for segment in path_segments]
    display_path = ''.join([display_path, '/'.join(path_segments)])

    if data_stream_name:
      data_stream_name = data_stream_name.translate(
          dfimagetools_definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)
      display_path = ':'.join([display_path, data_stream_name])

    return display_path or '/'

  def ExtractSchemas(self, path, options=None):
    """Extracts property list schemas from the path.

    Args:
      path (str): path of a property list file or storage media image containing
          property list files.
      options (Optional[dfvfs.VolumeScannerOptions]): volume scanner options. If
          None the default volume scanner options are used, which are defined in
          the dfVFS VolumeScannerOptions class.

    Yields:
      tuple[str, dict[str, str]]: known property list type identifier or the
          name of the property list file if not known and schema.
    """
    entry_lister = file_entry_lister.FileEntryLister(mediator=self._mediator)

    base_path_specs = entry_lister.GetBasePathSpecs(path, options=options)
    if not base_path_specs:
      logging.warning(
          f'Unable to determine base path specifications from: {path:s}')

    else:
      for file_entry, path_segments in entry_lister.ListFileEntries(
          base_path_specs):
        if (not file_entry.IsFile() or
            file_entry.size < self._MINIMUM_FILE_SIZE or
            file_entry.size > self._MAXIMUM_FILE_SIZE):
          continue

        file_object = file_entry.GetFileObject()

        if not self._CheckSignature(file_object):
          continue

        # Skip Cocoa nib files for now https://developer.apple.com/library/
        # archive/documentation/Cocoa/Conceptual/LoadingResources/CocoaNibs/
        # CocoaNibs.html
        if path_segments[-1].endswith('.nib'):
          continue

        display_path = self.GetDisplayPath(path_segments)
        # logging.info(f'Extracting schema from plist file: {display_path:s}')

        # Note that plistlib assumes the file-like object current offset is at
        # the start of the property list.
        file_object.seek(0, os.SEEK_SET)

        try:
          root_item = plistlib.load(file_object)
        except plistlib.InvalidFileException:
          logging.error(f'Invalid property list file: {display_path:s}')
        except xml.parsers.expat.ExpatError:
          logging.error(f'Corrupt XML property list file: {display_path:s}')

        if self._nskeyedarchiver_decoder.IsEncoded(root_item):
          try:
            root_item = self._nskeyedarchiver_decoder.Decode(root_item)
          except RuntimeError as exception:
            logging.error((
                f'Unable to decode property list file: {display_path:s} '
                f'with error: {exception!s}'))

        plist_schema = self._GetPropertyListSchemaFromItem(root_item, [''])
        if plist_schema is None:
          logging.warning(
              f'Unable to determine schema from plist file: {display_path:s}')
          continue

        # TODO: implement determine plist identifier.
        plist_identifier = path_segments[-1]

        yield plist_identifier, plist_schema

  def FormatSchema(self, schema, output_format):
    """Formats a schema into the output format.

    Args:
      schema (PropertyDefinition): schema.
      output_format (str): output format.

    Returns:
      str: formatted schema.

    Raises:
      RuntimeError: if a query could not be parsed.
    """
    if output_format == 'yaml':
      return self._FormatSchemaAsYAML(schema)

    raise RuntimeError(f'Unsupported output format: {output_format:s}')
