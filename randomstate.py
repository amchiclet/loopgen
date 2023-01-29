import random
import pickle

# Stores the random state to the path pointed to by pathlib.Path
# If state is not given, use the current random state.
def checkpoint(path, state=None):
    if state is None:
        state = random.getstate()
    with path.open('wb') as f:
        pickle.dump(state, f)

# Loads the random state to the path pointed to by pathlib.Path
def restore(path):
    with path.open('rb') as f:
        random.setstate(pickle.load(f))
