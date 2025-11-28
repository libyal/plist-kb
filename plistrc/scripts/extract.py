#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to extract the schema of Property List files."""

import argparse
import logging
import os
import sys

import artifacts

from dfvfs.lib import errors as dfvfs_errors

from dfimagetools.helpers import command_line

from plistrc import schema_extractor


def Main():
  """Entry point of console script to extract Property List schemas.

  Returns:
    int: exit code that is provided to sys.exit().
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extracts the schema of Property List files.'))

  # TODO: add data group.
  argument_parser.add_argument(
      '--artifact_definitions', '--artifact-definitions',
      dest='artifact_definitions', type=str, metavar='PATH', action='store',
      help=('Path to a directory or file containing the artifact definition '
            '.yaml files.'))

  # TODO: add output group.
  argument_parser.add_argument(
      '--format', dest='format', action='store', type=str,
      choices=['text', 'yaml'], default='yaml', metavar='FORMAT',
      help='Output format.')

  argument_parser.add_argument(
      '--output', dest='output', action='store', metavar='./plist-kb/',
      default=None, help='Directory to write the output to.')

  # TODO: add source group.
  command_line.AddStorageMediaImageCLIArguments(argument_parser)

  argument_parser.add_argument(
      'source', nargs='?', action='store', metavar='image.raw', default=None,
      help='path of a storage media image or Property List file.')

  options = argument_parser.parse_args()

  if not options.source:
    print('Source value is missing.')
    print('')
    argument_parser.print_help()
    print('')
    return 1

  artifact_definitions = options.artifact_definitions
  if not artifact_definitions:
    artifact_definitions = os.path.join(
        os.path.dirname(artifacts.__file__), 'data')
    if not os.path.exists(artifact_definitions):
      artifact_definitions = os.path.join('/', 'usr', 'share', 'artifacts')
    if not os.path.exists(artifact_definitions):
      artifact_definitions = None

  if not artifact_definitions:
    print('Path to artifact definitions is missing.')
    print('')
    argument_parser.print_help()
    print('')
    return 1

  if options.output:
    if not os.path.exists(options.output):
      os.mkdir(options.output)

    if not os.path.isdir(options.output):
      print(f'{options.output:s} must be a directory')
      print('')
      return 1

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  mediator, volume_scanner_options = (
      command_line.ParseStorageMediaImageCLIArguments(options))

  extractor = schema_extractor.PropertyListSchemaExtractor(
      artifact_definitions, mediator=mediator)

  try:
    for property_list_identifier, plist_schema in extractor.ExtractSchemas(
        options.source, options=volume_scanner_options):
      if not plist_schema:
        continue

      output_text = extractor.FormatSchema(plist_schema, options.format)
      if not options.output:
        print(output_text)
      else:
        file_exists = False
        output_file = None
        for number in range(1, 99):
          filename = (
              f'{property_list_identifier:s}.{number:d}.{options.format:s}')
          output_file = os.path.join(options.output, filename)
          if not os.path.exists(output_file):
            break

          with open(output_file, 'r', encoding='utf-8') as existing_file_object:
            existing_output_text = existing_file_object.read()
            if output_text == existing_output_text:
              file_exists = True
              break

        if not file_exists:
          with open(output_file, 'w', encoding='utf-8') as output_file_object:
            output_file_object.write(output_text)

  except dfvfs_errors.ScannerError as exception:
    print(f'[ERROR] {exception!s}', file=sys.stderr)
    print('')
    return 1

  except KeyboardInterrupt:
    print('Aborted by user.', file=sys.stderr)
    print('')
    return 1

  return 0


if __name__ == '__main__':
  sys.exit(Main())
