:py:mod:`asciidoctrine.resolver`
================================

.. py:module:: asciidoctrine.resolver

.. autodoc2-docstring:: asciidoctrine.resolver
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`WorkspaceCatalog <asciidoctrine.resolver.WorkspaceCatalog>`
     - .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceCatalog
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`ASGResolver <asciidoctrine.resolver.ASGResolver>`
     - .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`WorkspaceBuilder <asciidoctrine.resolver.WorkspaceBuilder>`
     - .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:class:: WorkspaceCatalog()
   :canonical: asciidoctrine.resolver.WorkspaceCatalog

   .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceCatalog
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceCatalog.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: index_document(file_id: str, document: asciidoctrine.nodes.Document) -> None
      :canonical: asciidoctrine.resolver.WorkspaceCatalog.index_document

      .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceCatalog.index_document
         :parser: sphinx_asciidoctrine.parser

.. py:class:: ASGResolver(document: asciidoctrine.nodes.Document, catalog: typing.Optional[asciidoctrine.resolver.WorkspaceCatalog] = None, current_file_id: typing.Optional[str] = None)
   :canonical: asciidoctrine.resolver.ASGResolver

   Bases: :py:obj:`asciidoctrine.nodes.NodeTransformer`

   .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: _resolve_docinfo_files(doc: asciidoctrine.nodes.Document) -> tuple[str, str]
      :canonical: asciidoctrine.resolver.ASGResolver._resolve_docinfo_files

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver._resolve_docinfo_files
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: resolve(node: asciidoctrine.nodes.Node) -> typing.Dict[str, typing.Any]
      :canonical: asciidoctrine.resolver.ASGResolver.resolve

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.resolve
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: generic_visit(node: asciidoctrine.nodes.Node, **kwargs: typing.Any) -> asciidoctrine.nodes.Node
      :canonical: asciidoctrine.resolver.ASGResolver.generic_visit

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.generic_visit
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_text(node: asciidoctrine.nodes.Text, **kwargs: typing.Any) -> asciidoctrine.nodes.Node
      :canonical: asciidoctrine.resolver.ASGResolver.visit_text

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.visit_text
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_attributes(node: asciidoctrine.nodes.Attributes, **kwargs: typing.Any) -> asciidoctrine.nodes.Node
      :canonical: asciidoctrine.resolver.ASGResolver.visit_attributes

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.visit_attributes
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_comment(node: asciidoctrine.nodes.Node, **kwargs: typing.Any) -> typing.Optional[asciidoctrine.nodes.Node]
      :canonical: asciidoctrine.resolver.ASGResolver.visit_comment

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.visit_comment
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_ref(node: asciidoctrine.nodes.Ref, **kwargs: typing.Any) -> asciidoctrine.nodes.Node
      :canonical: asciidoctrine.resolver.ASGResolver.visit_ref

      .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.visit_ref
         :parser: sphinx_asciidoctrine.parser

.. py:class:: WorkspaceBuilder(workspace_root: str, lark_parser_instance: typing.Optional[typing.Any] = None)
   :canonical: asciidoctrine.resolver.WorkspaceBuilder

   .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: _get_file_id(absolute_path: pathlib.Path) -> str
      :canonical: asciidoctrine.resolver.WorkspaceBuilder._get_file_id

      .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder._get_file_id
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: discover_and_parse_project() -> None
      :canonical: asciidoctrine.resolver.WorkspaceBuilder.discover_and_parse_project

      .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder.discover_and_parse_project
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: index_workspace_symbols() -> None
      :canonical: asciidoctrine.resolver.WorkspaceBuilder.index_workspace_symbols

      .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder.index_workspace_symbols
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: resolve_workspace_semantics() -> None
      :canonical: asciidoctrine.resolver.WorkspaceBuilder.resolve_workspace_semantics

      .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder.resolve_workspace_semantics
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: build() -> typing.Dict[str, typing.Dict[str, typing.Any]]
      :canonical: asciidoctrine.resolver.WorkspaceBuilder.build

      .. autodoc2-docstring:: asciidoctrine.resolver.WorkspaceBuilder.build
         :parser: sphinx_asciidoctrine.parser
