# -*- coding: utf-8 -*-
"""Property List file schema extractor."""

import logging
import os
import plistlib
import xml

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfimagetools import definitions as dfimagetools_definitions
from dfimagetools import file_entry_lister


class PropertyListSchemaExtractor(object):
  """Property List file schema extractor."""

  _MAXIMUM_FILE_SIZE = 64 * 1024 * 1024

  _MINIMUM_FILE_SIZE = 8

  _UTF8_BYTE_ORDER_MARK = b'\xef\xbb\xbf'
  _UTF16BE_BYTE_ORDER_MARK = b'\xfe\xff'
  _UTF16LE_BYTE_ORDER_MARK = b'\xff\xfe'
  _UTF32BE_BYTE_ORDER_MARK = b'\x00\x00\xfe\xff'
  _UTF32LE_BYTE_ORDER_MARK = b'\xff\xfe\x00\x00'

  def __init__(self, artifact_definitions, mediator=None):
    """Initializes a Property List file schema extractor.

    Args:
      artifact_definitions (str): path to a single artifact definitions
          YAML file or a directory of definitions YAML files.
      mediator (Optional[dfvfs.VolumeScannerMediator]): a volume scanner
          mediator.
    """
    super(PropertyListSchemaExtractor, self).__init__()
    self._artifacts_registry = artifacts_registry.ArtifactDefinitionsRegistry()
    self._mediator = mediator

    if artifact_definitions:
      reader = artifacts_reader.YamlArtifactsReader()
      if os.path.isdir(artifact_definitions):
        self._artifacts_registry.ReadFromDirectory(reader, artifact_definitions)
      elif os.path.isfile(artifact_definitions):
        self._artifacts_registry.ReadFromFile(reader, artifact_definitions)

  def _CheckByteOrderMark(self, data):
    """Determines if a Property List starts with a byte-order-mark.

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
      file_object (dfvfs.FileIO): file-like object of the Property List.

    Returns:
      bool: True if the signature matches that of a Property List, False
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

  def _GetPropertyListSchemaFromFileObject(self, file_object):
    """Retrieves schema from given Property List file-like object.

    Args:
      file_object (dfvfs.FileIO): file-like object of the Property List.

    Returns:
      dict[str, str]: schema or None if the schema could not be retrieved.
    """
    # Note that plistlib assumes the file-like object current offset is at the
    # start of the Property List.
    file_object.seek(0, os.SEEK_SET)

    return plistlib.load(file_object)

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
    """Extracts Property List schemas from the path.

    Args:
      path (str): path of a Property List file or storage media image containing
          Property List files.
      options (Optional[dfvfs.VolumeScannerOptions]): volume scanner options. If
          None the default volume scanner options are used, which are defined in
          the dfVFS VolumeScannerOptions class.

    Yields:
      tuple[str, dict[str, str]]: known Property List type identifier or the
          name of the Property List file if not known and schema.
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

        display_path = self.GetDisplayPath(path_segments)
        # logging.info(f'Extracting schema from plist file: {display_path:s}')

        try:
          plist_schema = self._GetPropertyListSchemaFromFileObject(file_object)
        except plistlib.InvalidFileException:
          logging.error(f'Invalid property list file: {display_path:s}')
        except xml.parsers.expat.ExpatError:
          logging.error(f'Corrupt XML property list file: {display_path:s}')

        if plist_schema is None:
          logging.warning(
              f'Unable to determine schema from plist file: {display_path:s}')
          continue

        # TODO: implement

        yield None, None

  # pylint: disable=redundant-returns-doc

  def FormatSchema(self, schema, output_format):
    """Formats a schema into a word-wrapped string.

    Args:
      schema (dict[str, str]): schema.
      output_format (str): output format.

    Returns:
      str: formatted schema.

    Raises:
      RuntimeError: if a query could not be parsed.
    """
    raise RuntimeError(f'Unsupported output format: {output_format:s}')
