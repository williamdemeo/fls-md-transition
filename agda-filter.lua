-- agda-filter.lua (Version 6 - Consolidated)
-- Processes output from preprocess.py (which wraps Agda code in verbatim
-- within HiddenAgdaCode/VisibleAgdaCode environments, and uses
-- \texttt{@@AgdaTerm@@...} placeholders for inline terms).
-- Outputs GFM suitable for .lagda.md files.
--
-- **Key Features of this Version:**
--
-- * Includes the `list_contains` helper.
-- * Includes the `parse_placeholder_args_from_marker` helper.
-- * Includes the `create_attrs` helper to handle Pandoc 2.x/3.x attribute differences.
-- * **`Div` Handler:**
--     * Finds `Div`s for `VisibleAgdaCode` and `HiddenAgdaCode`.
--     * Expects a nested `CodeBlock` (from the pre-processor's `verbatim` wrapping).
--     * Extracts the verbatim code text.
--     * Returns `pandoc.RawBlock("gfm", ...)` containing the literal desired output (`
--       ```agda...` or ``) to ensure correct formatting and prevent dropping of hidden
--       blocks.
--     * Includes warnings if the expected nested `CodeBlock` isn't found.
--     * Applies walking (`pandoc.walk_block`) to the content of other recognized `Div`s
--       (`NoConway`, etc.) to ensure placeholders inside them are processed. Added
--       default walking for unknown Divs for safety.
-- * **`RawInline` Handler:** Specifically looks for `\HighlightPlaceholder` and
--   converts it to a `Span` with class `highlight`. Added check for `inline.format`
--   existence.
-- * **`Code` Handler:** Looks for `\texttt{}` content starting with `@@AgdaTerm@@`,
--   parses the `basename` and `class`, and returns a new `Code` element with the
--   correct text and class attributes (e.g., producing ``code`` `{.agda-agdafield}`).
--   Includes fallback warning/behavior.


-- Helper function to check if a Lua list (table) contains an item
local function list_contains(list, item)
   if not list then return false end
   for _, value in ipairs(list) do
     if value == item then
       return true
     end
   end
   return false
 end
 
 -- Helper function to parse key=value pairs from marker string
 -- Example: basename=Acnt@@class=AgdaRecord
 local function parse_placeholder_args_from_marker(marker_text)
   local args = {}
   -- Match key=value pairs between @@ markers
   for key, value in string.gmatch(marker_text, "([^=@]+)=([^@]+)") do
      -- Trim whitespace just in case it sneaks in
      key = key:match("^%s*(.-)%s*$")
      value = value:match("^%s*(.-)%s*$")
      args[key] = value
   end
   return args
 end
 
 -- Determine Pandoc attribute style based on pandoc.Attr existence
 -- Creates attribute structure compatible with Pandoc 2.x and 3.x+
 local function create_attrs(classes, kv_pairs)
    classes = classes or {}
    kv_pairs = kv_pairs or {}
    -- Identifier is always empty string "" for our purposes here
    if type(pandoc.Attr) == "function" then
        -- Pandoc 3.x+ style: pandoc.Attr(identifier, classes, key-value_pairs)
        return pandoc.Attr("", classes, kv_pairs)
    else
        -- Older Pandoc 2.x style table: {identifier, classes, key-value_pairs}
        return {"", classes, kv_pairs}
    end
 end
 
 -- Process Div blocks (mainly for code environments and custom containers)
 function Div(div)
   local code_str = nil
   local nested_code_block = nil
 
   -- Find the nested CodeBlock (expected from \begin{verbatim})
   -- Check if content exists and the first element is a CodeBlock
   if div.content and div.content[1] and div.content[1].t == "CodeBlock" then
       nested_code_block = div.content[1]
       code_str = nested_code_block.text -- Get text directly, preserving formatting
       -- Ensure code_str ends with a newline for consistency in ``` blocks
       if code_str and not code_str:match("\n$") then
           code_str = code_str .. "\n"
       end
   end
 
   -- Handle VisibleAgdaCode
   if list_contains(div.classes, "VisibleAgdaCode") then
     if code_str then
         -- Output raw GFM fenced code block for exact syntax control
         local visible_code_md = "```agda\n" .. code_str .. "```"
         return pandoc.RawBlock("gfm", visible_code_md)
     else
         -- Warning if expected nested code block is missing
         return pandoc.Para({pandoc.Emph({pandoc.Str("Warning: No verbatim code found inside VisibleAgdaCode div.")})})
     end
   end
 
   -- Handle HiddenAgdaCode
   if list_contains(div.classes, "HiddenAgdaCode") then
      if code_str then
         -- Output raw GFM HTML comment wrapping a fenced code block
         local hidden_code_md = ""
         return pandoc.RawBlock("gfm", hidden_code_md)
      else
         -- Warning if expected nested code block is missing
         return pandoc.Para({pandoc.Emph({pandoc.Str("Warning: No verbatim code found inside HiddenAgdaCode div.")})})
      end
   end
 
   -- Handle other environments like NoConway, Conway, etc.
   -- We need to process their *content* with the filter too (e.g., for placeholders inside)
   if list_contains(div.classes, "NoConway") or
      list_contains(div.classes, "Conway") or
      list_contains(div.classes, "figure*") or -- Should be removed by preprocessor, but check just in case
      list_contains(div.classes, "AgdaMultiCode") -- If this wasn't removed by preprocessor
   then
      -- Walk the content first to apply inline filters (Code, RawInline)
      -- Define the walkers table for walk_block
      local walkers = { Code = Code, RawInline = RawInline }
      -- Create a dummy block to walk (walk_block needs a block, not just content table)
      local temp_div_for_walking = pandoc.Div(div.content)
      local processed_content = pandoc.walk_block(temp_div_for_walking, walkers).content
      -- Return a new Div containing the processed content, keeping the original attributes/classes
      return pandoc.Div(processed_content, div.attr)
   end
 
   -- Otherwise, return the Div unchanged (or walk its content if it might contain placeholders)
   -- Default walk might be safer if unsure about content of other Divs
   -- For safety, let's walk unknown Divs too.
   local walkers = { Code = Code, RawInline = RawInline }
   return pandoc.walk_block(div, walkers)
   -- return div -- Less safe alternative
 end
 
 
 -- Process RawInline elements (mainly for HighlightPlaceholder)
 function RawInline(inline)
   if inline.format and inline.format:match 'latex' then -- Check inline.format exists
     -- Check for HighlightPlaceholder
     -- Using non-greedy match for content
     local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
     if highlight_match then
        local content_str = highlight_match
        -- Attempt to parse the content string back into Pandoc inline elements
        -- This is simplistic; a real LaTeX parser would be needed for complex content.
        -- For now, treat as simple string.
        local content_inline = { pandoc.Str(content_str) }
        local attrs = create_attrs({"highlight"})
        return pandoc.Span(content_inline, attrs)
     end
   end
   -- Return unchanged if not a known placeholder or not latex format
   return inline
 end
 
 
 -- Process Code inline elements (to find AgdaTerm markers)
 function Code(inline)
   -- Check if the text content contains our Agda term marker
   -- Allow for optional whitespace around markers
   local marker_match = inline.text:match "^%s*@@AgdaTerm@@(.-)@@%s*$"
   if marker_match then
      local payload = marker_match
      local args = parse_placeholder_args_from_marker(payload)
      if args.basename and args['class'] then
          -- Create CSS class like 'agda-agdatype'
          local css_class = "agda-" .. args['class']:lower()
          local attrs = create_attrs({css_class})
          -- Return a new Code element with the *correct* basename and attributes
          return pandoc.Code(args.basename, attrs)
      else
         -- If parsing failed, maybe return the original marker text but as plain code?
         print("Warning: Could not parse AgdaTerm marker payload: " .. payload)
         -- Return original Code element to show the marker text for debugging
         return inline
      end
   end
 
   -- If it's not our special marker Code, return it unchanged
   return inline
 end
 