# Build Script Builder

Small python script that walks over the directories (in the export format from SQL Developer) and writes the build.sql script at the root that can run all the sub-scripts.

Copy buildBuild.py and buildBuild.cmd into the root of the directory (you may wish to add these files to that DB project's .gitignore) and run buildBuild.cmd

Requires Python 3+ (built and tested on Python 3.8)

# Known "issues" or quirks:
- Case-sensitive - Looks for upper-case directory names. This matches the standard output from SQL Developer's "Separate Directories" export mode
- Only looks for script files one layer deep. Again, this matches the format of SQL Developer's export, but could be modified to walk to deeper directories if this becomes an issue