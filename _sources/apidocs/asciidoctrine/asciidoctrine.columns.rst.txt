:py:mod:`asciidoctrine.columns`
===============================

.. py:module:: asciidoctrine.columns

.. autodoc2-docstring:: asciidoctrine.columns
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`_format_percentage <asciidoctrine.columns._format_percentage>`
     - .. autodoc2-docstring:: asciidoctrine.columns._format_percentage
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`parse_cols <asciidoctrine.columns.parse_cols>`
     - .. autodoc2-docstring:: asciidoctrine.columns.parse_cols
          :parser: sphinx_asciidoctrine.parser
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`COL_SPEC_REGEX <asciidoctrine.columns.COL_SPEC_REGEX>`
     - .. autodoc2-docstring:: asciidoctrine.columns.COL_SPEC_REGEX
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`ALIGN_MAP <asciidoctrine.columns.ALIGN_MAP>`
     - .. autodoc2-docstring:: asciidoctrine.columns.ALIGN_MAP
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`VALIGN_MAP <asciidoctrine.columns.VALIGN_MAP>`
     - .. autodoc2-docstring:: asciidoctrine.columns.VALIGN_MAP
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`STYLE_MAP <asciidoctrine.columns.STYLE_MAP>`
     - .. autodoc2-docstring:: asciidoctrine.columns.STYLE_MAP
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:data:: COL_SPEC_REGEX
   :canonical: asciidoctrine.columns.COL_SPEC_REGEX
   :value: 'compile(...)'

   .. autodoc2-docstring:: asciidoctrine.columns.COL_SPEC_REGEX
      :parser: sphinx_asciidoctrine.parser

.. py:data:: ALIGN_MAP
   :canonical: asciidoctrine.columns.ALIGN_MAP
   :value: None

   .. autodoc2-docstring:: asciidoctrine.columns.ALIGN_MAP
      :parser: sphinx_asciidoctrine.parser

.. py:data:: VALIGN_MAP
   :canonical: asciidoctrine.columns.VALIGN_MAP
   :value: None

   .. autodoc2-docstring:: asciidoctrine.columns.VALIGN_MAP
      :parser: sphinx_asciidoctrine.parser

.. py:data:: STYLE_MAP
   :canonical: asciidoctrine.columns.STYLE_MAP
   :value: None

   .. autodoc2-docstring:: asciidoctrine.columns.STYLE_MAP
      :parser: sphinx_asciidoctrine.parser

.. py:function:: _format_percentage(val: float) -> str
   :canonical: asciidoctrine.columns._format_percentage

   .. autodoc2-docstring:: asciidoctrine.columns._format_percentage
      :parser: sphinx_asciidoctrine.parser

.. py:function:: parse_cols(cols_str: typing.Optional[str], fallback_col_count: int = 0) -> list[dict[str, typing.Any]]
   :canonical: asciidoctrine.columns.parse_cols

   .. autodoc2-docstring:: asciidoctrine.columns.parse_cols
      :parser: sphinx_asciidoctrine.parser
