# preprocess.py (Placeholder Version)
import re
import json
import sys
import os

# --- Configuration ---
repo_url = "https://github.com/IntersectMBO/formal-ledger-specifications"
repo_src_base = "blob/master/src/Ledger"

# --- Global Storage ---
# Stores { "placeholder_id": {"content": "...", "hidden": True/False} }
code_blocks_data = {}
code_block_counter = 0
# Stores macro definitions loaded from JSON file
macro_data = {}

# --- Replacement Functions ---

def process_code_block(match, is_hidden):
    """Captures code, stores it, returns placeholder."""
    global code_block_counter, code_blocks_data
    # Extract content between the \begin{code...} and \end{code}
    # Group 1 should capture the content due to (.*?)
    original_code = match.group(1) 
    code_block_counter += 1
    placeholder_id = f"@@CODEBLOCK_ID_{code_block_counter}@@"

    # Ensure content ends with a newline for consistency, preserve others
    # Careful: original_code might be None if regex somehow fails group capture
    if original_code is None: original_code = "" # Safety check
    if not original_code.endswith('\n'):
        original_code += '\n'

    code_blocks_data[placeholder_id] = {
        "content": original_code,
        "hidden": is_hidden
    }
    # Return ONLY the placeholder to replace the whole \begin{code}...\end{code}
    return placeholder_id

def replace_modulenote_direct(match):
    """Expands \modulenote directly"""
    module_name = match.group(1)
    module_text = f"Ledger.{module_name}"
    module_file = f"{module_name}.lagda"
    module_url = f"{repo_url}/{repo_src_base}/{module_file}"
    module_link = f"\\href{{{module_url}}}{{\\texttt{{{module_text}}}}}"
    repo_link = f"\\href{{{repo_url}}}{{formal ledger specification}}"
    return f"This section is part of the {module_link} module of the {repo_link}"

def expand_agda_term_placeholder(match):
    """Replaces \MacroName{} with \texttt{@@AgdaTerm@@...} marker"""
    global macro_data
    macro_name = match.group(1)
    term_info = macro_data.get("agda_terms", {}).get(macro_name)
    if term_info and isinstance(term_info, dict):
        basename = term_info.get("basename", macro_name)
        agda_class = term_info.get("agda_class", "AgdaUnknown")
        return f"\\texttt{{@@AgdaTerm@@basename={basename}@@class={agda_class}@@}}"
    else:
        # If macro not in JSON, return original matched text (e.g., \macro{})
        print(f"Debug: Macro {macro_name} not found in JSON, keeping original.", file=sys.stderr)
        return match.group(0) 

def expand_hldiff(match):
    """Replaces \hldiff{...} with \HighlightPlaceholder{...}."""
    # Group 1 captures the content inside \hldiff{...}
    content = match.group(1)
    return f"\\HighlightPlaceholder{{{content}}}"

# --- Main Processing Function ---
def preprocess_lagda(content):
    """Applies all preprocessing replacements."""
    global macro_data # Make sure it's accessible

    # 1. Replace code blocks with placeholders and store content
    # Important: Process hidden blocks *first* to avoid conflicts with visible regex
    # The lambda function calls process_code_block with the match object and hidden status
    content = re.sub(r'\\begin\{code\}\s*\[hide\](.*?)\\end\{code\}',
                     lambda m: process_code_block(m, is_hidden=True),
                     content, flags=re.DOTALL)
    content = re.sub(r'\\begin\{code\}(.*?)\\end\{code\}',
                     lambda m: process_code_block(m, is_hidden=False),
                     content, flags=re.DOTALL)

    # 2. Inline \modulenote
    # Use the more specific regex targeting the known structure:
    content = re.sub(r'\\modulenote\{\s*\\LedgerModule\{(.*?)\}\s*\}',
                     replace_modulenote_direct,
                     content)

    # 3. Replace Agda term macros with \texttt{@@...@@} placeholders
    if macro_data.get("agda_terms"):
      # Regex matches \MacroName{} only if MacroName is a key in the dict
      agda_term_pattern = r'\\(' + '|'.join(re.escape(k) for k in macro_data["agda_terms"].keys()) + r')\{\}'
      content = re.sub(agda_term_pattern, expand_agda_term_placeholder, content)

    # 4. Replace \hldiff with \HighlightPlaceholder
    # Use non-greedy match for content and DOTALL flag
    content = re.sub(r'\\hldiff\{(.*?)\}', expand_hldiff, content, flags=re.DOTALL) 

    # 5. Remove figure* environment wrappers
    content = re.sub(r'^\s*\\begin\{figure\*}(\[[^\]]*\])?\s*?\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*\\end\{figure\*\}\s*?\n?', '', content, flags=re.MULTILINE)

    # 6. Remove AgdaMultiCode wrappers
    content = re.sub(r'^\s*\\begin\{AgdaMultiCode\}\s*?\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*\\end\{AgdaMultiCode\}\s*?\n?', '', content, flags=re.MULTILINE)

    return content

# --- Script Entry Point ---
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} <input.lagda> <macros.json> <output_code_blocks.json>")
        sys.exit(1)

    input_lagda_file = sys.argv[1]
    input_json_file = sys.argv[2]
    output_code_blocks_file = sys.argv[3] # File to save code blocks

    # Reset global state for each run if needed (though script exits)
    code_blocks_data = {}
    code_block_counter = 0
    macro_data = {}

    try:
        # Load macro definitions
        with open(input_json_file, 'r', encoding='utf-8') as f_json:
            macro_data = json.load(f_json)

        # Read input lagda file
        with open(input_lagda_file, 'r', encoding='utf-8') as f_lagda:
            input_content = f_lagda.read()

        # Process content (this populates global code_blocks_data)
        processed_content = preprocess_lagda(input_content)

        # Output processed LaTeX (with placeholders) to stdout
        sys.stdout.write(processed_content)

        # Save the captured code blocks to the specified JSON file
        with open(output_code_blocks_file, 'w', encoding='utf-8') as f_code:
            json.dump(code_blocks_data, f_code, indent=2)
        # Use stderr for status messages to not interfere with stdout redirection
        print(f"Code blocks saved to {output_code_blocks_file}", file=sys.stderr)


    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {input_json_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
