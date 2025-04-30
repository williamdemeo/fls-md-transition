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
 local function parse_placeholder_args_from_marker(marker_text)
   local args = {}
   -- Match key=value pairs between @@ markers
   -- Example: basename=Acnt@@class=AgdaRecord
   for key, value in string.gmatch(marker_text, "([^=@]+)=([^@]+)") do
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
   if inline.format:match 'latex' then
     -- Check for HighlightPlaceholder (assuming this *does* come through as RawInline)
     local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
     if highlight_match then
        local content_str = highlight_match
        -- If content can contain markup, we need to parse it.
        -- For now, assuming simple text content:
        local content_inline = { pandoc.Str(content_str) }
        local attrs
        if type(pandoc.Attr) == "function" then attrs = pandoc.Attr("", {"highlight"}, {})
        else attrs = {"", {"highlight"}, {}} end
        return pandoc.Span(content_inline, attrs)
     end
   end
   -- Return unchanged if not a known placeholder
   return inline
 end


 -- *** NEW: Handler for Code inline elements ***
function Code(inline)
   -- Check if the text content contains our Agda term marker
   -- Allow for optional whitespace around markers
   local marker_match = inline.text:match "^%s*@@AgdaTerm@@(.-)@@%s*$"
   if marker_match then
      local payload = marker_match
      local args = parse_placeholder_args_from_marker(payload) -- Use modified parser
      if args.basename and args['class'] then
          local css_class = "agda-" .. args['class']:lower()
          local attrs
          if type(pandoc.Attr) == "function" then attrs = pandoc.Attr("", {css_class}, {})
          else attrs = {"", {css_class}, {}} end
          -- Return a new Code element with the *correct* basename and attributes
          return pandoc.Code(args.basename, attrs)
      else
         -- If parsing failed, maybe return the original marker text but as plain code?
         print("Warning: Could not parse AgdaTerm marker payload: " .. payload)
         return pandoc.Code(inline.text) -- Fallback: show the marker text
      end
   end
 
   -- If it's not our special marker Code, return it unchanged
   return inline
 end
 