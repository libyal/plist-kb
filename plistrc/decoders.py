# -*- coding: utf-8 -*-
"""Property list decoders."""

import plistlib
import uuid


class NSKeyedArchiverDecoder(object):
  """Decoder for NSKeyedArchiver encoded plists.

  Also see:
    https://developer.apple.com/documentation/foundation/nskeyedarchiver
  """

  _CALLBACKS = {
      'NSArray': '_DecodeNSArray',
      'NSData': '_DecodeNSData',
      'NSDate': '_DecodeNSDate',
      'NSDictionary': '_DecodeNSDictionary',
      'NSHashTable': '_DecodeNSHashTable',
      'NSNull': '_DecodeNSNull',
      'NSObject': '_DecodeCompositeObject',
      'NSSet': '_DecodeNSArray',
      'NSString': '_DecodeNSString',
      'NSURL': '_DecodeNSURL',
      'NSUUID': '_DecodeNSUUID'}

  def _DecodeCompositeObject(
      self, plist_property, objects_array, parent_objects):
    """Decodes a composite object.

    Args:
      plist_property (object): property containing the encoded composite object.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded composite object.

    Raises:
      RuntimeError: if the composite object cannot be decoded.
    """
    composite_object = {}

    for key in plist_property:
      if key == '$class':
        continue

      value_plist_property = plist_property.get(key, None)

      value_plist_uid = self._GetPlistUID(value_plist_property)
      if value_plist_uid is None:
        composite_object[key] = self._DecodeObject(
            value_plist_property, objects_array, parent_objects)
        continue

      if value_plist_uid in parent_objects:
        continue

      parent_objects.append(value_plist_uid)

      composite_object[key] = self._DecodeObject(
          objects_array[value_plist_uid], objects_array, parent_objects)

      parent_objects.pop(-1)

    return composite_object

  def _DecodeNSArray(self, plist_property, objects_array, parent_objects):
    """Decodes a NSArray or NSSet.

    Args:
      plist_property (object): property containing the encoded NSArray or NSSet.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      list[object]: decoded NSArray or NSSet.

    Raises:
      RuntimeError: if the NSArray or NSSet cannot be decoded.
    """
    class_name = self._GetClassName(plist_property, objects_array)

    if 'NS.objects' not in plist_property:
      raise RuntimeError(f'Missing NS.objects in {class_name:s}')

    ns_objects_property = plist_property['NS.objects']

    ns_array = []

    for index, ns_object_property in enumerate(ns_objects_property):
      ns_object_plist_uid = self._GetPlistUID(ns_object_property)
      if ns_object_plist_uid is None:
        raise RuntimeError(
            f'Missing UID in NS.objects[{index:d}] property of {class_name:s}.')

      if ns_object_plist_uid in parent_objects:
        continue

      ns_object_referenced_property = objects_array[ns_object_plist_uid]

      parent_objects.append(ns_object_plist_uid)

      ns_array_element = self._DecodeObject(
          ns_object_referenced_property, objects_array, parent_objects)

      parent_objects.pop(-1)

      ns_array.append(ns_array_element)

    return ns_array

  # pylint: disable=unused-argument

  def _DecodeNSData(self, plist_property, objects_array, parent_objects):
    """Decodes a NSData.

    Args:
      plist_property (object): property containing the encoded NSData.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      bytes: decoded NSData.

    Raises:
      RuntimeError: if the NSData cannot be decoded.
    """
    class_name = self._GetClassName(plist_property, objects_array)

    if 'NS.data' not in plist_property:
      raise RuntimeError(f'Missing NS.data in {class_name:s}')

    ns_data = plist_property['NS.data']

    if not isinstance(ns_data, bytes):
      type_string = type(ns_data)
      raise RuntimeError(
          f'Unsupported type: {type_string!s} in {class_name:s}.NS.data.')

    return ns_data

  def _DecodeNSDate(self, plist_property, objects_array, parent_objects):
    """Decodes a NSDate.

    Args:
      plist_property (object): property containing the encoded NSDate.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      bytes: decoded NSDate.

    Raises:
      RuntimeError: if the NSDate cannot be decoded.
    """
    class_name = self._GetClassName(plist_property, objects_array)

    if 'NS.time' not in plist_property:
      raise RuntimeError(f'Missing NS.time in {class_name:s}')

    ns_time = plist_property['NS.time']

    if not isinstance(ns_time, float):
      type_string = type(ns_time)
      raise RuntimeError(
          f'Unsupported type: {type_string!s} in {class_name:s}.NS.time.')

    return ns_time

  # pylint: enable=unused-argument

  def _DecodeNSDictionary(self, plist_property, objects_array, parent_objects):
    """Decodes a NSDictionary.

    Args:
      plist_property (object): property containing the encoded NSDictionary.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      dict[str, object]: decoded NSDictionary.

    Raises:
      RuntimeError: if the NSDictionary cannot be decoded.
    """
    class_name = self._GetClassName(plist_property, objects_array)

    if 'NS.keys' not in plist_property or 'NS.objects' not in plist_property:
      raise RuntimeError(f'Missing NS.keys or NS.objects in {class_name:s}')

    ns_keys_property = plist_property['NS.keys']
    ns_objects_property = plist_property['NS.objects']

    if len(ns_keys_property) != len(ns_objects_property):
      raise RuntimeError((
          f'Mismatch between number of NS.keys and NS.objects in '
          f'{class_name:s}'))

    ns_dictionary = {}

    for index, ns_object_property in enumerate(ns_objects_property):
      ns_key_property = ns_keys_property[index]

      ns_key_plist_uid = self._GetPlistUID(ns_key_property)
      if ns_key_plist_uid is None:
        raise RuntimeError(
            f'Missing UID in NS.keys[{index:d}] property of {class_name:s}.')

      ns_key_referenced_property = objects_array[ns_key_plist_uid]

      parent_objects.append(ns_key_plist_uid)

      ns_key = self._DecodeObject(
          ns_key_referenced_property, objects_array, parent_objects)

      parent_objects.pop(-1)

      if not ns_key:
        raise RuntimeError((
            f'Missing {class_name:s}.NS.keys[{index:d}] with UID: '
            f'{ns_key_plist_uid:d}.'))

      if not isinstance(ns_key, str):
        type_string = type(ns_key)
        raise RuntimeError((
            f'Unsupported type: {type_string!s} in {class_name:s}.NS.keys'
            f'[{index:d}] with UID: {ns_key_plist_uid:d}.'))

      ns_object_plist_uid = self._GetPlistUID(ns_object_property)
      if ns_object_plist_uid is None:
        raise RuntimeError((
            f'Missing UID in NS.objects[{index:d}] property of {class_name:s}'
            f'.{ns_key:s}.'))

      if ns_object_plist_uid in parent_objects:
        continue

      ns_object_referenced_property = objects_array[ns_object_plist_uid]

      parent_objects.append(ns_object_plist_uid)

      ns_dictionary[ns_key] = self._DecodeObject(
          ns_object_referenced_property, objects_array, parent_objects)

      parent_objects.pop(-1)

    return ns_dictionary

  def _DecodeNSHashTable(self, plist_property, objects_array, parent_objects):
    """Decodes a NSHashTable.

    Args:
      plist_property (object): property containing the encoded NSHashTable.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded NSHashTable.

    Raises:
      RuntimeError: if the NSHashTable cannot be decoded.
    """
    class_name = self._GetClassName(plist_property, objects_array)

    if '$1' not in plist_property:
      raise RuntimeError(f'Missing $1 in {class_name:s}')

    value_property = plist_property['$1']

    value_plist_uid = self._GetPlistUID(value_property)
    if value_plist_uid is None:
      type_string = type(value_property)
      raise RuntimeError(f'Unsupported {class_name:s}.$1 type: {type_string!s}')

    if value_plist_uid in parent_objects:
      raise RuntimeError((
          f'{class_name:s}.$1 wth UID: {value_plist_uid:d} in parent objects'))

    referenced_property = objects_array[value_plist_uid]
    if not referenced_property:
      raise RuntimeError(
          f'Missing {class_name:s}.$1 with UID: {value_plist_uid:d}.')

    # TODO: what about value $0? It seems to indicate the number of elements
    # in the hash table.
    # TODO: what about value $2?

    parent_objects.append(value_plist_uid)

    ns_hash_table = self._DecodeCompositeObject(
        referenced_property, objects_array, parent_objects)

    parent_objects.pop(-1)

    return ns_hash_table

  # pylint: disable=unused-argument

  def _DecodeNSNull(self, plist_property, objects_array, parent_objects):
    """Decodes a NSNull.

    Args:
      plist_property (object): property containing the encoded NSNull.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      None: decoded NSNull.
    """
    return None

  # pylint: enable=unused-argument

  def _DecodeNSObject(self, plist_property, objects_array, parent_objects):
    """Decodes a NSObject.

    Args:
      plist_property (object): property containing the encoded NSObject.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.

    Raises:
      RuntimeError: if the NSObject cannot be decoded.
    """
    class_property = plist_property.get('$class', None)
    if not class_property:
      raise RuntimeError('$class property missing in NSObject.')

    class_plist_uid = self._GetPlistUID(class_property)
    if class_plist_uid is None:
      raise RuntimeError('Missing UID in $class property of NSObject.')

    referenced_property = objects_array[class_plist_uid]
    if not referenced_property:
      raise RuntimeError(
          f'Missing NSObject.$class with UID: {class_plist_uid:d}.')

    class_name = referenced_property.get('$classname', None)
    if not class_name:
      raise RuntimeError((
          f'$classname property missing in NSObject.$class with UID: '
          f'{class_plist_uid:d}.'))

    classes = referenced_property.get('$classes', None)
    if not classes:
      raise RuntimeError((
          f'$classes property missing in NSObject.$class with UID: '
          f'{class_plist_uid:d}.'))

    for name in classes:
      callback_method = self._CALLBACKS.get(name, None)
      if callback_method:
        break

    if not callback_method:
      raise RuntimeError(f'Missing callback for class: {class_name:s}')

    callback = getattr(self, callback_method, None)
    return callback(plist_property, objects_array, parent_objects)

  # pylint: disable=unused-argument

  def _DecodeNSString(self, plist_property, objects_array, parent_objects):
    """Decodes a NSString.

    Args:
      plist_property (object): property containing the encoded NSString.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      str: decoded NSString.

    Raises:
      RuntimeError: if the NSString cannot be decoded.
    """
    class_name = self._GetClassName(plist_property, objects_array)

    if 'NS.string' not in plist_property:
      raise RuntimeError(f'Missing NS.string in {class_name:s}')

    ns_string = plist_property['NS.string']

    if not isinstance(ns_string, str):
      type_string = type(ns_string)
      raise RuntimeError(
          f'Unsupported type: {type_string!s} in {class_name:s}.NS.string.')

    return ns_string

  def _DecodeNSURL(self, plist_property, objects_array, parent_objects):
    """Decodes a NSURL.

    Args:
      plist_property (object): property containing the encoded NSURL.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.

    Raises:
      RuntimeError: if the NSURL cannot be decoded.
    """
    if 'NS.base' not in plist_property or 'NS.relative' not in plist_property:
      raise RuntimeError('Missing NS.base or NS.relative in NSURL')

    ns_base_plist_uid = self._GetPlistUID(plist_property['NS.base'])
    if ns_base_plist_uid is None:
      raise RuntimeError('Missing UID in NS.base property of NSURL.')

    ns_base = objects_array[ns_base_plist_uid]
    if not ns_base:
      raise RuntimeError(
          f'Missing NSURL.NS.base with UID: {ns_base_plist_uid:d}.')

    if not isinstance(ns_base, str):
      type_string = type(ns_base)
      raise RuntimeError((
          f'Unsupported type: {type_string!s} in NSURL.NS.base with UID: '
          f'{ns_base_plist_uid:d}.'))

    ns_relative_plist_uid = self._GetPlistUID(plist_property['NS.relative'])
    if ns_relative_plist_uid is None:
      raise RuntimeError('Missing UID in NS.relative property of NSURL.')

    ns_relative = objects_array[ns_relative_plist_uid]
    if not ns_relative:
      raise RuntimeError(
          f'Missing NSURL.NS.relative with UID: {ns_relative_plist_uid:d}.')

    if not isinstance(ns_relative, str):
      type_string = type(ns_relative)
      raise RuntimeError((
          f'Unsupported type: {type_string!s} in NSURL.NS.relative with UID: '
          f'{ns_relative_plist_uid:d}.'))

    if ns_base == '$null':
      ns_url = ns_relative
    else:
      ns_url = '/'.join([ns_base, ns_relative])

    return ns_url

  def _DecodeNSUUID(self, plist_property, objects_array, parent_objects):
    """Decodes a NSUUID.

    Args:
      plist_property (object): property containing the encoded NSUUID.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.

    Raises:
      RuntimeError: if the NSUUID cannot be decoded.
    """
    if 'NS.uuidbytes' not in plist_property:
      raise RuntimeError('Missing NS.uuidbytes')

    ns_uuidbytes = plist_property['NS.uuidbytes']
    if len(ns_uuidbytes) != 16:
      raise RuntimeError('Unsupported NS.uuidbytes size')

    return str(uuid.UUID(bytes=ns_uuidbytes))

  # pylint: enable=unused-argument

  def _DecodeObject(self, plist_property, objects_array, parent_objects):
    """Decodes an object.

    Args:
      plist_property (object): property containing the encoded NSUUID.
      objects_array (list[object]): $objects array.
      parent_objects (list[int]): parent object UIDs.

    Returns:
      object: decoded object.

    Raises:
      RuntimeError: if the object cannot be decoded.
    """
    if isinstance(plist_property, dict) and '$class' in plist_property:
      return self._DecodeNSObject(plist_property, objects_array, parent_objects)

    if isinstance(plist_property, str) and plist_property == '$null':
      return None

    return plist_property

  def _GetClassName(self, plist_property, objects_array):
    """Retrieves a class name.

    Args:
      plist_property (object): property containing the $class property.
      objects_array (list[object]): $objects array.

    Returns:
      str: class name or None if not available.

    Raises:
      RuntimeError: if the class name cannot be retrieved.
    """
    class_property = plist_property.get('$class', None)
    if not class_property:
      raise RuntimeError('Missing $class property.')

    class_plist_uid = self._GetPlistUID(class_property)
    if class_plist_uid is None:
      raise RuntimeError('Missing UID in $class property.')

    referenced_property = objects_array[class_plist_uid]
    if not referenced_property:
      raise RuntimeError(f'Missing class with UID: {class_plist_uid:d}.')

    class_name = referenced_property.get('$classname', None)
    if not class_name:
      raise RuntimeError((
          f'$classname property missing in class with UID: '
          f'{class_plist_uid:d}.'))

    return class_name

  def _GetPlistUID(self, plist_property):
    """Retrieves a plist UID.

    Args:
      plist_property (object): property containing the plist UID.

    Returns:
      int: plist UID or None if not available.
    """
    if isinstance(plist_property, plistlib.UID):
      return plist_property.data

    if (isinstance(plist_property, dict) and 'CF$UID' in plist_property and
        len(plist_property) == 1):
      return plist_property['CF$UID']

    return None

  def Decode(self, root_item):
    """Decodes a NSKeyedArchiver encoded plist.

    Args:
      root_item (object): root object of the NSKeyedArchiver encoded plist.

    Returns:
      dict[str, object]: root object of the decoded plist.

    Raises:
      RuntimeError: if the plist cannot be decoded.
    """
    if not isinstance(root_item, dict):
      type_string = type(root_item)
      raise RuntimeError(
          f'Unsupported plist: unsupported root item type: {type_string!s}.')

    archiver = root_item.get('$archiver')
    version = root_item.get('$version')
    if archiver != 'NSKeyedArchiver' or version != 100000:
      raise RuntimeError(f'Unsupported plist: {archiver!s} {version!s}')

    decoded_object = {}

    objects_array = root_item.get('$objects') or []

    top_property = root_item.get('$top') or {}
    for name, value_property in top_property.items():
      value_plist_uid = self._GetPlistUID(value_property)
      if value_plist_uid is None:
        decoded_object[name] = value_property
        continue

      value_referenced_property = objects_array[value_plist_uid]
      if not value_referenced_property:
        raise RuntimeError(
            f'Missing $top["{name:s}"] with UID: {value_plist_uid:d}.')

      decoded_object[name] = self._DecodeNSObject(
          value_referenced_property, objects_array, [value_plist_uid])

    return decoded_object

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
