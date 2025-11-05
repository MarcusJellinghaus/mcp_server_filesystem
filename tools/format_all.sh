#!/bin/bash
# Format all source code using black and isort

black src tests
isort --profile=black --float-to-top src tests
