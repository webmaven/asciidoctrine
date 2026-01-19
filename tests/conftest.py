import glob
import os
import re
from typing import List, Tuple


def get_all_doctest_examples() -> List[Tuple[str, str]]:
    """
    Discovers and parses all doctest examples from vendor/asciidoctor-doctest.
    Returns a list of (example_id, content) tuples.
    """
    examples_dir = os.path.join(
        "vendor", "asciidoctor-doctest", "data", "examples", "asciidoc"
    )
    if not os.path.exists(examples_dir):
        return []

    examples = []
    for adoc_file in sorted(glob.glob(os.path.join(examples_dir, "*.adoc"))):
        group_name = os.path.splitext(os.path.basename(adoc_file))[0]
        with open(adoc_file, "r") as f:
            content = f.read()

        # Split by // .id
        # We use a regex that matches the marker line at the beginning of a line
        parts = re.split(r"^// \.(.+)$", content, flags=re.MULTILINE)

        # parts[0] is everything before the first // .
        # Then parts[1] is name, parts[2] is content, parts[3] is name,
        # parts[4] is content, etc.
        for i in range(1, len(parts), 2):
            example_name = parts[i].strip()
            example_content = parts[i + 1]
            # Strip trailing empty lines but preserve leading ones if part of the
            # example actually we should probably lstrip one newline that was
            # after the // .name
            if example_content.startswith("\n"):
                example_content = example_content[1:]
            elif example_content.startswith("\r\n"):
                example_content = example_content[2:]

            example_id = f"{group_name}:{example_name}"
            examples.append((example_id, example_content))

    return examples
