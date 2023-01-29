from hashlib import md5
from pathlib import Path

# reads checksum (hex string) saved in path as int
def read_checksum(path):
    with open(path) as f:
        return int(f.read().strip(), 16)

# Writes checksum of input_path to output_path.
# Leading and trailing spaces are ignored.
# Overwrites output_path if it already exists.
# Returns the hexdigest of the checksum.
def write_checksum(input_path, output_path):
    with open(input_path) as f, open(output_path, 'w') as g:
        contents = f.read().strip()
        checksum = md5(contents.encode()).hexdigest()
        g.write(checksum)
        return int(checksum, 16)

# Calls f for each input that matches root_path/input_pattern.
def iterate_inputs(root_path, input_pattern, f):
    path = Path(root_path)
    assert(path.exists())
    for core_c in path.glob(input_pattern):
        f(core_c)

# Gets checksum of input_path. Writes if checksum file doesn't exist.
def get_checksum(input_path):
    checksum_path = input_path.parent / 'checksum'
    if checksum_path.exists():
        return read_checksum(checksum_path)
    else:
        return write_checksum(input_path, checksum_path)
    
# Populates path->checksum dict.
# Populates checksum->[path] dict
def gather_checksums(root_path, input_pattern):
    checksums = {}
    def gather_checksum(input_path):
        nonlocal checksums
        checksum = get_checksum(input_path)
        if checksum not in checksums:
            checksums[checksum] = []
        checksums[checksum].append(input_path)

    iterate_inputs(root_path, input_pattern, gather_checksum)
    return checksums

# example
# print(gather_checksums('./generated/code/dir', '*/*/*/core.c'))
