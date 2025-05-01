# fls-translate

Scripts for translating LaTeX-based literate Agda files into Markdown-based literate
Agda.

## Features

1.  Handles hidden and visible code blocks by converting
    `\begin{code} ... \end{code}` and `\begin{code}[hide] ... \end{code}`
    to separate `div`s.
    
2.  Extracts Agda code blocks before processing with Pandoc so as to perfectly
    preserve the Agda code, reinserting it in the final output file exactly as it
    appeared in the original version.
    
3.  Handles macros that are aliases to `\Agda<keyword>{}` macros for typesetting
    keywords in the appropriate colors. 



## How to use the scripts

**Pipeline Command Sequence:**

1.  **Generate Macro JSON**.  Convert LaTeX macros to JSON structure for use in preprocessing step.
    ```bash
    python generate_macro_json.py macros.sty preprocess_macros.json
    ```

2.  **Pre-processing step (`preprocess.py`)**.  Generate `.lagda.temp` and save code blocks. 

    Convert `lagda` file to a temporary file called `Transaction.lagda.temp` that
    is easier for Pandoc to handle, extracting and saving Agda code blocks with
    identifiers in a JSON file called `code_blocks.json` (ensuring Pandoc doesn't
    touch any Agda code).
    ```bash
    python preprocess.py Transaction.lagda preprocess_macros.json code_blocks.json > Transaction.lagda.temp
    ```

3.  **Pandoc + Lua Filter step (`agda-filter.lua`)**. Process prose and inline placeholders.

    ```bash
    pandoc Transaction.lagda.temp -f latex -t gfm+attributes --lua-filter=agda-filter.lua -o Transaction.md.intermediate
    ```

4.  **Post-processing step (`postprocess.py`):** Generate final `.lagda.md` file by
    substituting code block placeholders.

    ```bash
    python postprocess.py Transaction.md.intermediate code_blocks.json Transaction.lagda.md
    ```
