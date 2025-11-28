#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to decodes a NSKeyedArchiver encoded plist."""

import argparse
import base64
import json
import plistlib
import sys

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plistrc import decoders


class NSKeyedArchiverJSONEncoder(json.JSONEncoder):
  """JSON encoder for decoded NSKeyedArchiver encoded plists."""

  def default(self, o):
    """Encodes an object as JSON.

    Args:
      o (object): object to encode.

    Returns:
      object: JSON encoded object.
    """
    if isinstance(o, bytes):
      encoded_bytes = base64.urlsafe_b64encode(o)
      return encoded_bytes.decode('latin1')

    if isinstance(o, dfdatetime_cocoa_time.CocoaTime):
      return o.timestamp

    return super(NSKeyedArchiverJSONEncoder, self).default(o)


def Main():
  """Entry point of console script to decode NSKeyedArchiver encoded plists.

  Returns:
    int: exit code that is provided to sys.exit().
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
    return 1

  decoder = decoders.NSKeyedArchiverDecoder()

  with open(options.source, 'rb') as file_object:
    encoded_plist = plistlib.load(file_object)

  try:
    decoded_plist = decoder.Decode(encoded_plist)
  except RuntimeError as exception:
    print(f'[WARNING] {exception!s}')
    return 1

  json_string = json.dumps(decoded_plist, cls=NSKeyedArchiverJSONEncoder)
  print(json_string)

  return 0


if __name__ == '__main__':
  sys.exit(Main())
