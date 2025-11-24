#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the property list resources."""

import unittest

from plistrc import resources

from tests import test_lib


class PropertyDefinitionTest(test_lib.BaseTestCase):
  """Tests for the property definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    test_definition = resources.PropertyDefinition()
    self.assertIsNotNone(test_definition)


class PropertyListDefinitionTest(test_lib.BaseTestCase):
  """Tests for the property list definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    test_definition = resources.PropertyListDefinition()
    self.assertIsNotNone(test_definition)


if __name__ == '__main__':
  unittest.main()
