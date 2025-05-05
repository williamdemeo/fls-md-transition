# postprocess.py (Fixing Admonitions)
import re
import json
import sys

# Helper function to indent a block of text
def indent_block(text, prefix="    "):
    # Indent non-empty lines
    return "\n".join([prefix + line if line.strip() else line
                       for line in text.splitlines()])

# Code block replacer (Revised for hidden admonition formatting)
# In postprocess.py

# Keep the indent_block helper function as defined previously:
# def indent_block(text, prefix="    "): ...

def replace_code_placeholder(match, code_blocks):
    """Replaces code placeholder ID with formatted code block or admonition."""
    placeholder_id = match.group(0)
    block_data = code_blocks.get(placeholder_id)
    if not block_data:
        print(f"Warning: Code block data not found for {placeholder_id}", file=sys.stderr)
        return placeholder_id

    # *** Get content WITHOUT stripping overall whitespace ***
    content = block_data.get("content", "")
    is_hidden = block_data.get("hidden", False)

    # Ensure content ends with a newline (important before closing fence)
    if content and not content.endswith('\n'):
        content += '\n'

    if is_hidden:
        title = "Supporting source code"
        # 1. Format the raw code block first
        code_block_str = f"```agda\n{content}```"
        # 2. Indent the entire code block string for the admonition
        indented_code_block = indent_block(code_block_str, prefix="    ")
        # 3. Construct the final admonition string with surrounding newlines
        replacement_str = f'\n??? note "{title}"\n\n{indented_code_block}\n'
        return replacement_str
    else:
        # Format as visible block, ensure surrounding newlines
        # Use the original content directly.
        return f"\n```agda\n{content}```\n"

# Conway Admonition processing (Revised based on working Tab logic)
def process_conway_admonitions(content):
    """Finds Conway markers, converts them to admonitions, and indents content."""
    output_lines = []
    is_indenting_admonition = False
    indent_prefix = "    " # 4 spaces for admonition content

    # Regex to find the marker at the beginning of a line, capturing title and rest of line
    admonition_start_pattern = re.compile(r'^\s*@@ADMONITION_START\|(.*?)\s*@@(.*)')
    admonition_end_pattern = re.compile(r'^\s*@@ADMONITION_END@@\s*$')

    for line in content.splitlines():
        start_match = admonition_start_pattern.match(line)
        end_match = admonition_end_pattern.match(line)

        if start_match:
            title = start_match.group(1).strip() if start_match.group(1) else "Conway specifics"
            rest_of_line = start_match.group(2)
            # Output the MkDocs admonition syntax (collapsible)
            output_lines.append(f'\n??? note "{title}"\n') # Add blank line after marker
            is_indenting_admonition = True # Start indenting lines that follow
            # Handle content on the same line as the marker (indent it)
            if rest_of_line.strip():
                output_lines.append(indent_prefix + rest_of_line)
        elif end_match and is_indenting_admonition:
            # Stop indenting when we hit the end marker
            is_indenting_admonition = False
            # Do not append the end marker line itself
        elif is_indenting_admonition:
            # If we are inside an admonition, indent the line
            if line.strip() or line.isspace(): # Indent lines with content or only whitespace
                output_lines.append(indent_prefix + line)
            else:
                output_lines.append(line) # Keep blank lines unindented
        else:
            # Line is outside any admonition, append as is
            output_lines.append(line)

    # Join lines back, adding a final newline
    return "\n".join(output_lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 4: print(f"Usage: python {sys.argv[0]} <input_md_intermediate> <input_code_blocks_json> <output_lagda_md>"); sys.exit(1)
    input_md_file, input_code_blocks_file, output_lagda_md_file = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        with open(input_code_blocks_file, 'r', encoding='utf-8') as f_code: code_blocks = json.load(f_code)
        with open(input_md_file, 'r', encoding='utf-8') as f_md: intermediate_content = f_md.read()

        # Step 1: Replace code block placeholders
        content_with_code = re.sub(r'@@CODEBLOCK_ID_\d+@@', lambda m: replace_code_placeholder(m, code_blocks), intermediate_content)

        # Step 2: Process Conway admonitions and indentation
        final_content = process_conway_admonitions(content_with_code)

        # Write final output
        with open(output_lagda_md_file, 'w', encoding='utf-8') as f_out: f_out.write(final_content)
        print(f"Successfully generated {output_lagda_md_file}")

    # ... (Keep exception handling) ...
    except FileNotFoundError as e: print(f"Error: Input file not found: {e.filename}", file=sys.stderr); sys.exit(1)
    except json.JSONDecodeError as e: print(f"Error: Failed to parse JSON file {input_code_blocks_file}: {e}", file=sys.stderr); sys.exit(1)
    except Exception as e: print(f"An error occurred: {e}", file=sys.stderr); sys.exit(1)
