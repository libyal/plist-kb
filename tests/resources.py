#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Property List resources."""

import unittest

from plistrc import resources

from tests import test_lib


class PropertyDefinitionTest(test_lib.BaseTestCase):
  """Tests for the property definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    property_definition = resources.PropertyDefinition()
    self.assertIsNotNone(property_definition)


if __name__ == '__main__':
  unittest.main()
