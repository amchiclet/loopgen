# LoopGen

LoopGen is a Python library that can randomly generate C programs with loops and arrays. [Here](example.py) is an example usage.

## System requirements

Tested and works with Python 3.8

## Installation

Requires z3, lark and loguru.

```
pip3 install --user z3-solver lark-parser loguru
```

Clone the repository, make sure that the library is in PYTHONPATH, then import the needed packages and functions.

## Overview

The original goal of LoopGen was to generate programs for compiler researchers. Programs with loops and arrays tend to activate optimizations performed by compilers. Being able to generate these types of programs would make it easier for researchers to test optimizating compilers.

While it is possible to freely generate random programs, having more control over the structure of generated programs allow users to focus on specific types of programs. LoopGen gives users control over the types of generated programs through skeletons, i.e. programs that have holes to be filled.

The high-level usage is the following:
1. Write a skeleton, which is a program with holes.
2. Randomly fill those holes with statements, expressions, or operations. The library gives you ways to control how those holes are filled.
3. Once a skeleton has no holes any more, generate a C program. The library provides helper functions to determine array sizes (e.g. in case the array indices are randomized), perform program transformations, and generate C programs.

The file [example.py](example.py) shows how to perform these steps with the library.
