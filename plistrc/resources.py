# -*- coding: utf-8 -*-
"""Property List resources."""


class PropertyDefinition(object):
  """Property definition.

  Attributes:
    key_path (str): key path of the property.
    name (str): name of the property.
    schema (list[PropertyDefinition]): schema of the property.
    value_type (str): value type of the property.
  """

  def __init__(self):
    """Initializes a property definition."""
    super(PropertyDefinition, self).__init__()
    self.key_path = None
    self.name = None
    self.schema = []
    self.value_type = None
