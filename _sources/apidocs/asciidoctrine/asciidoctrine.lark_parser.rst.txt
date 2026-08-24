:py:mod:`asciidoctrine.lark_parser`
===================================

.. py:module:: asciidoctrine.lark_parser

.. autodoc2-docstring:: asciidoctrine.lark_parser
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`AsciiDocTransformer <asciidoctrine.lark_parser.AsciiDocTransformer>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`ASTSyntaxAuditor <asciidoctrine.lark_parser.ASTSyntaxAuditor>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`PermissiveSyntaxWarningAuditor <asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor
          :parser: sphinx_asciidoctrine.parser
          :summary:

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`is_continuation_paragraph <asciidoctrine.lark_parser.is_continuation_paragraph>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.is_continuation_paragraph
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`find_deepest_active_list_item <asciidoctrine.lark_parser.find_deepest_active_list_item>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.find_deepest_active_list_item
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`resolve_block_internals <asciidoctrine.lark_parser.resolve_block_internals>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.resolve_block_internals
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`split_continuation_paragraphs <asciidoctrine.lark_parser.split_continuation_paragraphs>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.split_continuation_paragraphs
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`expand_joint_paragraphs <asciidoctrine.lark_parser.expand_joint_paragraphs>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.expand_joint_paragraphs
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`resolve_list_continuations <asciidoctrine.lark_parser.resolve_list_continuations>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.resolve_list_continuations
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`validate_custom_scheme <asciidoctrine.lark_parser.validate_custom_scheme>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.validate_custom_scheme
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`build_uri_terminal <asciidoctrine.lark_parser.build_uri_terminal>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.build_uri_terminal
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`parse_to_ast <asciidoctrine.lark_parser.parse_to_ast>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.parse_to_ast
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`clear_parser_cache <asciidoctrine.lark_parser.clear_parser_cache>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.clear_parser_cache
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`get_document_parser <asciidoctrine.lark_parser.get_document_parser>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.get_document_parser
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`get_inline_parser <asciidoctrine.lark_parser.get_inline_parser>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.get_inline_parser
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`parse_inlines <asciidoctrine.lark_parser.parse_inlines>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.parse_inlines
          :parser: sphinx_asciidoctrine.parser
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Children <asciidoctrine.lark_parser.Children>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.Children
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`Transformed <asciidoctrine.lark_parser.Transformed>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.Transformed
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`DEFAULT_GRAMMAR <asciidoctrine.lark_parser.DEFAULT_GRAMMAR>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.DEFAULT_GRAMMAR
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`DEFAULT_AUTHORITY_SCHEMES <asciidoctrine.lark_parser.DEFAULT_AUTHORITY_SCHEMES>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.DEFAULT_AUTHORITY_SCHEMES
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`DEFAULT_OPAQUE_SCHEMES <asciidoctrine.lark_parser.DEFAULT_OPAQUE_SCHEMES>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.DEFAULT_OPAQUE_SCHEMES
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`RESERVED_SCHEMES_BLACKLIST <asciidoctrine.lark_parser.RESERVED_SCHEMES_BLACKLIST>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser.RESERVED_SCHEMES_BLACKLIST
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`_DOCUMENT_PARSERS <asciidoctrine.lark_parser._DOCUMENT_PARSERS>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser._DOCUMENT_PARSERS
          :parser: sphinx_asciidoctrine.parser
          :summary:
   * - :py:obj:`_INLINE_PARSERS <asciidoctrine.lark_parser._INLINE_PARSERS>`
     - .. autodoc2-docstring:: asciidoctrine.lark_parser._INLINE_PARSERS
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:exception:: AsciiDocSyntaxError(message: str, line: typing.Optional[int] = None, column: typing.Optional[int] = None, context: typing.Optional[str] = None, filepath: typing.Optional[str] = None)
   :canonical: asciidoctrine.lark_parser.AsciiDocSyntaxError

   Bases: :py:obj:`ValueError`

   .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocSyntaxError
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocSyntaxError.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: __str__() -> str
      :canonical: asciidoctrine.lark_parser.AsciiDocSyntaxError.__str__

.. py:data:: Children
   :canonical: asciidoctrine.lark_parser.Children
   :value: None

   .. autodoc2-docstring:: asciidoctrine.lark_parser.Children
      :parser: sphinx_asciidoctrine.parser

.. py:data:: Transformed
   :canonical: asciidoctrine.lark_parser.Transformed
   :value: None

   .. autodoc2-docstring:: asciidoctrine.lark_parser.Transformed
      :parser: sphinx_asciidoctrine.parser

