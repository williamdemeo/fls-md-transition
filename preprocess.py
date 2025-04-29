import re
import sys
import os # For path manipulation potentially needed for URLs

# --- Configuration ---
repo_url = "https://github.com/IntersectMBO/formal-ledger-specifications"
# Base path within the repo to the 'src' directory for module links
# Adjust if your lagda files are not directly under src/Ledger/
repo_src_base = "blob/master/src/Ledger"

# Dictionary of Agda term macros to their base names for \texttt{}
# *** Needs to be populated from macros.sty ***
agda_term_macros = {
    "txins": "txins", "txouts": "txouts", "Coin": "Coin",
    "TxOut": "TxOut", "txsize": "txsize", "txid": "txid",
    "txvote": "txvote", "txprop": "txprop", "txdonation": "txdonation",
    "curTreasury": "curTreasury", "AgdaField": None, # Example: Maybe handle generic ones? Or list all specifics.
    "AgdaModule": None, # Generic handled differently
    # TODO: Add ALL relevant macros from the macros.sty list here
    # If the macro name itself is the desired text, map macro_name: macro_name
}
# Filter out None values if we added placeholders
agda_term_macros = {k: v for k, v in agda_term_macros.items() if v is not None}

# --- Replacement Functions ---

def expand_modulenote(match):
    """Expands \modulenote{\LedgerModule{Arg}} into text with \href."""
    inner_content = match.group(1).strip() # Content inside \modulenote{}
    module_arg_match = re.match(r'\\LedgerModule\{(.*?)\}', inner_content)
    if module_arg_match:
        module_name = module_arg_match.group(1)
        module_text = f"Ledger.{module_name}"
        module_file = f"{module_name}.lagda"
        # Construct full URL (simple version, assumes file is directly under repo_src_base)
        module_url = f"{repo_url}/{repo_src_base}/{module_file}"
        # Use \href with \texttt for the link text
        module_link = f"\\href{{{module_url}}}{{\\texttt{{{module_text}}}}}"
        repo_link = f"\\href{{{repo_url}}}{{formal ledger specification}}"
        return f"This section is part of the {module_link} module of the {repo_link}"
    else:
        print(f"Warning: Unexpected content inside modulenote: {inner_content}", file=sys.stderr)
        return match.group(0) # Return original if format unexpected

def expand_agda_term(match):
    """Expands \MacroName{} into \texttt{basename}."""
    macro_name = match.group(1)
    base_name = agda_term_macros.get(macro_name)
    if base_name:
        return f"\\texttt{{{base_name}}}"
    else:
        # This case shouldn't happen if the regex is built correctly
        return match.group(0)

def expand_hldiff(match):
    """Replaces \hldiff{...} with \HighlightPlaceholder{...}."""
    content = match.group(1)
    # Need to handle potential nested braces carefully if content can have them
    # Basic version assumes simple content:
    return f"\\HighlightPlaceholder{{{content}}}"

# --- Main Processing Function ---

def preprocess_lagda(content):
    """Applies all preprocessing replacements to the input content."""

    # 1. Rename code environments
    # Replace hidden blocks first (uses non-greedy .*?)
    content = re.sub(r'\\begin\{code\}\s*\[hide\](.*?)\\end\{code\}',
                     r'\\begin{HiddenAgdaCode}\1\\end{HiddenAgdaCode}',
                     content, flags=re.DOTALL)
    # Replace remaining visible blocks
    content = re.sub(r'\\begin\{code\}(.*?)\\end\{code\}',
                     r'\\begin{VisibleAgdaCode}\1\\end{VisibleAgdaCode}',
                     content, flags=re.DOTALL)

    # 2. Inline \modulenote (ensure it's not inside code blocks - harder without state)
    # Assuming modulenote primarily appears outside code for now.
    # Careful regex needed for nested braces if arguments get complex.
    # This simple version might capture too much if braces mismatch:
    content = re.sub(r'\\modulenote\{(.*?)\}', expand_modulenote, content)

    # 3. Inline Agda term macros (\txins{}, \Coin{}, etc.)
    if agda_term_macros: # Only run if dict is populated
      agda_term_pattern = r'\\(' + '|'.join(re.escape(k) for k in agda_term_macros.keys()) + r')\{\}'
      content = re.sub(agda_term_pattern, expand_agda_term, content)

    # 4. Replace \hldiff with placeholder
    # Simple version, careful with nested content:
    content = re.sub(r'\\hldiff\{(.*?)\}', expand_hldiff, content)

    # TODO: Add more replacements if other macros need inlining/placeholders

    return content

# --- Script Entry Point ---

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <input_lagda_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_content = f.read()

        processed_content = preprocess_lagda(input_content)

        # Output to stdout
        sys.stdout.write(processed_content)

    except FileNotFoundError:
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
