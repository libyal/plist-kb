# -*- coding: utf-8 -*-
"""Property List decoders."""

import base64
import plistlib
import uuid


class NSKeyedArchiverDecoder(object):
  """Decodes a NSKeyedArchiver encoded plist.

  Also see:
    https://developer.apple.com/documentation/foundation/nskeyedarchiver
  """

  # TODO: add support for NSAttributedString
  # TODO: add support for NSData
  # TODO: add support for NSDate
  # TODO: add support for NSMutableAttributedString
  # TODO: add support for NSMutableData
  # TODO: add support for NSMutableString
  # TODO: add support for NSValue
  # TODO: add support for SFLListItem

  _CALLBACKS = {
      'BackgroundItemContainer': '_DecodeComposite',
      'BackgroundItems': '_DecodeComposite',
      'BackgroundLoginItem': '_DecodeComposite',
      'Bookmark': '_DecodeComposite',
      'BTMUserSettings': '_DecodeComposite',
      'ItemRecord': '_DecodeComposite',
      'NSArray': '_DecodeNSArray',
      'NSBox': '_DecodeNSBox',
      'NSButton': '_DecodeNSControl',
      'NSButtonCell': '_DecodeComposite',
      'NSButtonImageSource': '_DecodeComposite',
      'NSColor': '_DecodeComposite',
      'NSCustomObject': '_DecodeComposite',
      'NSCustomResource': '_DecodeComposite',
      'NSDictionary': '_DecodeNSDictionary',
      'NSFont': '_DecodeComposite',
      'NSHashTable': '_DecodeNSHashTable',
      'NSIBObjectData': '_DecodeComposite',
      'NSImageCell': '_DecodeComposite',
      'NSImageView': '_DecodeNSControl',
      'NSMenu': '_DecodeComposite',
      'NSMutableArray': '_DecodeNSArray',
      'NSMutableDictionary': '_DecodeNSDictionary',
      'NSMutableSet': '_DecodeNSSet',
      'NSNibOutletConnector': '_DecodeNSNibOutletConnector',
      'NSPopUpButton': '_DecodeNSControl',
      'NSPopUpButtonCell': '_DecodeComposite',
      'NSSet': '_DecodeNSSet',
      'NSTextField': '_DecodeNSControl',
      'NSTextFieldCell': '_DecodeComposite',
      'NSURL': '_DecodeNSURL',
      'NSUUID': '_DecodeNSUUID',
      'NSView': '_DecodeNSView',
      'NSWindowTemplate': '_DecodeComposite',
      'Storage': '_DecodeComposite'}

  def _DecodeComposite(self, encoded_object, objects_array, parent_objects):
    """Decodes a composite object.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class'])

  def _DecodeCompositeWithDebug(
      self, encoded_object, objects_array, parent_objects):
    """Decodes a composite object with debugging.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class'], enable_debug=True)

  def _DecodeCompositeWithFilter(
      self, encoded_object, objects_array, parent_objects, keys_to_ignore=None,
      enable_debug=False):
    """Decodes a composite object.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.
      keys_to_ignore (Optional[list[str]]): keys to ignore.

    Returns:
      object: decoded object.
    """
    decoded_dict = {}

    for key in encoded_object:
      if keys_to_ignore and key in keys_to_ignore:
        continue

      encoded_value = encoded_object.get(key, None)
      if not encoded_value:
        continue

      sub_parent_objects = list(parent_objects)

      plist_uid = self._GetPlistUID(encoded_value)
      if plist_uid is not None:
        if plist_uid in parent_objects:
          class_name = self._GetClassname(
              encoded_object, objects_array, parent_objects)
          message = f'{class_name:s}.{key:s} {plist_uid:d} in parent objects'
          if not enable_debug:
            raise RuntimeError(message)

          print(message)
          continue

        sub_parent_objects.append(plist_uid)

        encoded_value = objects_array[plist_uid]

      decoded_value = self._DecodeObject(
          encoded_value, objects_array, sub_parent_objects)

      decoded_dict[key] = decoded_value

    return decoded_dict

  def _DecodeContainer(self, encoded_object, objects_array, parent_objects):
    """Decodes a container object.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class', 'container'])

  def _DecodeNSArray(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSArray.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    if 'NS.objects' not in encoded_object:
      raise RuntimeError('Missing NS.objects')

    return [self._DecodeObject(element, objects_array, parent_objects)
            for element in encoded_object['NS.objects']]

  def _DecodeNSBox(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSBox.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class', 'NSContentView', 'NSNextResponder', 'NSSubviews',
            'NSSuperview'])

  def _DecodeNSControl(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSControl.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class', 'NSCell', 'NSNextResponder', 'NSSuperview'])

  def _DecodeNSDictionary(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSDictionary.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    if 'NS.keys' not in encoded_object or 'NS.objects' not in encoded_object:
      raise RuntimeError('Missing NS.keys or NS.objects')

    ns_keys = encoded_object['NS.keys']
    ns_objects = encoded_object['NS.objects']

    if len(ns_keys) != len(ns_objects):
      raise RuntimeError('Mismatch between number of NS.keys and NS.objects')

    decoded_dict = {}

    for index, encoded_key in enumerate(ns_keys):
      decoded_key = self._DecodeObject(
          encoded_key, objects_array, parent_objects)

      encoded_value = ns_objects[index]
      decoded_value = self._DecodeObject(
          encoded_value, objects_array, parent_objects)

      decoded_dict[decoded_key] = decoded_value

    return decoded_dict

  def _DecodeNSHashTable(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSHashTable.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    if '$1' not in encoded_object:
      raise RuntimeError('Missing $1')

    value_object = encoded_object['$1']

    plist_uid = self._GetPlistUID(value_object)
    if plist_uid is None:
      encoded_object_type = type(value_object)
      raise RuntimeError(
          f'Unsupported encoded object $1 type: {encoded_object_type!s}')

    if plist_uid in parent_objects:
      raise RuntimeError(f'$object {plist_uid:d} in parent objects')

    parent_objects = list(parent_objects)
    parent_objects.append(plist_uid)

    referenced_object = objects_array[plist_uid]

    # TODO: what about value $0? It seems to indicate the number of elements
    # in the hash table.
    # TODO: what about value $2?

    return self._DecodeContainer(
        referenced_object, objects_array, parent_objects)

  def _DecodeNSNibOutletConnector(
      self, encoded_object, objects_array, parent_objects):
    """Decodes a NSNibOutletConnector.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class', 'NSSource'])

  def _DecodeNSSet(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSSet.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    if 'NS.objects' not in encoded_object:
      raise RuntimeError('Missing NS.objects')

    decoded_list = []

    for index, value_object in enumerate(encoded_object['NS.objects']):
      plist_uid = self._GetPlistUID(value_object)
      if plist_uid in parent_objects:
        raise RuntimeError(
            f'NS.objects[{index:d}] {plist_uid:d} in parent objects')

      sub_parent_objects = list(parent_objects)
      sub_parent_objects.append(plist_uid)

      referenced_object = objects_array[plist_uid]

      decoded_element = self._DecodeObject(
          referenced_object, objects_array, sub_parent_objects)

      decoded_list.append(decoded_element)

    return decoded_list

  def _DecodeNSURL(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSURL.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    if 'NS.base' not in encoded_object or 'NS.relative' not in encoded_object:
      raise RuntimeError('Missing NS.base or NS.relative')

    decoded_base = self._DecodeObject(
        encoded_object['NS.base'], objects_array, parent_objects)

    decoded_relative = self._DecodeObject(
        encoded_object['NS.relative'], objects_array, parent_objects)

    if decoded_base:
      decoded_url = '/'.join([decoded_base, decoded_relative])
    else:
      decoded_url = decoded_relative

    return decoded_url

  # pylint: disable=unused-argument

  def _DecodeNSUUID(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSUUID.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    if 'NS.uuidbytes' not in encoded_object:
      raise RuntimeError('Missing NS.uuidbytes')

    ns_uuidbytes = encoded_object['NS.uuidbytes']
    if len(ns_uuidbytes) != 16:
      raise RuntimeError('Unsupported NS.uuidbytes size')

    return str(uuid.UUID(bytes=ns_uuidbytes))

  # pylint: enable=unused-argument

  def _DecodeNSView(self, encoded_object, objects_array, parent_objects):
    """Decodes a NSView.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    return self._DecodeCompositeWithFilter(
        encoded_object, objects_array, parent_objects, keys_to_ignore=[
            '$class', 'NSNextResponder', 'NSSubviews', 'NSSuperview'])

  def _DecodeObject(self, encoded_object, objects_array, parent_objects):
    """Decodes an object.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.
    """
    # Due to how plist UID are stored in a XML plist we need to test for it
    # before testing for a dict.

    plist_uid = self._GetPlistUID(encoded_object)
    if plist_uid is not None:
      referenced_object = objects_array[plist_uid]
      return self._DecodeObject(
          referenced_object, objects_array, parent_objects)

    if (encoded_object is None or
        isinstance(encoded_object, (bool, int, float))):
      return encoded_object

    if isinstance(encoded_object, bytes):
      return str(base64.urlsafe_b64encode(encoded_object))[2:-1]

    if isinstance(encoded_object, str):
      if encoded_object == '$null':
        return None

      return encoded_object

    if isinstance(encoded_object, dict):
      class_name = self._GetClassname(
          encoded_object, objects_array, parent_objects)
      if not class_name:
        return encoded_object

      callback_method = self._CALLBACKS.get(class_name, None)
      if not callback_method:
        raise RuntimeError(f'Missing callback for class: {class_name:s}')

      callback = getattr(self, callback_method, None)
      return callback(encoded_object, objects_array, parent_objects)

    if isinstance(encoded_object, list):
      return [self._DecodeObject(element, objects_array, parent_objects)
              for element in encoded_object]

    encoded_object_type = type(encoded_object)
    raise RuntimeError(
        f'Unsupported encoded object type: {encoded_object_type!s}')

  def _GetClassname(self, encoded_object, objects_array, parent_objects):
    """Retrieves a class name.

    Args:
      encoded_object (object): encoded object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      str: class name or None if not available.
    """
    encoded_class = encoded_object.get('$class', None)
    if not encoded_class:
      return None

    decoded_class = self._DecodeObject(
        encoded_class, objects_array, parent_objects)
    return decoded_class.get('$classname', None)

  def _GetPlistUID(self, encoded_object):
    """Retrieves a plist UID.

    Args:
      encoded_object (object): encoded object.

    Returns:
      int: plist UID or None if not available.
    """
    if isinstance(encoded_object, plistlib.UID):
      return encoded_object.data

    if (isinstance(encoded_object, dict) and 'CF$UID' in encoded_object and
        len(encoded_object) == 1):
      return encoded_object['CF$UID']

    return None

  def Decode(self, root_item):
    """Decodes a NSKeyedArchiver encoded plist.

    Args:
      root_item (object): root object of the NSKeyedArchiver encoded plist.

    Returns:
      dict[str, object]: root object of the decoded plist.

    Raises:
      RuntimeError: if encoding is not supported.
    """
    archiver = root_item.get('$archiver')
    version = root_item.get('$version')
    if archiver != 'NSKeyedArchiver' or version != 100000:
      raise RuntimeError(f'Unsupported plist: {archiver!s} {version!s}')

    decoded_plist = {}

    objects_array = root_item.get('$objects') or []

    top_items = root_item.get('$top') or {}
    for name, value in top_items.items():
      plist_uid = self._GetPlistUID(value)
      if plist_uid is not None:
        encoded_object = objects_array[plist_uid]

        value = self._DecodeObject(encoded_object, objects_array, [plist_uid])

      decoded_plist[name] = value

    return decoded_plist

  def IsEncoded(self, root_item):
    """Determines if a plist is NSKeyedArchiver encoded.

    Args:
      root_item (object): root object of the NSKeyedArchiver encoded plist.

    Returns:
      bool: True if NSKeyedArchiver encoded, False otherwise.
    """
    if not isinstance(root_item, dict):
      return False

    archiver = root_item.get('$archiver')
    version = root_item.get('$version')

    return archiver == 'NSKeyedArchiver' and version == 100000