.. py:class:: AsciiDocTransformer(*args: typing.Any, **kwargs: typing.Any)
   :canonical: asciidoctrine.lark_parser.AsciiDocTransformer

   Bases: :py:obj:`asciidoctrine.transformers.block_transformer.BlockTransformer`, :py:obj:`asciidoctrine.transformers.inline_transformer.InlineTransformer`, :py:obj:`lark.Transformer`\ [\ :py:obj:`lark.Token`\ , :py:obj:`asciidoctrine.lark_parser.Transformed`\ ]

   .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:attribute:: AUTHOR_REGEX
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.AUTHOR_REGEX
      :value: 'compile(...)'

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.AUTHOR_REGEX
         :parser: sphinx_asciidoctrine.parser

   .. py:attribute:: REVISION_REGEX
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.REVISION_REGEX
      :value: 'compile(...)'

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.REVISION_REGEX
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _set_location_from_meta(node: asciidoctrine.nodes.Node, meta: typing.Any) -> asciidoctrine.nodes.Node
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer._set_location_from_meta

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer._set_location_from_meta
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: document(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.Document
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.document

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.document
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: document_header_with_body(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.Document
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.document_header_with_body

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.document_header_with_body
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: body_only(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.Document
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.body_only

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.body_only
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _finalize_document_blocks(blocks: typing.List[typing.Any]) -> typing.List[asciidoctrine.nodes.Node]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer._finalize_document_blocks

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer._finalize_document_blocks
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _nest_sections(blocks: typing.List[asciidoctrine.nodes.Node]) -> typing.List[asciidoctrine.nodes.Node]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer._nest_sections

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer._nest_sections
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: document_header(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.Header
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.document_header

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.document_header
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: author_rev_line(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.List[asciidoctrine.nodes.Node]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.author_rev_line

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.author_rev_line
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: AUTHOR_SPECIAL_CHARS(token: lark.Token) -> lark.Token
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.AUTHOR_SPECIAL_CHARS

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.AUTHOR_SPECIAL_CHARS
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: document_title(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.Title
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.document_title

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.document_title
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: block(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.lark_parser.Transformed
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.block

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.block
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: blank_line(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.blank_line

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.blank_line
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: comment(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.comment

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.comment
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: attributed_block(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.BlockNode
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.attributed_block

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.attributed_block
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: block_metadata(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.block_metadata

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.block_metadata
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: block_title(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.Title
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.block_title

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.block_title
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: attributed_simple_block(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.BlockNode
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.attributed_simple_block

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.attributed_simple_block
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: section_title(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Tuple[int, asciidoctrine.nodes.Title]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.section_title

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.section_title
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: attribute_content(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> str
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.attribute_content

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.attribute_content
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: attribute_list(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Dict[str, str]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.attribute_list

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.attribute_list
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: ATTR_LIST_CONTENT(token: lark.Token) -> lark.Token
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.ATTR_LIST_CONTENT

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.ATTR_LIST_CONTENT
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: attribute_entry(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.AttributeEntry
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.attribute_entry

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.attribute_entry
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: block_macro(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.BlockNode
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.block_macro

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.block_macro
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: thematic_break(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.ThematicBreak
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.thematic_break

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.thematic_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: page_break(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> asciidoctrine.nodes.PageBreak
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.page_break

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.page_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: anchor(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Dict[str, str]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.anchor

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.anchor
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: inline_attribute_list(meta: typing.Any, children: asciidoctrine.lark_parser.Children) -> typing.Dict[str, str]
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.inline_attribute_list

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.inline_attribute_list
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: WHITESPACE(token: lark.Token) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.WHITESPACE

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.WHITESPACE
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _WS(token: lark.Token) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer._WS

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer._WS
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: SECTION_TITLE_LEAD(token: lark.Token) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer.SECTION_TITLE_LEAD

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer.SECTION_TITLE_LEAD
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _NEWLINE(token: lark.Token) -> typing.Any
      :canonical: asciidoctrine.lark_parser.AsciiDocTransformer._NEWLINE

      .. autodoc2-docstring:: asciidoctrine.lark_parser.AsciiDocTransformer._NEWLINE
         :parser: sphinx_asciidoctrine.parser

.. py:data:: DEFAULT_GRAMMAR
   :canonical: asciidoctrine.lark_parser.DEFAULT_GRAMMAR
   :value: 'join(...)'

   .. autodoc2-docstring:: asciidoctrine.lark_parser.DEFAULT_GRAMMAR
      :parser: sphinx_asciidoctrine.parser

.. py:class:: ASTSyntaxAuditor(source_lines: typing.List[str], line_map: typing.Optional[typing.Dict[int, typing.Tuple[str, int]]] = None)
   :canonical: asciidoctrine.lark_parser.ASTSyntaxAuditor

   Bases: :py:obj:`asciidoctrine.nodes.NodeVisitor`

   .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: _get_origin(line_idx: int) -> typing.Tuple[typing.Optional[str], int]
      :canonical: asciidoctrine.lark_parser.ASTSyntaxAuditor._get_origin

      .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor._get_origin
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlist(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.lark_parser.ASTSyntaxAuditor.visit_descriptionlist

      .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor.visit_descriptionlist
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_paragraph(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.lark_parser.ASTSyntaxAuditor.visit_paragraph

      .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor.visit_paragraph
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_cell(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.lark_parser.ASTSyntaxAuditor.visit_cell

      .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor.visit_cell
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: generic_visit(node: asciidoctrine.nodes.Node, **kwargs: typing.Any) -> typing.Any
      :canonical: asciidoctrine.lark_parser.ASTSyntaxAuditor.generic_visit

      .. autodoc2-docstring:: asciidoctrine.lark_parser.ASTSyntaxAuditor.generic_visit
         :parser: sphinx_asciidoctrine.parser

.. py:class:: PermissiveSyntaxWarningAuditor(source_lines: typing.List[str], line_map: typing.Optional[typing.Dict[int, typing.Tuple[str, int]]] = None)
   :canonical: asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor

   Bases: :py:obj:`asciidoctrine.nodes.NodeVisitor`

   .. autodoc2-docstring:: asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlist(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor.visit_descriptionlist

      .. autodoc2-docstring:: asciidoctrine.lark_parser.PermissiveSyntaxWarningAuditor.visit_descriptionlist
         :parser: sphinx_asciidoctrine.parser

.. py:function:: is_continuation_paragraph(node: asciidoctrine.nodes.Node) -> bool
   :canonical: asciidoctrine.lark_parser.is_continuation_paragraph

   .. autodoc2-docstring:: asciidoctrine.lark_parser.is_continuation_paragraph
      :parser: sphinx_asciidoctrine.parser

.. py:function:: find_deepest_active_list_item(node: asciidoctrine.nodes.Node) -> typing.Optional[typing.Union[asciidoctrine.nodes.ListItem, asciidoctrine.nodes.DescriptionListItem]]
   :canonical: asciidoctrine.lark_parser.find_deepest_active_list_item

   .. autodoc2-docstring:: asciidoctrine.lark_parser.find_deepest_active_list_item
      :parser: sphinx_asciidoctrine.parser

.. py:function:: resolve_block_internals(block: asciidoctrine.nodes.Node) -> asciidoctrine.nodes.Node
   :canonical: asciidoctrine.lark_parser.resolve_block_internals

   .. autodoc2-docstring:: asciidoctrine.lark_parser.resolve_block_internals
      :parser: sphinx_asciidoctrine.parser

.. py:function:: split_continuation_paragraphs(blocks: typing.List[asciidoctrine.nodes.Node]) -> typing.List[asciidoctrine.nodes.Node]
   :canonical: asciidoctrine.lark_parser.split_continuation_paragraphs

   .. autodoc2-docstring:: asciidoctrine.lark_parser.split_continuation_paragraphs
      :parser: sphinx_asciidoctrine.parser

.. py:function:: expand_joint_paragraphs(blocks: typing.List[asciidoctrine.nodes.Node]) -> typing.List[asciidoctrine.nodes.Node]
   :canonical: asciidoctrine.lark_parser.expand_joint_paragraphs

   .. autodoc2-docstring:: asciidoctrine.lark_parser.expand_joint_paragraphs
      :parser: sphinx_asciidoctrine.parser

.. py:function:: resolve_list_continuations(blocks: typing.List[asciidoctrine.nodes.Node]) -> typing.List[asciidoctrine.nodes.Node]
   :canonical: asciidoctrine.lark_parser.resolve_list_continuations

   .. autodoc2-docstring:: asciidoctrine.lark_parser.resolve_list_continuations
      :parser: sphinx_asciidoctrine.parser

.. py:data:: DEFAULT_AUTHORITY_SCHEMES
   :canonical: asciidoctrine.lark_parser.DEFAULT_AUTHORITY_SCHEMES
   :value: ('https?', 'ftps?', 'file', 'ircs?', 'wss?', 'git', 'ssh')

   .. autodoc2-docstring:: asciidoctrine.lark_parser.DEFAULT_AUTHORITY_SCHEMES
      :parser: sphinx_asciidoctrine.parser

.. py:data:: DEFAULT_OPAQUE_SCHEMES
   :canonical: asciidoctrine.lark_parser.DEFAULT_OPAQUE_SCHEMES
   :value: ('mailto', 'data', 'tel', 'sms')

   .. autodoc2-docstring:: asciidoctrine.lark_parser.DEFAULT_OPAQUE_SCHEMES
      :parser: sphinx_asciidoctrine.parser

.. py:data:: RESERVED_SCHEMES_BLACKLIST
   :canonical: asciidoctrine.lark_parser.RESERVED_SCHEMES_BLACKLIST
   :value: None

   .. autodoc2-docstring:: asciidoctrine.lark_parser.RESERVED_SCHEMES_BLACKLIST
      :parser: sphinx_asciidoctrine.parser

.. py:function:: validate_custom_scheme(scheme: str) -> str
   :canonical: asciidoctrine.lark_parser.validate_custom_scheme

   .. autodoc2-docstring:: asciidoctrine.lark_parser.validate_custom_scheme
      :parser: sphinx_asciidoctrine.parser

.. py:function:: build_uri_terminal(extra_authority_schemes: typing.Optional[typing.List[str]] = None, extra_opaque_schemes: typing.Optional[typing.List[str]] = None) -> str
   :canonical: asciidoctrine.lark_parser.build_uri_terminal

   .. autodoc2-docstring:: asciidoctrine.lark_parser.build_uri_terminal
      :parser: sphinx_asciidoctrine.parser

.. py:function:: parse_to_ast(source: str, grammar_file: str = DEFAULT_GRAMMAR, base_dir: typing.Optional[str] = None, safe_mode: int = 0, preprocess_directives: bool = True, strict: bool = True, extra_authority_schemes: typing.Optional[typing.List[str]] = None, extra_opaque_schemes: typing.Optional[typing.List[str]] = None, loader: typing.Optional[asciidoctrine.loader.FileProvider] = None) -> asciidoctrine.nodes.Document
   :canonical: asciidoctrine.lark_parser.parse_to_ast

   .. autodoc2-docstring:: asciidoctrine.lark_parser.parse_to_ast
      :parser: sphinx_asciidoctrine.parser

.. py:data:: _DOCUMENT_PARSERS
   :canonical: asciidoctrine.lark_parser._DOCUMENT_PARSERS
   :type: typing.Dict[typing.Tuple[str, float, typing.Tuple[str, ...], typing.Tuple[str, ...]], lark.Lark]
   :value: None

   .. autodoc2-docstring:: asciidoctrine.lark_parser._DOCUMENT_PARSERS
      :parser: sphinx_asciidoctrine.parser

.. py:data:: _INLINE_PARSERS
   :canonical: asciidoctrine.lark_parser._INLINE_PARSERS
   :type: typing.Dict[typing.Tuple[str, float], lark.Lark]
   :value: None

   .. autodoc2-docstring:: asciidoctrine.lark_parser._INLINE_PARSERS
      :parser: sphinx_asciidoctrine.parser

.. py:function:: clear_parser_cache() -> None
   :canonical: asciidoctrine.lark_parser.clear_parser_cache

   .. autodoc2-docstring:: asciidoctrine.lark_parser.clear_parser_cache
      :parser: sphinx_asciidoctrine.parser

.. py:function:: get_document_parser(grammar_file: str = DEFAULT_GRAMMAR, extra_authority_schemes: typing.Optional[typing.Tuple[str, ...]] = None, extra_opaque_schemes: typing.Optional[typing.Tuple[str, ...]] = None) -> lark.Lark
   :canonical: asciidoctrine.lark_parser.get_document_parser

   .. autodoc2-docstring:: asciidoctrine.lark_parser.get_document_parser
      :parser: sphinx_asciidoctrine.parser

.. py:function:: get_inline_parser(grammar_file: str = DEFAULT_GRAMMAR) -> lark.Lark
   :canonical: asciidoctrine.lark_parser.get_inline_parser

   .. autodoc2-docstring:: asciidoctrine.lark_parser.get_inline_parser
      :parser: sphinx_asciidoctrine.parser

.. py:function:: parse_inlines(source: str, grammar_file: str = DEFAULT_GRAMMAR) -> typing.List[asciidoctrine.nodes.Node]
   :canonical: asciidoctrine.lark_parser.parse_inlines

   .. autodoc2-docstring:: asciidoctrine.lark_parser.parse_inlines
      :parser: sphinx_asciidoctrine.parser
