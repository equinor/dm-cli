import re


def search_in_list(
    document: list, pattern: str, target_attr: str, path: str, parent_was_dict: bool, targets: dict, references: dict
):
    attribute_types = map(lambda attr: (attr, type(attr)), document)
    for i, at in enumerate(attribute_types):
        a = at[0]
        t = at[1]
        if is_primitive(t):
            result = search_in_primitive(a, pattern)
            if result:
                references[f"{path}[{i}]"] = result
        else:
            action = type_to_action[t]
            action(a, pattern, target_attr, f"{path}[{i}]", False, targets, references)


def search_in_primitive(val, pattern: str):
    match = re.match(pattern, str(val))
    if match:
        return match.group(1)


def is_primitive(t: type):
    return t == str or t == int or t == float or t == bool


def is_list(t: type):
    return t == list


def is_dict(t: type):
    return t == dict


def search_in_dict(
    document: dict, pattern: str, target_attr: str, path: str, parent_was_dict: bool, targets: dict, references: dict
):
    """Search for internal references in 'document', referencing to a target attribute.

    Uses the methods 'search_in_list' and 'search_in_primitive' to continue searching in attributes of these types

    Args:
        document: the input document which contains internal references
        pattern: (what does a 'reference' look like?) regex which tries to match the reference structure, defaults to
            ^.$<some_id>. Is used to populate the lookup_of_references table
        target_attr: (where is the reference pointing to?) the attribute which contains the id which is being referred
            to is used to populate the lookup_of_targets table
        path: the absolute path at each level in the search
        parent_was_dict: flag to track the type of the parent
        targets: dict to track discovered attributes that define local ids
        references: dict to track discovered references to local ids

    Returns:
        Two lookup tables: 'references' dict, which mapping from the location of the reference (path), to the
        local id, and 'targets' dict, which is a mapping from the local id to the location of the element which owns
        that id (absolute local path)
    """

    attribute_types = map(lambda attr: (attr, type(document[attr])), list(document.keys()))
    for a, t in attribute_types:
        val = document[a]
        if is_primitive(t):
            if a == target_attr:
                parent_path = path.rsplit("[", 1)[0]
                final_path = path if parent_was_dict else f"{parent_path}({target_attr}={val})"
                targets[val] = final_path
            result = search_in_primitive(val, pattern)
            if result:
                references[f"{path}.{a}"] = result
        else:
            action = type_to_action[t]
            action(document[a], pattern, target_attr, f"{path}.{a}", True, targets, references)
    return targets, references


def _dig_and_replace(document, path_iterator: iter, replace: str):
    attr = next(path_iterator, None)
    if not attr:
        return True
    attr = int(attr) if is_list(type(document)) else attr
    last_attribute = _dig_and_replace(document[attr], path_iterator, replace)
    if last_attribute:
        document[attr] = replace


def dig_and_replace(targets: dict, references: dict, document):
    """Transform references in 'references' to the absolute (local) path found in 'targets'

    Traverses the document based on the path found in 'references' lookup table, and updates the entry with the
    corresponding value found in the 'targets' lookup table (the local path to the target attribute)

    Args:
        references: mapping from the location of the reference (path), to the local id
        targets: mapping from the local id to the location of the element which owns that id
        document: dictionary document which contains references we want to transform/replace

    Returns:
        The final document with all the local id references resolved into local path references

    """
    for path, ref in references.items():
        path_items = re.split("[\.\[\]]+", path)[1:]  # splits path on the '.', '[' and ']' characters
        path_iterator = iter(path_items)
        _dig_and_replace(document, path_iterator, targets[ref])
    return document


def resolve_local_ids_in_document(
    document: dict,
    pattern: str = r"\^\.\$(\w+)",
    target_attr: str = "_id",
    path: str = "^",
    parent_was_dict: bool = True,
):
    """Transform local_id references in 'document' to absolute (local) paths

    e.g.: customers[0].car.address points to cars[0][0]

    (local id reference)         (absolute path reference)
    "address": ^.$12345    ->    "address": ^.cars[0](_id=12345)

    Args:
        document: the input document which contains internal references
        pattern: (what does a 'reference' look like?) regex which tries to match the reference structure, defaults to
            ^.$<some_id>. Is used to populate the lookup_of_references table
        target_attr: (where is the reference pointing to?) the attribute which contains the id which is being referred
            to is used to populate the lookup_of_targets table
        path: the absolute path at each level in the search
        parent_was_dict: flag to track the type of the parent

    Returns:
        The final document with all the local id references resolved into local path references
    """

    targets, references = search_in_dict(document, pattern, target_attr, path, parent_was_dict, {}, {})
    return dig_and_replace(targets, references, document)


type_to_action = {list: search_in_list, dict: search_in_dict}
