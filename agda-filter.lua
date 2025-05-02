-- agda-filter.lua (Version 8 - Content Tabs)
-- Processes output from preprocess.py (which wraps Agda code in verbatim
-- within HiddenAgdaCode/VisibleAgdaCode environments, and uses
-- \texttt{@@AgdaTerm@@...} placeholders for inline terms).
-- Outputs GFM suitable for .lagda.md files, aiming to fix list rendering
-- and code block formatting/presence issues.

-- agda-filter.lua (Version 8 - Simplified for Tab Post-Processing)

-- Helper function to check if a Lua list (table) contains an item
local function list_contains(list, item) if not list then return false end; for _, value in ipairs(list) do if value == item then return true end end; return false end
-- Helper function to parse key=value pairs from marker string
local function parse_placeholder_args_from_marker(marker_text) local args = {}; for key, value in string.gmatch(marker_text, "([^=@]+)=([^@]+)") do key = key:match("^%s*(.-)%s*$"); value = value:match("^%s*(.-)%s*$"); args[key] = value end; return args end
-- Helper function to create Pandoc attributes (2.x/3.x compatible)
local function create_attrs(classes, kv_pairs) classes = classes or {}; kv_pairs = kv_pairs or {}; if type(pandoc.Attr) == "function" then return pandoc.Attr("", classes, kv_pairs) else return {"", classes, kv_pairs} end end

-- Process Div blocks - simplified, no longer handles NoConway/Conway specially
function Div(div)
  -- Walk Divs using the inline handlers (Code, RawInline)
  -- This ensures placeholders inside any Div are processed.
  local walkers = { Code = Code, RawInline = RawInline }
  return pandoc.walk_block(div, walkers)
end

-- Process RawInline elements (mainly for HighlightPlaceholder)
function RawInline(inline)
  if inline.format and inline.format:match 'latex' then
    -- Use non-greedy match for content
    local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
    if highlight_match then
       local content_str = highlight_match;
       -- Assume simple text content
       local content_inline = { pandoc.Str(content_str) }
       local attrs = create_attrs({"highlight"});
       return pandoc.Span(content_inline, attrs)
    end
  end
  return inline
end

-- Process Code inline elements (to find AgdaTerm markers)
function Code(inline)
  local marker_match = inline.text:match "^%s*@@AgdaTerm@@(.-)@@%s*$"
  if marker_match then
     local payload = marker_match; local args = parse_placeholder_args_from_marker(payload)
     if args.basename and args['class'] then
         local css_class = "agda-" .. args['class']:lower(); local attrs = create_attrs({css_class})
         return pandoc.Code(args.basename, attrs)
     else
        print("Warning: Could not parse AgdaTerm marker payload: " .. payload);
        return inline -- Return original Code with marker if parsing fails
     end
  end
  return inline
end
