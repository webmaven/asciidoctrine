#!/usr/bin/env python3
import sys
import json

def main():
    try:
        # Read from stdin
        input_data = sys.stdin.read()
        if not input_data:
            return

        payload = json.loads(input_data)
        # For now, we don't do anything with the payload
        # but we successfully parsed it.

        # Return a minimal valid ASG
        asg = {
            "type": "document",
            "children": []
        }
        print(json.dumps(asg))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
