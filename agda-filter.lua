-- agda-filter.lua (Version 8 - Content Tabs)
-- Processes output from preprocess.py (which wraps Agda code in verbatim
-- within HiddenAgdaCode/VisibleAgdaCode environments, and uses
-- \texttt{@@AgdaTerm@@...} placeholders for inline terms).
-- Outputs GFM suitable for .lagda.md files, aiming to fix list rendering
-- and code block formatting/presence issues.

-- Changes Div handler for NoConway/Conway to output tab syntax.

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
local function parse_placeholder_args_from_marker(marker_text)
  local args = {}
  for key, value in string.gmatch(marker_text, "([^=@]+)=([^@]+)") do
     key = key:match("^%s*(.-)%s*$")
     value = value:match("^%s*(.-)%s*$")
     args[key] = value
  end
  return args
end

-- Helper function to create Pandoc attributes (2.x/3.x compatible)
local function create_attrs(classes, kv_pairs)
   classes = classes or {}
   kv_pairs = kv_pairs or {}
   if type(pandoc.Attr) == "function" then
       return pandoc.Attr("", classes, kv_pairs)
   else
       return {"", classes, kv_pairs}
   end
end


-- Process Div blocks
function Div(div)
  local code_str = nil
  local nested_code_block = nil

  -- Check for nested CodeBlock (from verbatim wrapper)
  if div.content and div.content[1] and div.content[1].t == "CodeBlock" then
      nested_code_block = div.content[1]
      code_str = nested_code_block.text
      if code_str and not code_str:match("\n$") then code_str = code_str .. "\n" end
  end

  -- Handle VisibleAgdaCode (Output raw GFM)
  if list_contains(div.classes, "VisibleAgdaCode") then
    if code_str then
        local visible_code_md = "```agda\n" .. code_str .. "```"
        return pandoc.RawBlock("gfm", visible_code_md)
    else
        return pandoc.Para({pandoc.Emph({pandoc.Str("Warning: No verbatim code in VisibleAgdaCode.")})})
    end
  end

  -- Handle HiddenAgdaCode (Output raw GFM comment)
  if list_contains(div.classes, "HiddenAgdaCode") then
     if code_str then
        local hidden_code_md = "<!--\n```agda\n" .. code_str .. "```\n-->"
        return pandoc.RawBlock("gfm", hidden_code_md)
     else
        return pandoc.Para({pandoc.Emph({pandoc.Str("Warning: No verbatim code in HiddenAgdaCode.")})})
     end
  end

  -- *** NEW: Handle NoConway/Conway by outputting Tab syntax ***
  local is_tab_div = false
  local tab_title = ""

  if list_contains(div.classes, "NoConway") then
      is_tab_div=true; tab_title="Pre-Conway"
  elseif list_contains(div.classes, "Conway") then
      is_tab_div=true; tab_title="Conway Features"
  end

  if is_tab_div then
     -- Define walkers for inline elements within the content
     local walkers = { Code = Code, RawInline = RawInline }
     -- Create a temporary block to walk the original Div's content
     local temp_div_for_walking = pandoc.Div(div.content)
     -- Walk the content to process placeholders etc.
     local processed_content_block = pandoc.walk_block(temp_div_for_walking, walkers)
     -- Extract the processed list of block elements
     local processed_content_ast = processed_content_block.content

     -- Create the Raw Markdown block for the tab marker: === "Title"
     -- Ensure newline after marker
     local tab_marker = pandoc.RawBlock("markdown", "=== \"" .. tab_title .. "\"\n")

     -- Build the result list: [tab_marker, processed_content...]
     -- WARNING: The pymdownx.tabbed extension requires content under a tab
     -- marker to be indented by 4 spaces in the Markdown source.
     -- Achieving this purely by manipulating the Pandoc AST here is non-trivial.
     -- This initial attempt simply places the blocks after the marker;
     -- it might NOT render correctly as tabbed content if indentation is missing.
     -- We may need to adjust this later (e.g., by converting blocks to raw
     -- markdown strings and adding indentation, or using post-processing).
     local result_blocks = {}
     table.insert(result_blocks, tab_marker)
     if processed_content_ast then
         for _, block in ipairs(processed_content_ast) do
           -- TODO: How to reliably add 4-space indent here to rendered Markdown?
           -- For now, just inserting the block directly.
           table.insert(result_blocks, block)
         end
     end
     -- Return the list of blocks, replacing the original Div
     return result_blocks
  end

  -- Handle other Divs (e.g., AgdaMultiCode if not removed) by walking content
  if list_contains(div.classes, "AgdaMultiCode") then
     local walkers = { Code = Code, RawInline = RawInline }
     return pandoc.walk_block(div, walkers)
  end

  -- Walk any other unknown Div for safety
  local walkers = { Code = Code, RawInline = RawInline }
  return pandoc.walk_block(div, walkers)
end


-- Process RawInline elements (mainly for HighlightPlaceholder)
function RawInline(inline)
  if inline.format and inline.format:match 'latex' then
    local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
    if highlight_match then
       local content_str = highlight_match
       local content_inline = { pandoc.Str(content_str) }
       local attrs = create_attrs({"highlight"})
       return pandoc.Span(content_inline, attrs)
    end
  end
  return inline
end


-- Process Code inline elements (to find AgdaTerm markers)
function Code(inline)
  local marker_match = inline.text:match "^%s*@@AgdaTerm@@(.-)@@%s*$"
  if marker_match then
     local payload = marker_match
     local args = parse_placeholder_args_from_marker(payload)
     if args.basename and args['class'] then
         local css_class = "agda-" .. args['class']:lower()
         local attrs = create_attrs({css_class})
         return pandoc.Code(args.basename, attrs)
     else
        print("Warning: Could not parse AgdaTerm marker payload: " .. payload)
        return inline
     end
  end
  return inline
end
