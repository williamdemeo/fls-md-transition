-- agda-filter.lua
-- Converts pre-processed LaTeX AST elements into .lagda.md format

local PANDOC_VERSION = pandoc.utils.pandoc_version

-- Helper function to reconstruct code string from list of Paras/Strs/Spaces etc.
-- This needs to be careful about preserving formatting/indentation.
local function reconstruct_code(blocks)
  local code_lines = {}
  for i, block in ipairs(blocks) do
    -- Use pandoc.utils.stringify to get raw text content of each block (likely a Para)
    -- This might collapse whitespace, need care. A more manual traversal might be better.
    local block_text = pandoc.utils.stringify(block)
    table.insert(code_lines, block_text)
  end
  -- Join lines with newline. This is a basic version and might need
  -- refinement based on how Pandoc structures the content (e.g., SoftBreaks).
  -- It likely won't preserve original indentation perfectly without more complex traversal.
  local reconstructed = table.concat(code_lines, "\n")
  -- A common issue: pandoc.utils.stringify might add unwanted spaces or process escapes.
  -- A safer (but more verbose) approach involves walking the inline elements manually.
  -- For now, let's see what stringify produces.

  -- Basic cleanup: Trim leading/trailing whitespace from the whole block
  reconstructed = reconstructed:match("^%s*(.-)%s*$")

  return reconstructed
end


-- Helper function to parse key=value pairs from placeholder string
-- e.g., "basename=Acnt, class=AgdaRecord"
local function parse_placeholder_args(arg_string)
  local args = {}
  for key, value in string.gmatch(arg_string, "([%w_]+)=([^,]+)") do
    -- Trim whitespace from value just in case
    value = value:match("^%s*(.-)%s*$")
    args[key] = value
  end
  return args
end

-- Process Div blocks (mainly for code environments)
function Div(div)
  -- Check for VisibleAgdaCode
  if pandoc.utils.list_contains(div.classes, "VisibleAgdaCode") then
    local code_str = reconstruct_code(div.content)
    -- Create a CodeBlock with 'agda' class
    -- Attributes format depends on pandoc version
    local attrs = pandoc.Attr("", {"agda"}, {}) -- Pandoc 3.x format
    if PANDOC_VERSION < {3,0,0} then
       attrs = {"", {"agda"}, {}} -- Pandoc 2.x format
    end
    return pandoc.CodeBlock(code_str, attrs)
  end

  -- Check for HiddenAgdaCode
  if pandoc.utils.list_contains(div.classes, "HiddenAgdaCode") then
    local code_str = reconstruct_code(div.content)
    -- Wrap the reconstructed code (as an Agda fenced block) in HTML comments
    local hidden_code_md = ""
    return pandoc.RawBlock("html", hidden_code_md)
  end

  -- Handle other environments like NoConway, Conway, figure*
  -- Option 1: Just return the Div, let Pandoc handle it (might become basic div in HTML)
  -- Option 2: Convert to Raw HTML block for explicit control
  -- Let's try Option 1 first for simplicity
  if pandoc.utils.list_contains(div.classes, "NoConway") or
     pandoc.utils.list_contains(div.classes, "Conway") or
     pandoc.utils.list_contains(div.classes, "figure*") or
     pandoc.utils.list_contains(div.classes, "AgdaMultiCode") -- If preprocessor leaves this
  then
     -- Return the Div as is - Pandoc might render it as <div class="..."> in HTML output
     -- We might need walk_block if content needs further processing by other filter functions
     return div
     -- Alternative: return pandoc.Div(pandoc.walk_block(div.content, {}), div.attr)
  end

  -- Otherwise, return the Div unchanged
  return div
end

-- Process RawInline elements (mainly for placeholders)
function RawInline(inline)
  -- Check if it's a raw latex placeholder we created
  if inline.format:match 'latex' then
    -- Check for AgdaTermPlaceholder
    local placeholder_match = inline.text:match '\\AgdaTermPlaceholder{(.*)}'
    if placeholder_match then
      local args = parse_placeholder_args(placeholder_match)
      if args.basename and args['class'] then -- Renamed 'class' key lookup
         -- Create CSS class like 'agda-agdatype'
         local css_class = "agda-" .. args['class']:lower()
         -- Create Code inline element with attributes
         -- Pandoc 3.x uses Attr constructor; earlier versions used plain tables.
         local attrs
         if PANDOC_VERSION >= {3,0,0} then
             attrs = pandoc.Attr("", {css_class}, {})
         else
             attrs = {"", {css_class}, {}}
         end
         return pandoc.Code(args.basename, attrs)
      end
    end

    -- Check for HighlightPlaceholder
    local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
    if highlight_match then
       local content_str = highlight_match -- Simple string content for now
       -- We should ideally parse content_str back to Pandoc Inline elements
       -- For now, assume simple text:
       local content_inline = { pandoc.Str(content_str) }
       -- Wrap in a Span with class 'highlight'
       local attrs
       if PANDOC_VERSION >= {3,0,0} then
           attrs = pandoc.Attr("", {"highlight"}, {})
       else
           attrs = {"", {"highlight"}, {}}
       end
       return pandoc.Span(content_inline, attrs)
    end

  end

  -- Otherwise return the RawInline element unchanged
  return inline
end

-- Note: We might need handlers for other elements like Para, Header etc.
-- if the pre-processor or default LaTeX reader introduces things
-- that need adjustment for Markdown output (e.g., figure captions).
