# postprocess.py
import re
import json
import sys

# In postprocess.py

def replace_placeholder(match, code_blocks):
    """Replaces placeholder ID with formatted code block, ensuring newlines."""
    placeholder_id = match.group(0)
    # print(f"DEBUG: Found placeholder: {placeholder_id}", file=sys.stderr)
    block_data = code_blocks.get(placeholder_id)

    if not block_data:
        # print(f"DEBUG: Data not found for {placeholder_id}", file=sys.stderr)
        return placeholder_id 

    content = block_data.get("content", "")
    is_hidden = block_data.get("hidden", False)
    # print(f"DEBUG: Data found: hidden={is_hidden}, content[:50]={repr(content[:50])}...", file=sys.stderr)

    # Ensure content ends with a newline for consistency IF it's not empty
    if content and not content.endswith('\n'):
        content += '\n'

    replacement_str = "" 
    if is_hidden:
        # print(f"DEBUG: Formatting {placeholder_id} as HIDDEN", file=sys.stderr)
        # *** USE f-string AND add leading/trailing \n ***
        replacement_str = f"<!--\n```agda\n{content}```\n-->"
    else:
        # print(f"DEBUG: Formatting {placeholder_id} as VISIBLE", file=sys.stderr)
         # *** Add leading/trailing \n ***
        replacement_str = f"\n```agda\n{content}```\n"

    # print(f"DEBUG: Replacing {placeholder_id} with {len(replacement_str)} chars starting with: {repr(replacement_str[:60])}...", file=sys.stderr)
    return replacement_str
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} <input_md_intermediate> <input_code_blocks_json> <output_lagda_md>")
        sys.exit(1)

    input_md_file = sys.argv[1]
    input_code_blocks_file = sys.argv[2]
    output_lagda_md_file = sys.argv[3]

    try:
        #print(f"DEBUG: Loading code blocks from {input_code_blocks_file}", file=sys.stderr) # DEBUG
        with open(input_code_blocks_file, 'r', encoding='utf-8') as f_code:
            code_blocks = json.load(f_code)
        #print(f"DEBUG: Loaded {len(code_blocks)} code blocks.", file=sys.stderr) # DEBUG

        #print(f"DEBUG: Reading intermediate MD from {input_md_file}", file=sys.stderr) # DEBUG
        with open(input_md_file, 'r', encoding='utf-8') as f_md:
            intermediate_content = f_md.read()
        #print(f"DEBUG: Read {len(intermediate_content)} chars from intermediate file.", file=sys.stderr) # DEBUG

        # Find and replace all placeholders using the function
        #print(f"DEBUG: Starting replacement...", file=sys.stderr) # DEBUG
        final_content = re.sub(r'@@CODEBLOCK_ID_\d+@@',
                               lambda m: replace_placeholder(m, code_blocks),
                               intermediate_content)
        #print(f"DEBUG: Replacement finished. Final content length: {len(final_content)}", file=sys.stderr) # DEBUG

        # Write the final lagda.md file
        #print(f"DEBUG: Writing final output to {output_lagda_md_file}", file=sys.stderr) # DEBUG
        with open(output_lagda_md_file, 'w', encoding='utf-8') as f_out:
            f_out.write(final_content)

        # Standard success message to stdout (can be removed if only using stderr for logs)
        print(f"Successfully generated {output_lagda_md_file}") 

    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {input_json_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
