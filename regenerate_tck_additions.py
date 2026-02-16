import glob
import json
import os
import subprocess


def regenerate_tests(base_dir):
    pattern = os.path.join(base_dir, "**", "*-input.adoc")
    adoc_files = glob.glob(pattern, recursive=True)

    for input_path in adoc_files:
        print(f"Regenerating {input_path}...")
        with open(input_path, "r") as f:
            content = f.read()

        parse_type = "inline" if "inline" in input_path else "block"
        payload = {"contents": content, "type": parse_type}

        env = os.environ.copy()
        env["TCK_INCLUDE_LOCATIONS"] = "true"
        env["PYTHONPATH"] = "src"

        result = subprocess.run(
            ["venv/bin/python3", "bin/tck-adapter.py"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
        )

        if result.returncode == 0:
            output_path = input_path.replace("-input.adoc", "-output.json")
            asg = json.loads(result.stdout)
            with open(output_path, "w") as f:
                json.dump(asg, f, indent=2)
                f.write("\n")
        else:
            print(f"Error regenerating {input_path}: {result.stderr}")


if __name__ == "__main__":
    regenerate_tests("tests/tck_harness/tests")
