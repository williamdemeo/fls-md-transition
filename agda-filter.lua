-- agda-filter.lua (Version 7 - Simplified for Post-Processing)

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
 
 -- Walk known container environments to process their content by inline filters
 function Div(div)
   if list_contains(div.classes, "NoConway") or
      list_contains(div.classes, "Conway") or
      list_contains(div.classes, "AgdaMultiCode") -- Walk AgdaMultiCode too
   then
      -- Define walkers for elements we might find inside these Divs
      local walkers = { Code = Code, RawInline = RawInline }
      -- Create a dummy block for walking just the content
      local temp_div_for_walking = pandoc.Div(div.content)
      local processed_content = pandoc.walk_block(temp_div_for_walking, walkers).content
      -- Return a new Div containing the processed content, keeping the original attributes/classes
      return pandoc.Div(processed_content, div.attr)
   end
 
   -- Walk other Divs too for safety, in case they contain placeholders
   local walkers = { Code = Code, RawInline = RawInline }
   return pandoc.walk_block(div, walkers)
 end
 
 
 -- Process RawInline elements (mainly for HighlightPlaceholder)
 function RawInline(inline)
   -- Check format exists before matching
   if inline.format and inline.format:match 'latex' then
     -- Check for HighlightPlaceholder using non-greedy match
     local highlight_match = inline.text:match '\\HighlightPlaceholder{(.*)}'
     if highlight_match then
        local content_str = highlight_match
        -- Assume simple text content for now
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
         -- Return original Code element to show the marker text for debugging
         return inline
      end
   end
   -- If it's not our special marker Code, return it unchanged
   return inline
 end
 