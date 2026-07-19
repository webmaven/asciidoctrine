:py:mod:`asciidoctrine.serializer`
==================================

.. py:module:: asciidoctrine.serializer

.. autodoc2-docstring:: asciidoctrine.serializer
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`AsciiDocSerializerVisitor <asciidoctrine.serializer.AsciiDocSerializerVisitor>`
     - .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor
          :parser: sphinx_asciidoctrine.parser
          :summary:

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`serialize_to_asciidoc <asciidoctrine.serializer.serialize_to_asciidoc>`
     - .. autodoc2-docstring:: asciidoctrine.serializer.serialize_to_asciidoc
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:class:: AsciiDocSerializerVisitor()
   :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor

   Bases: :py:obj:`asciidoctrine.nodes.NodeVisitor`

   .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: serialize(node: asciidoctrine.nodes.Node) -> str
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.serialize

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.serialize
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: write(s: str) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.write

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.write
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: write_block_metadata(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.write_block_metadata

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.write_block_metadata
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_document(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_document

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_document
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_header(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_header

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_header
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_section(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_section

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_section
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_title(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_title

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_title
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_paragraph(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_paragraph

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_paragraph
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_listing(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_listing

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_listing
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_literal(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_literal

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_literal
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_comment(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_comment

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_comment
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_sidebar(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_sidebar

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_sidebar
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_example(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_example

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_example
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_quote(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_quote

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_quote
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_admonition(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_admonition

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_admonition
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_open(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_open

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_open
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_list(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_list

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_list
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_listitem(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_listitem

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_listitem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlist(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_descriptionlist

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_descriptionlist
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlistitem(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_descriptionlistitem

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_descriptionlistitem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlistterm(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_descriptionlistterm

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_descriptionlistterm
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_table(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_table

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_table
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_row(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_row

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_row
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_cell(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_cell

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_cell
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_thematic_break(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_thematic_break

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_thematic_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_page_break(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_page_break

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_page_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_attribute_entry(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_attribute_entry

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_attribute_entry
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_include(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_include

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_include
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_toc(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_toc

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_toc
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_text(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_text

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_text
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_break(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_break

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_span(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_span

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_span
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_ref(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_ref

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_ref
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_image(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_image

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_image
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_audio(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_audio

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_audio
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_video(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_video

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_video
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_kbd(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_kbd

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_kbd
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_button(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_button

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_button
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_menu(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_menu

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_menu
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_callout(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_callout

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_callout
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_stem(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_stem

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_stem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_passthrough(node: asciidoctrine.nodes.Node) -> None
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_passthrough

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.visit_passthrough
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: generic_visit(node: asciidoctrine.nodes.Node, **kwargs: typing.Any) -> typing.Any
      :canonical: asciidoctrine.serializer.AsciiDocSerializerVisitor.generic_visit

      .. autodoc2-docstring:: asciidoctrine.serializer.AsciiDocSerializerVisitor.generic_visit
         :parser: sphinx_asciidoctrine.parser

.. py:function:: serialize_to_asciidoc(node: asciidoctrine.nodes.Node) -> str
   :canonical: asciidoctrine.serializer.serialize_to_asciidoc

   .. autodoc2-docstring:: asciidoctrine.serializer.serialize_to_asciidoc
      :parser: sphinx_asciidoctrine.parser
