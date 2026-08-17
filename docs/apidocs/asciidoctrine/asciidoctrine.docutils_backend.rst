:py:mod:`asciidoctrine.docutils_backend`
========================================

.. py:module:: asciidoctrine.docutils_backend

.. autodoc2-docstring:: asciidoctrine.docutils_backend
   :parser: sphinx_asciidoctrine.parser
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`DocutilsRenderer <asciidoctrine.docutils_backend.DocutilsRenderer>`
     - .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer
          :parser: sphinx_asciidoctrine.parser
          :summary:

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`asciidoc_to_docutils <asciidoctrine.docutils_backend.asciidoc_to_docutils>`
     - .. autodoc2-docstring:: asciidoctrine.docutils_backend.asciidoc_to_docutils
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:class:: DocutilsRenderer(document: docutils.nodes.document)
   :canonical: asciidoctrine.docutils_backend.DocutilsRenderer

   Bases: :py:obj:`asciidoctrine.nodes.NodeVisitor`

   .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.__init__
      :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_document(node: asciidoctrine.nodes.Document) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_document

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_document
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_section(node: asciidoctrine.nodes.Section) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_section

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_section
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_floatingtitle(node: asciidoctrine.nodes.FloatingTitle) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_floatingtitle

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_floatingtitle
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_paragraph(node: asciidoctrine.nodes.Paragraph) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_paragraph

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_paragraph
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_text(node: asciidoctrine.nodes.Text) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_text

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_text
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_break(node: asciidoctrine.nodes.Break) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_break

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_kbd(node: asciidoctrine.nodes.Kbd) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_kbd

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_kbd
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_button(node: asciidoctrine.nodes.Button) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_button

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_button
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_menu(node: asciidoctrine.nodes.Menu) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_menu

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_menu
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_calloutlist(node: asciidoctrine.nodes.CalloutList) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_calloutlist

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_calloutlist
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_calloutlistitem(node: asciidoctrine.nodes.CalloutListItem) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_calloutlistitem

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_calloutlistitem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_callout(node: asciidoctrine.nodes.Callout) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_callout

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_callout
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_span(node: asciidoctrine.nodes.Span) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_span

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_span
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_list(node: asciidoctrine.nodes.List) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_list

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_list
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_table(node: asciidoctrine.nodes.Table) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_table

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_table
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_row(node: asciidoctrine.nodes.TableRow) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_row

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_row
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_cell(node: asciidoctrine.nodes.TableCell) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_cell

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_cell
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_listitem(node: asciidoctrine.nodes.ListItem) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_listitem

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_listitem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlist(node: asciidoctrine.nodes.DescriptionList) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_descriptionlist

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_descriptionlist
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlistitem(node: asciidoctrine.nodes.DescriptionListItem) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_descriptionlistitem

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_descriptionlistitem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_descriptionlistterm(node: asciidoctrine.nodes.DescriptionListTerm, **kwargs: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_descriptionlistterm

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_descriptionlistterm
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_ref(node: asciidoctrine.nodes.Ref) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_ref

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_ref
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_listing(node: asciidoctrine.nodes.Listing) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_listing

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_listing
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_passthrough(node: asciidoctrine.nodes.Passthrough) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_passthrough

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_passthrough
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_stem(node: asciidoctrine.nodes.Stem) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_stem

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_stem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_inlinestem(node: asciidoctrine.nodes.InlineStem) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_inlinestem

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_inlinestem
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_admonition(node: asciidoctrine.nodes.Admonition) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_admonition

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_admonition
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_image(node: asciidoctrine.nodes.Image) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_image

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_image
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: _append_attribution(bq: docutils.nodes.Element, attribution: typing.Optional[str], citetitle: typing.Optional[str]) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer._append_attribution

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer._append_attribution
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_quote(node: asciidoctrine.nodes.Quote) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_quote

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_quote
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_verse(node: asciidoctrine.nodes.Verse) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_verse

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_verse
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_open(node: asciidoctrine.nodes.Open) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_open

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_open
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_thematic_break(node: asciidoctrine.nodes.ThematicBreak) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_thematic_break

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_thematic_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_toc(node: asciidoctrine.nodes.Toc) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_toc

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_toc
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_audio(node: asciidoctrine.nodes.Audio) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_audio

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_audio
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_video(node: asciidoctrine.nodes.Video) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_video

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_video
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_sidebar(node: asciidoctrine.nodes.Sidebar) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_sidebar

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_sidebar
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_header(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_header

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_header
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_author(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_author

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_author
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_revision(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_revision

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_revision
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_page_break(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_page_break

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_page_break
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_attribute_entry(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_attribute_entry

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_attribute_entry
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_attributes(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_attributes

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_attributes
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_include(node: typing.Any) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_include

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_include
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_collapsible(node: asciidoctrine.nodes.Collapsible) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_collapsible

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_collapsible
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_indexterm(node: asciidoctrine.nodes.IndexTerm) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_indexterm

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_indexterm
         :parser: sphinx_asciidoctrine.parser

   .. py:method:: visit_docinfo(node: asciidoctrine.nodes.Docinfo) -> None
      :canonical: asciidoctrine.docutils_backend.DocutilsRenderer.visit_docinfo

      .. autodoc2-docstring:: asciidoctrine.docutils_backend.DocutilsRenderer.visit_docinfo
         :parser: sphinx_asciidoctrine.parser

.. py:function:: asciidoc_to_docutils(source: str, base_dir: typing.Optional[str] = None, safe_mode: int = 0) -> docutils.nodes.document
   :canonical: asciidoctrine.docutils_backend.asciidoc_to_docutils

   .. autodoc2-docstring:: asciidoctrine.docutils_backend.asciidoc_to_docutils
      :parser: sphinx_asciidoctrine.parser
