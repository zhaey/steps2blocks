# Steps2Blocks

Simple GUI app for converting stepmania charts to Beat Saber maps.

Developed with Python 3.9 on Linux. It should work fine on Windows, but I don't test it on there myself so let me know
if there are any issues (`zhaey#5375` on Discord).

## Usage

If you have a recent version of Python installed you should just be able to run `steps2blocks.pyz` from the release
page. A GUI will pop up allowing you to pick a `.sm` file to convert. The default values for `sample rate`
and `song length` should work fine for most songs shorter than 10 minutes.

## Building

Executable zip file releases created by running the following command in the project
root: `python -m zipapp -p "/usr/bin/env python3" steps2blocks`.
