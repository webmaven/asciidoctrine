:py:mod:`asciidoctrine.preprocessor`
====================================

.. py:module:: asciidoctrine.preprocessor

.. autodoc2-docstring:: asciidoctrine.preprocessor
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Preprocessor <asciidoctrine.preprocessor.Preprocessor>`
     - .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:exception:: PreprocessorError()
   :canonical: asciidoctrine.preprocessor.PreprocessorError

   Bases: :py:obj:`Exception`

   .. autodoc2-docstring:: asciidoctrine.preprocessor.PreprocessorError
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.preprocessor.PreprocessorError.__init__
      :parser: sphinx_asciidoctrine.parser

.. py:exception:: CircularIncludeError()
   :canonical: asciidoctrine.preprocessor.CircularIncludeError

   Bases: :py:obj:`asciidoctrine.preprocessor.PreprocessorError`

   .. autodoc2-docstring:: asciidoctrine.preprocessor.CircularIncludeError
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.preprocessor.CircularIncludeError.__init__
      :parser: sphinx_asciidoctrine.parser

.. py:exception:: PreprocessorWarning()
   :canonical: asciidoctrine.preprocessor.PreprocessorWarning

   Bases: :py:obj:`UserWarning`

   .. autodoc2-docstring:: asciidoctrine.preprocessor.PreprocessorWarning
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.preprocessor.PreprocessorWarning.__init__
      :parser: sphinx_asciidoctrine.parser

.. py:class:: Preprocessor(base_dir: typing.Optional[str] = None, safe_mode: bool = True, preprocess_directives: bool = True, attributes: typing.Optional[dict[str, str]] = None)
   :canonical: asciidoctrine.preprocessor.Preprocessor

   .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: _parse_attributes(attr_str: str) -> dict[str, str]
      :canonical: asciidoctrine.preprocessor.Preprocessor._parse_attributes

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor._parse_attributes
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _update_delimiter_stack(line: str, delimiter_stack: list[str]) -> None
      :canonical: asciidoctrine.preprocessor.Preprocessor._update_delimiter_stack

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor._update_delimiter_stack
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _evaluate_condition(condition_str: str) -> bool
      :canonical: asciidoctrine.preprocessor.Preprocessor._evaluate_condition

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor._evaluate_condition
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _handle_include_directive(match: re.Match[str], current_file: str, current_dir: str, line_num: int, line: str, include_stack: list[tuple[str, int, str]], delimiter_stack: list[str], in_verbatim: str | None, expected_closer: str | None) -> str
      :canonical: asciidoctrine.preprocessor.Preprocessor._handle_include_directive

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor._handle_include_directive
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: process(source: str) -> str
      :canonical: asciidoctrine.preprocessor.Preprocessor.process

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor.process
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _record_line(file_path: str, line_num: int) -> None
      :canonical: asciidoctrine.preprocessor.Preprocessor._record_line

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor._record_line
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _process_source(source: str, current_file: str, include_stack: list[tuple[str, int, str]], delimiter_stack: list[str], in_verbatim: str | None = None, expected_closer: str | None = None) -> str
      :canonical: asciidoctrine.preprocessor.Preprocessor._process_source

      .. autodoc2-docstring:: asciidoctrine.preprocessor.Preprocessor._process_source
         :parser: sphinx_asciidoctrine.parser
