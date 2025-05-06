# postprocess.py
import re
import json
import sys
import io

# Helper function to indent a block of text
def indent_block(text, prefix="    "):
    lines = text.split('\n')
    indented_lines = [(prefix + line if line.strip() else line) for line in lines]
    return "\n".join(indented_lines)

# Code block replacer
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
    # Use rstrip() to remove only trailing whitespace before check/add
    content_rstrip = content.rstrip()
    if content and not content_rstrip.endswith('\n'):
       content = content_rstrip + '\n'
    else:
       # If original content was empty or only whitespace, keep it empty maybe?
       # Or just use the rstrip version if it wasn't empty
       if content.strip(): # If there was non-whitespace content
           content = content_rstrip + '\n'
       else: # Handle case where content was purely whitespace/empty
           content = '\n' # Ensure at least a newline

    if is_hidden:
        title = "Supporting source code"
        # Indent the code content itself by 4 spaces for nesting under ```agda
        indented_code_content = indent_block(content, prefix="    ")
        # Format as COLLAPSED admonition containing the code block (indented again)
        replacement_str = f'\n??? note "{title}"\n\n    ```agda\n{indented_code_content}    ```\n' # Note final ``` is indented
        return replacement_str
    else: # Visible code block
        # Indent the code content itself by 4 spaces
        indented_code_content = indent_block(content, prefix="    ")
        # Format as EXPANDED admonition (!!! note) containing the code block
        replacement_str = f'\n!!! note\n\n    ```agda\n{indented_code_content}    ```\n' # Note final ``` is indented
        return replacement_str

# In postprocess.py

def process_conway_admonitions(content):
    """Finds Conway markers, converts them to admonitions, and indents content."""
    output_lines = []
    is_indenting_admonition = False
    indent_prefix = "    " # 4 spaces

    # Using the simplified regex assuming marker is alone on line after strip
    admonition_start_pattern = re.compile(r'^\s*@@ADMONITION_START\\\|(.*?)\s*@@\s*$')
    # admonition_start_pattern = re.compile(r'^\s*@@ADMONITION_START\|(.*?)\s*@@\s*$')
    admonition_end_pattern = re.compile(r'^\s*@@ADMONITION_END@@\s*$')

    print("\nDEBUG: Starting process_conway_admonitions...", file=sys.stderr)
    # Process line by line
    for i, line in enumerate(content.splitlines()):
        line_stripped = line.strip()

        # *** ADD/UNCOMMENT THIS DEBUG PRINT VVV ***
        print(f"DEBUG: Line {i+1} (stripped): {repr(line_stripped)}", file=sys.stderr)

        start_match = admonition_start_pattern.match(line_stripped)
        end_match = admonition_end_pattern.match(line_stripped)

        if start_match:
            title = start_match.group(1).strip() if start_match.group(1) else "Conway specifics"
            print(f"DEBUG: Found START marker on line {i+1}. Title='{title}'", file=sys.stderr) # DEBUG
            output_lines.append(f'\n??? note "{title}"\n')
            is_indenting_admonition = True
        elif end_match and is_indenting_admonition:
             print(f"DEBUG: Found END marker on line {i+1}.", file=sys.stderr) # DEBUG
             is_indenting_admonition = False
        elif is_indenting_admonition:
            # Indent content lines (same as before)
            if line.strip() or line.isspace():
                 output_lines.append(indent_prefix + line)
            else:
                 output_lines.append(line)
        else:
            output_lines.append(line)

    print("DEBUG: Finished process_conway_admonitions.", file=sys.stderr) # DEBUG
    return "\n".join(output_lines) + "\n"

# Ensure other parts of postprocess.py (imports, replace_code_placeholder, __main__) are present

# Conway Admonition processing (Revised based on working Tab logic)
# def process_conway_admonitions(content):
#     """Finds Conway markers, converts them to admonitions, and indents content."""
#     output_lines = []
#     is_indenting_admonition = False
#     indent_prefix = "    " # 4 spaces for admonition content

#     # Regex to find the marker at the beginning of a line, capturing title and rest of line
#     admonition_start_pattern = re.compile(r'^\s*@@ADMONITION_START\|(.*?)\s*@@\s*$')
#     admonition_end_pattern = re.compile(r'^\s*@@ADMONITION_END@@\s*$')

#     for line in content.splitlines():
#         line_stripped = line.strip() # Check against stripped line
#         start_match = admonition_start_pattern.match(line_stripped)
#         end_match = admonition_end_pattern.match(line_stripped)

#         if start_match:
#             title = start_match.group(1).strip() if start_match.group(1) else "Conway specifics"
#             # No rest_of_line needed with this regex as we match the whole stripped line
#             print(f"DEBUG: Found START marker on line: {line_stripped}", file=sys.stderr) # DEBUG
#             output_lines.append(f'\n??? note "{title}"\n')
#             is_indenting_admonition = True
#         elif end_match and is_indenting_admonition:
#              print(f"DEBUG: Found END marker on line: {line_stripped}", file=sys.stderr) # DEBUG
#              is_indenting_admonition = False
#              # Don't append end marker line
#         elif is_indenting_admonition:
#             if line.strip() or line.isspace():
#                 output_lines.append(indent_prefix + line) # Indent original line
#             else:
#                 output_lines.append(line)
#         else:
#             output_lines.append(line)
#     return "\n".join(output_lines) + "\n"

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
