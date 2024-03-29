from hashlib import md5
from pathlib import Path

# TODO: Use pathlib Path as arguments

# reads checksum (hex string) saved in path as int
def read_checksum(path):
    with open(path) as f:
        return int(f.read().strip(), 16)

def calculate_checksum_hex(path):
    with open(path) as f:
        contents = f.read().strip()
        return md5(contents.encode()).hexdigest()

# Writes checksum of input_path to output_path.
# Leading and trailing spaces are ignored.
# Overwrites output_path if it already exists.
# Returns the hexdigest of the checksum.
def write_checksum(input_path, output_path):
    with open(output_path, 'w') as f:
        checksum = calculate_checksum_hex(input_path)
        f.write(checksum)
        return int(checksum, 16)

# Calls f for each input that matches root_path/input_pattern.
def iterate_inputs(root_path, input_pattern, f):
    path = Path(root_path)
    for core_c in path.glob(input_pattern):
        f(core_c)

# Gets checksum of input_path. Writes if checksum file doesn't exist.
def get_checksum(input_path):
    checksum_path = input_path.parent / 'checksum'
    if checksum_path.exists():
        expected = int(calculate_checksum_hex(input_path), 16)
        got = read_checksum(checksum_path)
        if expected != got:
            raise RuntimeError(f'checksum mismatch {input_path}')
        return got
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
