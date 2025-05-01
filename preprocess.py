# In preprocess.py
import re
import json # Ensure these are imported
import sys
import os

# --- Configuration & Global Data --- (Keep as is)
repo_url = "https://github.com/IntersectMBO/formal-ledger-specifications"
repo_src_base = "blob/master/src/Ledger"
macro_data = {} # Ensure this is loaded in __main__

# --- Placeholder expansion functions --- (Keep as is)
def expand_agda_term_placeholder(match):
    # ... (ensure this uses \texttt{@@AgdaTerm@@...}) ...
    global macro_data
    macro_name = match.group(1)
    term_info = macro_data.get("agda_terms", {}).get(macro_name)
    if term_info and isinstance(term_info, dict):
        basename = term_info.get("basename", macro_name)
        agda_class = term_info.get("agda_class", "AgdaUnknown")
        return f"\\texttt{{@@AgdaTerm@@basename={basename}@@class={agda_class}@@}}"
    else:
        # print(f"Warning: Macro {macro_name} not found / malformed in JSON.", file=sys.stderr)
        # Return original if not found, maybe add warning later if needed
        return match.group(0)


def expand_hldiff(match):
    # ... (ensure this uses \HighlightPlaceholder) ...
    content = match.group(1)
    return f"\\HighlightPlaceholder{{{content}}}"

# --- Code wrapping functions --- (Keep as is from previous step, without .strip())
def wrap_hidden(match):
    original_code = match.group(1)
    if original_code.lstrip().startswith('\\begin{verbatim}'): return match.group(0)
    return f"\\begin{{HiddenAgdaCode}}\n\\begin{{verbatim}}{original_code}\\end{{verbatim}}\n\\end{{HiddenAgdaCode}}"

def wrap_visible(match):
    original_code = match.group(1)
    if original_code.lstrip().startswith('\\begin{verbatim}'): return match.group(0)
    return f"\\begin{{VisibleAgdaCode}}\n\\begin{{verbatim}}{original_code}\\end{{verbatim}}\n\\end{{VisibleAgdaCode}}"


# --- Main Processing Function ---
def preprocess_lagda(content):
    """Applies all preprocessing replacements..."""
    global macro_data

    # 1. Wrap code environments (Using existing wrap_hidden/wrap_visible)
    content = re.sub(r'\\begin\{code\}\s*\[hide\](.*?)\\end\{code\}',
                     wrap_hidden,
                     content, flags=re.DOTALL)
    content = re.sub(r'\\begin\{code\}(.*?)\\end\{code\}',
                     wrap_visible,
                     content, flags=re.DOTALL)

    # *** 2. Inline \modulenote - REVISED HANDLING ***
    # Define the replacement function directly here or call a helper
    def replace_modulenote_direct(match):
        module_name = match.group(1) # Capture group 1 is the module name
        module_text = f"Ledger.{module_name}"
        module_file = f"{module_name}.lagda"
        # Basic URL construction, assumes module is directly under src/Ledger/
        module_url = f"{repo_url}/{repo_src_base}/{module_file}"
        # Use \href{URL}{\texttt{TEXT}} format
        module_link = f"\\href{{{module_url}}}{{\\texttt{{{module_text}}}}}"
        repo_link = f"\\href{{{repo_url}}}{{formal ledger specification}}"
        # Construct the full sentence from the original macro definition
        return f"This section is part of the {module_link} module of the {repo_link}"

    # Use the more specific regex targeting the known structure:
    # Match \modulenote{ possibly spaces \LedgerModule{ CAPTURE_THIS } possibly spaces }
    content = re.sub(r'\\modulenote\{\s*\\LedgerModule\{(.*?)\}\s*\}',
                     replace_modulenote_direct,
                     content)

    # 3. Replace Agda term macros with \texttt{@@...@@} placeholders (Ensure this uses the correct function)
    if macro_data.get("agda_terms"):
      agda_term_pattern = r'\\(' + '|'.join(re.escape(k) for k in macro_data["agda_terms"].keys()) + r')\{\}'
      content = re.sub(agda_term_pattern, expand_agda_term_placeholder, content)

    # 4. Replace \hldiff with placeholder (Ensure this uses the correct function)
    content = re.sub(r'\\hldiff\{(.*?)\}', expand_hldiff, content)

    # 5. Remove figure* wrappers (Same as previous version)
    content = re.sub(r'^\s*\\begin\{figure\*}(\[[^\]]*\])?\s*?\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*\\end\{figure\*\}\s*?\n?', '', content, flags=re.MULTILINE)

    return content

# --- Script Entry Point --- (Keep as is, loading JSON etc.)
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_lagda_file> <input_macros_json_file>")
        sys.exit(1)

    input_lagda_file = sys.argv[1]
    input_json_file = sys.argv[2]

    try:
        with open(input_json_file, 'r', encoding='utf-8') as f_json:
            macro_data = json.load(f_json)

        with open(input_lagda_file, 'r', encoding='utf-8') as f_lagda:
            input_content = f_lagda.read()

        processed_content = preprocess_lagda(input_content)

        sys.stdout.write(processed_content)

    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {input_json_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)