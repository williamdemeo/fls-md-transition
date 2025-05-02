# postprocess.py (Phase 2 - Admonitions Fixes)
import re
import json
import sys

# Helper function to indent a block of text's non-empty lines
def indent_block(text, prefix="    "):
    # Strip leading/trailing whitespace from the whole block first to handle edge cases
    text = text.strip()
    # Indent non-empty lines
    return "\n".join([prefix + line if line.strip() else line
                      for line in text.splitlines()])

# Code block replacer - Revised hidden block formatting
def replace_code_placeholder(match, code_blocks):
    """Replaces code placeholder ID with formatted code block or admonition."""
    placeholder_id = match.group(0)
    block_data = code_blocks.get(placeholder_id)
    if not block_data: return placeholder_id

    content = block_data.get("content", "")
    is_hidden = block_data.get("hidden", False)

    # Remove potential leading/trailing blank lines from captured code ONLY for formatting here
    # Keep internal whitespace/newlines intact as much as possible
    content_stripped = content.strip()

    if is_hidden:
        title = "Supporting source code" # Or "Hidden Code Details"
        # Indent the code block content itself by 4 spaces for nesting under ```agda
        indented_code_content = indent_block(content_stripped, prefix="    ")
        # Construct the admonition block string carefully
        # Admonition marker ??? starts the block
        # Content needs to be indented relative to the marker (4 spaces)
        # Code block fence ```agda needs to be indented (4 spaces)
        # Code content needs further indentation (8 spaces total) - indent_block handles the first 4
        # Closing fence ``` needs to be indented (4 spaces)

        # Let's build it line by line for clarity
        lines = [
            f'\n??? note "{title}"\n', # Start admonition (collapsed)
            f'    ```agda'           # Indented opening fence
        ]
        # Add indented code lines (already indented by 4 spaces by indent_block)
        lines.extend([f'    {line}' if line.strip() else line
                      for line in indented_code_content.splitlines()])

        lines.append('    ```')             # Indented closing fence
        lines.append('')                 # Add a newline at the end for separation

        replacement_str = "\n".join(lines)
        return replacement_str
    else:
        # Visible block - ensure leading/trailing newline separation
        # Content itself should retain original indentation
        return f"\n```agda\n{content_stripped}\n```\n"

# Renamed and Corrected Admonition Processor
def process_admonitions(content):
    """Finds admonition markers, converts them, and indents content below them."""
    output_lines = []
    is_indenting_admonition = False
    indent_prefix = "    " # 4 spaces for admonition content

    # Regex to find start marker at the beginning of a line
    admonition_start_pattern = re.compile(r'^\s*@@ADMONITION_START\|(.*?)\s*@@(.*)')
    admonition_end_pattern = re.compile(r'^\s*@@ADMONITION_END@@\s*$')

    for line in content.splitlines():
        start_match = admonition_start_pattern.match(line)
        end_match = admonition_end_pattern.match(line)

        if start_match:
            # Found start marker
            title = start_match.group(1).strip()
            rest_of_line = start_match.group(2).strip() # Capture rest of line too

            # Output the MkDocs admonition syntax (collapsible)
            output_lines.append(f'\n??? note "{title}"\n')
            is_indenting_admonition = True # Start indenting lines that follow

            # Handle the content immediately following the marker on the same line
            if rest_of_line:
                 output_lines.append(indent_prefix + rest_of_line)

        elif end_match:
            # Stop indenting when we hit the end marker
            is_indenting_admonition = False
            # Do not append the end marker line itself
        elif is_indenting_admonition:
            # If we are inside an admonition, indent the line
            # Indent lines with content or only whitespace
            if line.strip() or line.isspace():
                output_lines.append(indent_prefix + line)
            else:
                output_lines.append(line) # Keep blank lines unindented
        else:
            # Line is outside any admonition, append as is
            output_lines.append(line)

    # Join lines back, adding a final newline
    return "\n".join(output_lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 4: print(f"Usage: python {sys.argv[0]} <input_md_intermediate> <input_code_blocks.json> <output_lagda_md>"); sys.exit(1)
    input_md_file, input_code_blocks_file, output_lagda_md_file = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        with open(input_code_blocks_file, 'r', encoding='utf-8') as f_code: code_blocks = json.load(f_code)
        with open(input_md_file, 'r', encoding='utf-8') as f_md: intermediate_content = f_md.read()

        # Step 1: Replace code block placeholders (handles hidden blocks using admonitions)
        content_with_code = re.sub(r'@@CODEBLOCK_ID_\d+@@', lambda m: replace_code_placeholder(m, code_blocks), intermediate_content)

        # Step 2: Process Conway admonitions and indentation
        final_content = process_admonitions(content_with_code) # Use corrected function

        # Write final output
        with open(output_lagda_md_file, 'w', encoding='utf-8') as f_out: f_out.write(final_content)
        print(f"Successfully generated {output_lagda_md_file}")

    # ... (Keep exception handling) ...
    except FileNotFoundError as e: print(f"Error: Input file not found: {e.filename}", file=sys.stderr); sys.exit(1)
    except json.JSONDecodeError as e: print(f"Error: Failed to parse JSON file {input_code_blocks_file}: {e}", file=sys.stderr); sys.exit(1)
    except Exception as e: print(f"An error occurred: {e}", file=sys.stderr); sys.exit(1)
