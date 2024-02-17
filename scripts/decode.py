#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to decodes a NSKeyedArchiver encoded plist."""

import argparse
import json
import plistlib
import sys

from plistrc import decoders


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Decodes NSKeyedArchiver encoded plist files.'))

  argument_parser.add_argument(
      'source', nargs='?', action='store', metavar='PATH', default=None,
      help='path of the NSKeyedArchiver encoded plist file.')

  options = argument_parser.parse_args()

  if not options.source:
    print('Source file missing.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  decoder = decoders.NSKeyedArchiverDecoder()

  with open(options.source, 'rb') as file_object:
    encoded_plist = plistlib.load(file_object)

  try:
    decoded_plist = decoder.Decode(encoded_plist)
  except RuntimeError as exception:
    print(f'[WARNING] {exception!s}')
    return False

  print(json.dumps(decoded_plist))

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
