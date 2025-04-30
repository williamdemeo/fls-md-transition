import re
import json
import sys
import os

# --- Configuration ---
repo_url = "https://github.com/IntersectMBO/formal-ledger-specifications"
repo_src_base = "blob/master/src/Ledger"
macro_data = {}

# --- Replacement Functions ---

def expand_modulenote(match):
    """Expands \modulenote{\LedgerModule{Arg}} into text with \href."""
    inner_content = match.group(1).strip()
    module_arg_match = re.match(r'\\LedgerModule\{(.*?)\}', inner_content)
    if module_arg_match:
        module_name = module_arg_match.group(1)
        module_text = f"Ledger.{module_name}"
        module_file = f"{module_name}.lagda"
        module_url = f"{repo_url}/{repo_src_base}/{module_file}"
        module_link = f"\\href{{{module_url}}}{{\\texttt{{{module_text}}}}}"
        repo_link = f"\\href{{{repo_url}}}{{formal ledger specification}}"
        return f"This section is part of the {module_link} module of the {repo_link}"
    else:
        print(f"Warning: Unexpected content inside modulenote: {inner_content}", file=sys.stderr)
        return match.group(0)

def expand_agda_term_placeholder(match):
    """Replaces \MacroName{} with \AgdaTermPlaceholder{...} using loaded JSON data."""
    global macro_data
    macro_name = match.group(1)
    term_info = macro_data.get("agda_terms", {}).get(macro_name)
    if term_info and isinstance(term_info, dict):
        basename = term_info.get("basename", macro_name)
        agda_class = term_info.get("agda_class", "AgdaUnknown")
        return f"\\AgdaTermPlaceholder{{basename={basename}, class={agda_class}}}"
    else:
        print(f"Warning: Macro {macro_name} not found / malformed in JSON.", file=sys.stderr)
        return match.group(0)

def expand_hldiff(match):
    """Replaces \hldiff{...} with \HighlightPlaceholder{...}."""
    content = match.group(1)
    return f"\\HighlightPlaceholder{{{content}}}"


# --- wrap_hidden / wrap_visible ---
def wrap_hidden(match):
    original_code = match.group(1) # Capture the original code content
    # DO NOT STRIP original_code
    # Basic check to avoid double-wrapping
    # Use lstrip() only for the check to handle potential leading whitespace before \begin{verbatim}
    if original_code.lstrip().startswith('\\begin{verbatim}'):
         return match.group(0)
    # Wrap the original code, preserving its whitespace. Add newlines for clarity.
    return f"\\begin{{HiddenAgdaCode}}\n\\begin{{verbatim}}{original_code}\\end{{verbatim}}\n\\end{{HiddenAgdaCode}}"

def wrap_visible(match):
    original_code = match.group(1) # Capture the original code content
    # DO NOT STRIP original_code
    # Basic check to avoid double-wrapping
    if original_code.lstrip().startswith('\\begin{verbatim}'):
         return match.group(0)
    # Wrap the original code, preserving its whitespace. Add newlines for clarity.
    return f"\\begin{{VisibleAgdaCode}}\n\\begin{{verbatim}}{original_code}\\end{{verbatim}}\n\\end{{VisibleAgdaCode}}"

# --- Main Processing Function ---
def preprocess_lagda(content):
    """Applies all preprocessing replacements, wrapping code in verbatim."""
    global macro_data

    # 1. Wrap code environments AND rename them (using MODIFIED helpers)
    # Apply to hidden blocks first
    content = re.sub(r'\\begin\{code\}\s*\[hide\](.*?)\\end\{code\}',
                     wrap_hidden,
                     content, flags=re.DOTALL)
    # Apply to remaining visible blocks
    content = re.sub(r'\\begin\{code\}(.*?)\\end\{code\}',
                     wrap_visible,
                     content, flags=re.DOTALL)

    # 2. Inline \modulenote (ensure non-greedy match for argument)
    content = re.sub(r'\\modulenote\{(.*?)\}', expand_modulenote, content)

    # 3. Replace Agda term macros with placeholders
    if macro_data.get("agda_terms"):
      agda_term_pattern = r'\\(' + '|'.join(re.escape(k) for k in macro_data["agda_terms"].keys()) + r')\{\}'
      content = re.sub(agda_term_pattern, expand_agda_term_placeholder, content)

    # 4. Replace \hldiff with placeholder (ensure non-greedy match for argument)
    content = re.sub(r'\\hldiff\{(.*?)\}', expand_hldiff, content)

    # 5. *** NEW: Remove figure* environment wrappers ***
    # Remove \begin{figure*}[optional args] line
    content = re.sub(r'^\s*\\begin\{figure\*}(\[[^\]]*\])?\s*?\n', '', content, flags=re.MULTILINE)
    # Remove \end{figure*} line
    content = re.sub(r'^\s*\\end\{figure\*\}\s*?\n?', '', content, flags=re.MULTILINE)

    return content

# --- Script Entry Point ---
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
