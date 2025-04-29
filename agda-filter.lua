-- Initial draft for agda-filter.lua (handling code blocks)

local stringify = require('pandoc.utils').stringify -- Useful for getting plain text content

-- Function to check if a code block has the '[hide]' option
-- NOTE: This function needs refinement based on how Pandoc actually parses \begin{code}[hide]
local function is_hidden_code(block_or_div)
  -- Pandoc often parses environments like \begin{foo}[opt]{arg} into Divs
  -- with classes 'foo' and attributes/data for opts/args, containing the content.
  -- Let's check if the element passed is a Div that might represent the 'code' environment.

  if block_or_div.t == "Div" then
     -- Check if this Div represents our code environment (maybe class 'code'?)
     -- and if it has an attribute or class indicating 'hide'.
     -- This structure depends heavily on how Pandoc's LaTeX reader handles \begin{code}.
     -- Example check:
     -- if block_or_div.classes and pandoc.utils.list_contains(block_or_div.classes, 'code') then
     --   if block_or_div.attributes and block_or_div.attributes['hide'] then return true end
     --   if pandoc.utils.list_contains(block_or_div.classes, 'hide') then return true end -- Alternative
     -- end
  elseif block_or_div.t == "CodeBlock" then
     -- Less likely for environments with options, but maybe check attributes here too?
     -- if block_or_div.attributes and block_or_div.attributes['hide'] then return true end
  elseif block_or_div.t == "RawBlock" and block_or_div.format == "latex" then
     -- Fallback: Check raw LaTeX if Pandoc didn't parse it structuredly
     if string.match(block_or_div.text, "^\\begin{code}%[hide%]") then
        -- We'd need more logic here to extract the content properly
        -- This indicates a potential issue with Pandoc parsing this env
        return true -- Mark as hidden, but processing needs work
     end
  end

  -- *** This function is HIGHLY DEPENDENT on Pandoc's LaTeX parsing output ***
  -- *** We MUST inspect Pandoc's AST output first (native or json) ***

  return false -- Default to not hidden
end

-- Process Div elements first, in case Pandoc wraps code environments in Divs
function Div(div)
  -- Check if this Div represents a code block that should be hidden
  if is_hidden_code(div) then
     -- Assuming the Div contains a single CodeBlock (or list of blocks)
     local content_blocks = div.content

     -- Find the actual CodeBlock(s) inside
     local code_blocks = {}
     for _, element in ipairs(content_blocks) do
        if element.t == "CodeBlock" then
           -- Ensure it has 'agda' class
           element.classes = element.classes or {}
           if not pandoc.utils.list_contains(element.classes, 'agda') then
              table.insert(element.classes, 1, 'agda')
           end
           table.insert(code_blocks, element)
        end
     end

     if #code_blocks > 0 then
        -- Wrap the extracted code blocks in <details> HTML
        local summary_text = pandoc.RawInline('html', '<summary>View Hidden Code</summary>')
        local opening_tag = pandoc.RawBlock('html', '<details class="hidden-code">')
        local summary_para = pandoc.Para({summary_text})
        local closing_tag = pandoc.RawBlock('html', '</details>')

        -- Construct the list of blocks to return
        local result_blocks = { opening_tag, summary_para }
        for _, cb in ipairs(code_blocks) do
            -- Convert code block to raw HTML pre/code for simplicity within details
            -- (Or pass AST through if md_in_html extension works well)
            local code_content = cb.text
            local html_code_block = pandoc.RawBlock('html',
              '<div class="highlight"><pre><code class="language-agda">' .. pandoc.utils.html_escape(code_content) .. '</code></pre></div>'
            )
           table.insert(result_blocks, html_code_block)
        end
        table.insert(result_blocks, closing_tag)
        return result_blocks -- Return list of blocks replacing the Div
     end
  end
  -- If not a hidden code Div, return it unchanged for further processing (e.g., CodeBlock function below)
  return div
end


-- Process CodeBlock elements (might be called after Div processing)
function CodeBlock(block)
  -- Ensure it has the 'agda' class for syntax highlighting
  local has_agda_class = false
  if block.classes then
    for _, class in ipairs(block.classes) do
      if class == 'agda' then
        has_agda_class = true
        break
      end
    end
  else
    block.classes = {} -- Initialize classes if nil
  end

  if not has_agda_class then
    table.insert(block.classes, 1, 'agda') -- Add 'agda' class if not present
  end

  -- If it wasn't handled by the Div function (e.g., regular \begin{code} parsed directly as CodeBlock)
  -- return it as is (with potentially added 'agda' class)
  return block
end

-- Add placeholders for other functions we'll need later
-- function Inline(el) ... end
-- function Para(el) ... end -- For \modulenote maybe
-- function Str(el) ... end
