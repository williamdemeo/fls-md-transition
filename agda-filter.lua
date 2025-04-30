-- agda-filter.lua (Version 4)

-- Remove the reconstruct_code function entirely

-- Helper function to check if a Lua list (table) contains an item (Keep this)
local function list_contains(list, item) 
   if not list then return false end
   for _, value in ipairs(list) do
     if value == item then
       return true
     end
   end
   return false
 end
 
 -- Helper function to parse key=value pairs (Keep this)
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
   local code_str = nil
   local nested_code_block = nil
 
   -- Find the nested CodeBlock (expected from \begin{verbatim})
   -- It should ideally be the first block element inside the Div content
   -- Check if content exists and the first element is a CodeBlock
   if div.content and div.content[1] and div.content[1].t == "CodeBlock" then
       nested_code_block = div.content[1]
       code_str = nested_code_block.text -- Get text directly, preserving formatting
   end
 
   -- Check for VisibleAgdaCode
   if list_contains(div.classes, "VisibleAgdaCode") then
     if code_str then
         -- Create a NEW CodeBlock with the extracted text and 'agda' class
         local attrs 
         if type(pandoc.Attr) == "function" then attrs = pandoc.Attr("", {"agda"}, {})
         else attrs = {"", {"agda"}, {}} end
         -- Important: Return the CodeBlock directly, NOT the Div
         return pandoc.CodeBlock(code_str, attrs) 
     else
         -- Fallback or warning if nested CodeBlock wasn't found as expected
         return pandoc.Para({pandoc.Emph({pandoc.Str("Warning: Could not find verbatim code inside VisibleAgdaCode div.")})})
     end
   end
 
   -- Check for HiddenAgdaCode
   if list_contains(div.classes, "HiddenAgdaCode") then
      if code_str then
         -- Wrap the extracted verbatim code (as an Agda fenced block) in HTML comments
         -- Important: Return the RawBlock directly, NOT the Div
         local hidden_code_md = "" 
         return pandoc.RawBlock("html", hidden_code_md)
      else
         -- Fallback or warning
         return pandoc.Para({pandoc.Emph({pandoc.Str("Warning: Could not find verbatim code inside HiddenAgdaCode div.")})})
      end
   end
 
   -- Handle other environments (Keep previous logic or adjust as needed)
   if list_contains(div.classes, "NoConway") or
      list_contains(div.classes, "Conway") or
      list_contains(div.classes, "figure*") or
      list_contains(div.classes, "AgdaMultiCode")
   then
      -- Returning the Div as is for now - let other filters or default processing handle content
      -- Use pandoc.walk_block if filter needs to apply to content *within* these divs
      return div 
   end
 
   -- Otherwise, return the Div unchanged
   return div
 end
 
 -- Process RawInline elements (mainly for placeholders) - Keep this function as is from Version 3
 function RawInline(inline)
    -- ... (same logic as previous version using parse_placeholder_args) ...
   if inline.format:match 'latex' then
     local placeholder_match = inline.text:match '\\AgdaTermPlaceholder{(.*)}'
     if placeholder_match then
       local args = parse_placeholder_args(placeholder_match)
       if args.basename and args['class'] then
          local css_class = "agda-" .. args['class']:lower()
          local attrs
          if type(pandoc.Attr) == "function" then attrs = pandoc.Attr("", {css_class}, {})
          else attrs = {"", {css_class}, {}} end
          return pandoc.Code(args.basename, attrs)
       end
     end
     local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
     if highlight_match then
        local content_str = highlight_match
        local content_inline = { pandoc.Str(content_str) }
        local attrs
        if type(pandoc.Attr) == "function" then attrs = pandoc.Attr("", {"highlight"}, {})
        else attrs = {"", {"highlight"}, {}} end
        return pandoc.Span(content_inline, attrs)
     end
   end
   return inline
 end