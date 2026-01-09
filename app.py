pandas.errors.ParserError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/my-diary/app.py", line 103, in <module>
    df = pd.read_csv(DB_FILE)
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/io/parsers/readers.py", line 626, in _read
    return parser.read(nrows)
           ~~~~~~~~~~~^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/io/parsers/readers.py", line 1923, in read
    ) = self._engine.read(  # type: ignore[attr-defined]
        ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        nrows
        ^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/io/parsers/c_parser_wrapper.py", line 234, in read
    chunks = self._reader.read_low_memory(nrows)
File "pandas/_libs/parsers.pyx", line 838, in pandas._libs.parsers.TextReader.read_low_memory
File "pandas/_libs/parsers.pyx", line 905, in pandas._libs.parsers.TextReader._read_rows
File "pandas/_libs/parsers.pyx", line 874, in pandas._libs.parsers.TextReader._tokenize_rows
File "pandas/_libs/parsers.pyx", line 891, in pandas._libs.parsers.TextReader._check_tokenize_status
File "pandas/_libs/parsers.pyx", line 2061, in pandas._libs.parsers.raise_parser_error
