-- Keep long code identifiers within table cells.
function Code(element)
  local text = element.text
  if text:match("^[0-9a-f]+$") and #text >= 40 then
    local chunks = {}
    for index = 1, #text, 8 do
      table.insert(chunks, text:sub(index, index + 7))
    end
    return pandoc.RawInline("latex", "\\texttt{" .. table.concat(chunks, "\\allowbreak{}") .. "}")
  end
  return pandoc.RawInline("latex", "\\nolinkurl{" .. text .. "}")
end

function Header(element)
  local text = pandoc.utils.stringify(element.content)
  if text:match("Current handover") or text:match("Portable evaluator replay") then
    return {pandoc.RawBlock("latex", "\\Needspace{250pt}"), element}
  end
end
