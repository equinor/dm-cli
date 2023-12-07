"""dir_hash: Return SHA1 hash of a directory.
"""
import hashlib
import os


def update_hash(running_hash, filepath, encoding=''):
    """Update running SHA1 hash, factoring in hash of given file.

    Side Effects:
        running_hash.update()
    """
    if encoding:
        file = open(filepath, 'r', encoding=encoding)
        for line in file:
            hashed_line = hashlib.sha1(line.encode(encoding))
            hex_digest = hashed_line.hexdigest().encode(encoding)
            running_hash.update(hex_digest)
        file.close()
    else:
        file = open(filepath, 'rb')
        while True:
            # Read file in as little chunks.
            buffer = file.read(4096)
            if not buffer:
                break
            running_hash.update(hashlib.sha1(buffer).hexdigest())
        file.close()


def dir_hash(directory, verbose=False):
    """Return SHA1 hash of a directory.

    Args:
        directory (string): Path to a directory.
        verbose (bool): If True, prints progress updates.

    Raises:
        FileNotFoundError: If directory provided does not exist.

    Returns:
        string: SHA1 hash hexdigest of a directory.
    """
    sha_hash = hashlib.sha1()

    if not os.path.exists(directory):
        raise FileNotFoundError

    for root, dirs, files in os.walk(directory):
        for names in files:
            if verbose:
                print('Hashing', names)
            filepath = os.path.join(root, names)
            try:
                update_hash(running_hash=sha_hash,
                            filepath=filepath)
            except TypeError:
                update_hash(running_hash=sha_hash,
                            filepath=filepath)

    return sha_hash.hexdigest()