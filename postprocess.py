# postprocess.py (Phase 1 - Revised Tab Processing)
import re
import json
import sys

def replace_code_placeholder(match, code_blocks):
    """Replaces code placeholder ID with formatted code block."""
    placeholder_id = match.group(0)
    block_data = code_blocks.get(placeholder_id)
    if not block_data:
        print(f"Warning: Code block data not found for {placeholder_id}", file=sys.stderr)
        return placeholder_id # Return placeholder if data missing
    content = block_data.get("content", "")
    is_hidden = block_data.get("hidden", False)
    # Ensure content ends with newline (already done in preprocess.py V.latest)
    # if content and not content.endswith('\n'): content += '\n'
    if is_hidden:
        # Correct f-string for hidden blocks, with surrounding newlines
        return f"\n<!--\n```agda\n{content}```\n-->\n"
    else:
        # Visible block, with surrounding newlines
        return f"\n```agda\n{content}```\n"

def process_tabs_and_indent(content):
    """Finds tab markers, converts them to === "Title", and indents content below them."""
    output_lines = []
    is_indenting = False
    indent_prefix = "    " # 4 spaces

    # Regex to find the marker at the beginning of a line, capturing title and rest of line
    # Allows optional whitespace around marker and title. Escapes the pipe | character.
    tab_marker_pattern = re.compile(r'^\s*@@TAB_TITLE\|(.*?)\s*@@(.*)')

    for line in content.splitlines():
        tab_match = tab_marker_pattern.match(line)
        #tab_match = re.match(r'^@@TAB_TITLE\|(.*)@@$', line.strip())

        if tab_match:
            # Found a tab marker line
            print(f"DEBUG: Found a tab marker line: {line}", file=sys.stderr) # DEBUG

            title = tab_match.group(1).strip()
            rest_of_line = tab_match.group(2)

            output_lines.append(f'=== "{title}"') # Output the MkDocs tab syntax
            is_indenting = True # Start indenting subsequent lines

            # Handle the content immediately following the marker on the same line
            if rest_of_line.strip():
                output_lines.append(indent_prefix + rest_of_line)
            # else: the rest of the line was blank, just proceed to next line

        elif is_indenting:
            # We are inside a tab's content, indent the current line
            if line.strip(): # Don't indent lines that are only whitespace
                output_lines.append(indent_prefix + line)
            else:
                output_lines.append(line) # Keep blank lines as they are
        else:
            # We are not inside a tab's content, append line as is
            output_lines.append(line)

    # Join lines back, adding a final newline
    return "\n".join(output_lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} <input_md_intermediate> <input_code_blocks_json> <output_lagda_md>")
        sys.exit(1)
    input_md_file, input_code_blocks_file, output_lagda_md_file = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        # Load code blocks
        with open(input_code_blocks_file, 'r', encoding='utf-8') as f_code: code_blocks = json.load(f_code)
        # Read intermediate markdown
        with open(input_md_file, 'r', encoding='utf-8') as f_md: intermediate_content = f_md.read()

        # Step 1: Replace code block placeholders first
        content_with_code = re.sub(r'@@CODEBLOCK_ID_\d+@@', lambda m: replace_code_placeholder(m, code_blocks), intermediate_content)

        # Step 2: Process tabs and indentation on the result
        final_content = process_tabs_and_indent(content_with_code)

        # Write final output
        with open(output_lagda_md_file, 'w', encoding='utf-8') as f_out: f_out.write(final_content)
        print(f"Successfully generated {output_lagda_md_file}")

    except FileNotFoundError as e: print(f"Error: Input file not found: {e.filename}", file=sys.stderr); sys.exit(1)
    except json.JSONDecodeError as e: print(f"Error: Failed to parse JSON file {input_code_blocks_file}: {e}", file=sys.stderr); sys.exit(1)
    except Exception as e: print(f"An error occurred: {e}", file=sys.stderr); sys.exit(1)
