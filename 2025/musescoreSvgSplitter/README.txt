PROJECT TITLE:      Musescore SVG Splitter

DEPENDENCIES:       This program requires a Python3 instance with several
                        non-default libraries installed. They can be added
                        with the command:
                            python -m pip install svglib reportlab pypdf tqdm

STARTUP:            To run the program, execute the following command:
                            python musescoreSvgSplitter.py
                    where `python` refers to an installed copy of Python 3.
                    Prompts will then be given through the command line.

COMPATIBILITY:      This program was tested on Windows 11 with Python 3.11.4.

AUTHORS:            Benjamin Whitsett
                    whitsettbe@gmail.com

MODIFIED:           Dec. 29, 2024


PURPOSE:            This program assembles pdfs of music parts initially
                    stored as svg scores from Musescore or its website
                    (as svgs are visible in application data for the
                    preview tool in the browser). Files are sorted on
                    their numerical characters only (converted to ints),
                    and the output file `mergedParts.pdf` is created
                    in the same directory where the svgs were found.

ERRORS:             Each type of object that could appear in a Musescore
                        score needs its own rule in `scoreBuilder.py`,
                        and if a new object type is encountered an error
                        will be raised. This can be remedied by extension
                        of the relevant file to include rules for the
                        offending object type.
                    Should the program crash unexpectedly, contact the
                        developer with any questions.