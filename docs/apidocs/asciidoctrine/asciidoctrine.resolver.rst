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

   * - :py:obj:`ASGResolver <asciidoctrine.resolver.ASGResolver>`
     - .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver
          :parser: sphinx_asciidoctrine.parser
          :summary:

API
~~~

.. py:class:: ASGResolver(document: asciidoctrine.nodes.Document)
   :canonical: asciidoctrine.resolver.ASGResolver

   Bases: :py:obj:`asciidoctrine.nodes.NodeTransformer`

   .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver
      :parser: sphinx_asciidoctrine.parser

   .. rubric:: Initialization

   .. autodoc2-docstring:: asciidoctrine.resolver.ASGResolver.__init__
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
