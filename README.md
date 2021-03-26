# LoopGen

A tool that generates loops.

## System requirements

Tested and works with Python 3.8

## Installation

Requires z3, lark and loguru.

```
pip3 install --user z3-solver lark-parser loguru
```

## Overview

The original goal of LoopGen was to generate programs for compiler researchers. Programs with loops and arrays tend to activate optimizations performed by compilers. Being able to generate these types of programs would make it easier for researchers to test optimizating compilers.

While it is possible to freely generate random programs, having more control over the structure of generated programs allow users to focus on specific types of programs. LoopGen gives users control over the types of generated programs through skeletons, i.e. programs that have holes to be filled.

LoopGen is a Python library that makes it easier to randomly generate programs with loops and arrays while still being able to control the overall generated structure of the program.

The high-level usage is to create a [skeleton](#skeletons), fill in the holes in the skeleton, create a [pattern](#patterns) from the full skeleton, create an [instance](#instances) from the pattern, and finally generate code from the instance.

## Concepts

### Skeletons

A skeleton is a program with holes. Here's an example skeleton.

```
declare A[];
declare B[];

for [i] {
  $_$
  A[i] = A[i] * #_#;
  A[i] = A[i] @_@ B[i];
  A[i] = `_`[i] * B[i];
}
```

`$_$` denotes a hole to be filled with a statement.

`#_#` denotes a hole to be filled with an expression.

`@_@` denotes a hole to be filled with an operator.

`` `_` `` denotes a hole to be filled with a variable name.

When these holes are filled, a skeleton becomes a pattern.

### Patterns

A pattern is a program with constant variables. Here's an example pattern resulting from filling the holes of the above skeleton.

```
declare A[];
declare B[];

for [i] {
  A[i] = x;
  A[i] = A[i] * y;
  A[i] = A[i] + B[i];
  A[i] = B[i] * B[i];
}
```

Notice `x` and `y` (called constant variables). They are deemed constant variables because they are used in the program but they aren't declared. They need to be replaced by literals. There are also implicit constant variables `i_less_eq` and `i_greater_eq` representing the loop bounds such that `i` iterates over the range `[i_greater_eq, i_less_eq]` with step size of 1. Also notice that the array sizes are unspecified.

When all constant variables are replaced with literals and array sizes are determined, a pattern becomes an instance.

### Instances

An instance is a program operating on arrays. It has enough information to generate a C program. Here's an example instance. Note that it includes the array sizes, the loop bounds, and the loop step.

```
declare A[100];
declare B[100];

for [(i, >=0, <=99, +=1)] {
  A[i] = 5;
  A[i] = A[i] * 2;
  A[i] = A[i] + B[i];
  A[i] = B[i] * B[i];
}
```

## Usage

Example usages can be found in the [examples](examples) directory.

When running the examples, make sure the root directory of the repo is in PYTHONPATH.

```
# Current directory is root of the repo
export PYTHONPATH=$(pwd)

# Running an example from the examples directory
python3 examples/parse-skeleton.py
```

We recommend learning the examples in this sequence.
1. [Parse a skeleton](examples/parse-skeleton.py)
1. [Fill a name hole](examples/fill-name-hole.py)
1. [Fill an operator hole](examples/fill-operator-hole.py)
1. [Fill an expression hole](examples/fill-expr-hole.py)
1. [Fill a statement hole](examples/fill-stmt-hole.py)
1. [Parse a pattern](examples/parse-pattern.py)
1. [Create an instance](examples/create-instance.py)
1. [Generate random matmul code](examples/matmul.py)
1. [Exhaustively generate matmul code](examples/matmul-exhaustive.py)

Once an instance is created, users may generate code by visiting the generated AST. (TODO: include an example C code generator)
