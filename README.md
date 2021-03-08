# LoopGen

A tool that generates loops.

## System requirements

Tested and works with Python 3.8

## Installation

Requires z3, lark and loguru.

```
pip3 install --user z3-solver lark-parser loguru
```

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

An instance is a program operating on arrays. It has enough information to generate a C program. Here's an example instance.

```
declare A[100];
declare B[100];

for [(i, >=0, <=99)] {
  A[i] = 5;
  A[i] = A[i] * 2;
  A[i] = A[i] + B[i];
  A[i] = B[i] * B[i];
}
```

## API

TODO: Write API documentation
