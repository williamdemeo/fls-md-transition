import re
import json # Added
import sys
import os

# --- Configuration ---
# (repo_url and repo_src_base remain the same)
repo_url = "https://github.com/IntersectMBO/formal-ledger-specifications"
repo_src_base = "blob/master/src/Ledger"

# --- Global variable to store loaded macro data ---
# We load this once when the script starts
macro_data = {} 

# --- Replacement Functions ---

def expand_modulenote(match):
    """Expands \modulenote{\LedgerModule{Arg}} into text with \href."""
    # (This function remains the same as before)
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
    macro_name = match.group(1)
    term_info = macro_data.get("agda_terms", {}).get(macro_name)
    
    if term_info and isinstance(term_info, dict):
        basename = term_info.get("basename", macro_name) # Default to macro_name if basename missing
        agda_class = term_info.get("agda_class", "AgdaUnknown") # Default class if missing
        
        # Construct the placeholder string. 
        # Ensure no problematic characters for LaTeX parsing within the braces.
        # Simple key=value format should be okay.
        return f"\\AgdaTermPlaceholder{{basename={basename}, class={agda_class}}}"
    else:
        # Macro not found in JSON or JSON structure is wrong
        print(f"Warning: Macro {macro_name} not found in loaded JSON data or data malformed.", file=sys.stderr)
        return match.group(0) # Return original if macro unknown or data invalid

def expand_hldiff(match):
    """Replaces \hldiff{...} with \HighlightPlaceholder{...}."""
    # (This function remains the same as before)
    content = match.group(1)
    return f"\\HighlightPlaceholder{{{content}}}"

# --- Main Processing Function ---

def preprocess_lagda(content):
    """Applies all preprocessing replacements to the input content."""
    global macro_data # Ensure we're using the globally loaded data

    # 1. Rename code environments (Same as before)
    content = re.sub(r'\\begin\{code\}\s*\[hide\](.*?)\\end\{code\}',
                     r'\\begin{HiddenAgdaCode}\1\\end{HiddenAgdaCode}',
                     content, flags=re.DOTALL)
    content = re.sub(r'\\begin\{code\}(.*?)\\end\{code\}',
                     r'\\begin{VisibleAgdaCode}\1\\end{VisibleAgdaCode}',
                     content, flags=re.DOTALL)

    # 2. Inline \modulenote (Same as before)
    content = re.sub(r'\\modulenote\{(.*?)\}', expand_modulenote, content)

    # 3. Replace Agda term macros with placeholders *** USING LOADED JSON ***
    if macro_data.get("agda_terms"): 
      # Build pattern from keys in loaded JSON data
      agda_term_pattern = r'\\(' + '|'.join(re.escape(k) for k in macro_data["agda_terms"].keys()) + r')\{\}'
      content = re.sub(agda_term_pattern, expand_agda_term_placeholder, content) # Use the new function

    # 4. Replace \hldiff with placeholder (Same as before)
    content = re.sub(r'\\hldiff\{(.*?)\}', expand_hldiff, content)

    return content

# --- Script Entry Point ---

if __name__ == "__main__":
    # Modified to take JSON file as an argument
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_lagda_file> <input_macros_json_file>")
        sys.exit(1)

    input_lagda_file = sys.argv[1]
    input_json_file = sys.argv[2]

    try:
        # Load the JSON macro definitions first
        with open(input_json_file, 'r', encoding='utf-8') as f_json:
            macro_data = json.load(f_json) # Load into global variable

        # Now read the lagda file
        with open(input_lagda_file, 'r', encoding='utf-8') as f_lagda:
            input_content = f_lagda.read()
        
        # Process the content
        processed_content = preprocess_lagda(input_content)
        
        # Output to stdout
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
        
