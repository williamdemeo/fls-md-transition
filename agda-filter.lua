-- agda-filter.lua
-- Converts pre-processed LaTeX AST elements into .lagda.md format
-- Corrected version 3: Checks for pandoc.Attr constructor existence instead of version number.

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
 
 -- Helper function to reconstruct code string
 local function reconstruct_code(blocks)
   local code_lines = {}
   for i, block in ipairs(blocks) do
     local block_text = pandoc.utils.stringify(block)
     table.insert(code_lines, block_text)
   end
   local reconstructed = table.concat(code_lines, "\n")
   reconstructed = reconstructed:match("^%s*(.-)%s*$")
   return reconstructed
 end
 
 -- Helper function to parse key=value pairs
 local function parse_placeholder_args(arg_string)
   local args = {}
   for key, value in string.gmatch(arg_string, "([%w_]+)=([^,]+)") do
     value = value:match("^%s*(.-)%s*$")
     args[key] = value
   end
   return args
 end
 
 -- Process Div blocks (mainly for code environments)
 function Div(div)
   -- Check for VisibleAgdaCode
   if list_contains(div.classes, "VisibleAgdaCode") then
     local code_str = reconstruct_code(div.content)
     local attrs -- Declare attrs variable
     -- Check if pandoc.Attr constructor exists (Pandoc 3.x+)
     if type(pandoc.Attr) == "function" then
         attrs = pandoc.Attr("", {"agda"}, {}) -- Pandoc 3.x+ style
     else
         attrs = {"", {"agda"}, {}} -- Older Pandoc 2.x style table
     end
     return pandoc.CodeBlock(code_str, attrs)
   end
 
   -- Check for HiddenAgdaCode
   if list_contains(div.classes, "HiddenAgdaCode") then
     local code_str = reconstruct_code(div.content)
     local hidden_code_md = ""
     return pandoc.RawBlock("html", hidden_code_md)
   end
 
   -- Handle other environments
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
   if inline.format:match 'latex' then
     -- Check for AgdaTermPlaceholder
     local placeholder_match = inline.text:match '\\AgdaTermPlaceholder{(.*)}'
     if placeholder_match then
       local args = parse_placeholder_args(placeholder_match)
       if args.basename and args['class'] then
          local css_class = "agda-" .. args['class']:lower()
          local attrs -- Declare attrs variable
          -- Check if pandoc.Attr constructor exists
          if type(pandoc.Attr) == "function" then
              attrs = pandoc.Attr("", {css_class}, {}) -- Pandoc 3.x+ style
          else
              attrs = {"", {css_class}, {}} -- Older Pandoc 2.x style table
          end
          return pandoc.Code(args.basename, attrs)
       end
     end
 
     -- Check for HighlightPlaceholder
     local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
     if highlight_match then
        local content_str = highlight_match
        local content_inline = { pandoc.Str(content_str) }
        local attrs -- Declare attrs variable
        -- Check if pandoc.Attr constructor exists
        if type(pandoc.Attr) == "function" then
            attrs = pandoc.Attr("", {"highlight"}, {}) -- Pandoc 3.x+ style
        else
            attrs = {"", {"highlight"}, {}} -- Older Pandoc 2.x style table
        end
        return pandoc.Span(content_inline, attrs)
     end
   end
   return inline
 end