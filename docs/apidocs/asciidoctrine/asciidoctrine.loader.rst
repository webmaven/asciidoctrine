:py:mod:`asciidoctrine.loader`
==============================

.. py:module:: asciidoctrine.loader

.. autodoc2-docstring:: asciidoctrine.loader
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`FileProvider <asciidoctrine.loader.FileProvider>`
     - .. autodoc2-docstring:: asciidoctrine.loader.FileProvider
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`FsLoader <asciidoctrine.loader.FsLoader>`
     - .. autodoc2-docstring:: asciidoctrine.loader.FsLoader
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`MemoryLoader <asciidoctrine.loader.MemoryLoader>`
     - .. autodoc2-docstring:: asciidoctrine.loader.MemoryLoader
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:class:: FileProvider
   :canonical: asciidoctrine.loader.FileProvider

   Bases: :py:obj:`abc.ABC`

   .. autodoc2-docstring:: asciidoctrine.loader.FileProvider
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: read_text(path: typing.Union[str, pathlib.Path]) -> str
      :canonical: asciidoctrine.loader.FileProvider.read_text
      :abstractmethod:

      .. autodoc2-docstring:: asciidoctrine.loader.FileProvider.read_text
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: exists(path: typing.Union[str, pathlib.Path]) -> bool
      :canonical: asciidoctrine.loader.FileProvider.exists
      :abstractmethod:

      .. autodoc2-docstring:: asciidoctrine.loader.FileProvider.exists
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: is_file(path: typing.Union[str, pathlib.Path]) -> bool
      :canonical: asciidoctrine.loader.FileProvider.is_file
      :abstractmethod:

      .. autodoc2-docstring:: asciidoctrine.loader.FileProvider.is_file
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: resolve_path(path: typing.Union[str, pathlib.Path], base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> str
      :canonical: asciidoctrine.loader.FileProvider.resolve_path
      :abstractmethod:

      .. autodoc2-docstring:: asciidoctrine.loader.FileProvider.resolve_path
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: find_files(pattern: str = '*.adoc', base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> typing.List[str]
      :canonical: asciidoctrine.loader.FileProvider.find_files
      :abstractmethod:

      .. autodoc2-docstring:: asciidoctrine.loader.FileProvider.find_files
         :parser: sphinx_asciidoctrine.parser

.. py:class:: FsLoader(base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None, safe_mode: typing.Union[bool, int] = True)
   :canonical: asciidoctrine.loader.FsLoader

   Bases: :py:obj:`asciidoctrine.loader.FileProvider`

   .. autodoc2-docstring:: asciidoctrine.loader.FsLoader
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.loader.FsLoader.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: _validate_safe_path(target_abs_path: str) -> None
      :canonical: asciidoctrine.loader.FsLoader._validate_safe_path

      .. autodoc2-docstring:: asciidoctrine.loader.FsLoader._validate_safe_path
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: read_text(path: typing.Union[str, pathlib.Path]) -> str
      :canonical: asciidoctrine.loader.FsLoader.read_text

   .. py:method:: exists(path: typing.Union[str, pathlib.Path]) -> bool
      :canonical: asciidoctrine.loader.FsLoader.exists

   .. py:method:: is_file(path: typing.Union[str, pathlib.Path]) -> bool
      :canonical: asciidoctrine.loader.FsLoader.is_file

   .. py:method:: resolve_path(path: typing.Union[str, pathlib.Path], base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> str
      :canonical: asciidoctrine.loader.FsLoader.resolve_path

   .. py:method:: find_files(pattern: str = '*.adoc', base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> typing.List[str]
      :canonical: asciidoctrine.loader.FsLoader.find_files

.. py:class:: MemoryLoader(files: typing.Optional[typing.Dict[str, str]] = None, base_dir: str = '/workspace', safe_mode: typing.Union[bool, int] = True)
   :canonical: asciidoctrine.loader.MemoryLoader

   Bases: :py:obj:`asciidoctrine.loader.FileProvider`

   .. autodoc2-docstring:: asciidoctrine.loader.MemoryLoader
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.loader.MemoryLoader.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: _normalize_posix_path(path: typing.Union[str, pathlib.Path]) -> str
      :canonical: asciidoctrine.loader.MemoryLoader._normalize_posix_path
      :staticmethod:

      .. autodoc2-docstring:: asciidoctrine.loader.MemoryLoader._normalize_posix_path
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: put(path: typing.Union[str, pathlib.Path], content: str) -> None
      :canonical: asciidoctrine.loader.MemoryLoader.put

      .. autodoc2-docstring:: asciidoctrine.loader.MemoryLoader.put
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: resolve_path(path: typing.Union[str, pathlib.Path], base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> str
      :canonical: asciidoctrine.loader.MemoryLoader.resolve_path

   .. py:method:: read_text(path: typing.Union[str, pathlib.Path]) -> str
      :canonical: asciidoctrine.loader.MemoryLoader.read_text

   .. py:method:: exists(path: typing.Union[str, pathlib.Path]) -> bool
      :canonical: asciidoctrine.loader.MemoryLoader.exists

   .. py:method:: is_file(path: typing.Union[str, pathlib.Path]) -> bool
      :canonical: asciidoctrine.loader.MemoryLoader.is_file

   .. py:method:: find_files(pattern: str = '*.adoc', base_dir: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> typing.List[str]
      :canonical: asciidoctrine.loader.MemoryLoader.find_files
