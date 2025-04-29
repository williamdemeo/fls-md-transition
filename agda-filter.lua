-- agda-filter.lua
-- Converts pre-processed LaTeX AST elements into .lagda.md format
-- Corrected version: Replaces non-existent pandoc.utils.list_contains

local PANDOC_VERSION = pandoc.utils.pandoc_version

-- Helper function to check if a Lua list (table) contains an item
local function list_contains(list, item)
  if not list then return false end -- Guard against nil list
  for _, value in ipairs(list) do
    if value == item then
      return true
    end
  end
  return false
end

-- Helper function to reconstruct code string from list of Paras/Strs/Spaces etc.
local function reconstruct_code(blocks)
  -- (Keep the previous version of this function - it might need refinement later,
  -- but wasn't the cause of the current error)
  local code_lines = {}
  for i, block in ipairs(blocks) do
    local block_text = pandoc.utils.stringify(block)
    table.insert(code_lines, block_text)
  end
  local reconstructed = table.concat(code_lines, "\n")
  reconstructed = reconstructed:match("^%s*(.-)%s*$")
  return reconstructed
end


-- Helper function to parse key=value pairs from placeholder string
local function parse_placeholder_args(arg_string)
  -- (Keep the previous version of this function)
  local args = {}
  for key, value in string.gmatch(arg_string, "([%w_]+)=([^,]+)") do
    value = value:match("^%s*(.-)%s*$")
    args[key] = value
  end
  return args
end

-- Process Div blocks (mainly for code environments)
function Div(div)
  -- Check for VisibleAgdaCode using the CORRECTED helper
  if list_contains(div.classes, "VisibleAgdaCode") then
    local code_str = reconstruct_code(div.content)
    local attrs = pandoc.Attr("", {"agda"}, {})
    if PANDOC_VERSION < {3,0,0} then attrs = {"", {"agda"}, {}} end
    return pandoc.CodeBlock(code_str, attrs)
  end

  -- Check for HiddenAgdaCode using the CORRECTED helper
  if list_contains(div.classes, "HiddenAgdaCode") then
    local code_str = reconstruct_code(div.content)
    local hidden_code_md = ""
    return pandoc.RawBlock("html", hidden_code_md)
  end

  -- Handle other environments using the CORRECTED helper
  if list_contains(div.classes, "NoConway") or
     list_contains(div.classes, "Conway") or
     list_contains(div.classes, "figure*") or
     list_contains(div.classes, "AgdaMultiCode")
  then
     -- Returning the Div as is for now
     return div
  end

  -- Otherwise, return the Div unchanged
  return div
end

-- Process RawInline elements (mainly for placeholders)
function RawInline(inline)
  -- (Keep the previous version of this function - it was not the cause of the error)
  if inline.format:match 'latex' then
    local placeholder_match = inline.text:match '\\AgdaTermPlaceholder{(.*)}'
    if placeholder_match then
      local args = parse_placeholder_args(placeholder_match)
      if args.basename and args['class'] then
         local css_class = "agda-" .. args['class']:lower()
         local attrs
         if PANDOC_VERSION >= {3,0,0} then attrs = pandoc.Attr("", {css_class}, {})
         else attrs = {"", {css_class}, {}} end
         return pandoc.Code(args.basename, attrs)
      end
    end

    local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
    if highlight_match then
       local content_str = highlight_match
       local content_inline = { pandoc.Str(content_str) }
       local attrs
       if PANDOC_VERSION >= {3,0,0} then attrs = pandoc.Attr("", {"highlight"}, {})
       else attrs = {"", {"highlight"}, {}} end
       return pandoc.Span(content_inline, attrs)
    end
  end
  return inline
end