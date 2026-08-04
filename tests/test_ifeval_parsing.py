import pytest
from asciidoctrine.preprocessor import Preprocessor

def test_ifeval_preprocessor_integration():
    preprocessor = Preprocessor()
    input_text = """
:backend: html5
ifeval::["{backend}" == "html5"]
Included HTML line
endif::[]
ifeval::["{backend}" == "pdf"]
Excluded PDF line
endif::[]
"""
    result = preprocessor.process(input_text)
    assert "Included HTML line" in result
    assert "Excluded PDF line" not in result
