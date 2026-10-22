"""Write plain light/dark copies of a theme-aware SVG (CSS variables resolved, fixed background)."""
import re, sys
src = sys.argv[1]
s = open(src).read()
light = dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]+)', re.search(r'svg \{ (--.*?) \}', s, re.S).group(1)))
dark_block = re.search(r'@media \(prefers-color-scheme: dark\) \{\s*svg \{ (--.*?) \}', s, re.S).group(1)
dark = {**light, **dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]+)', dark_block))}
base = re.sub(r'\n    @media \(prefers-color-scheme: dark\) \{.*?\n    \}', '', s, flags=re.S)
base = re.sub(r'    svg \{ --.*?\}\n', '', base, flags=re.S)
for name, pal, bg in (("light", light, "#ffffff"), ("dark", dark, "#161514")):
    out = re.sub(r'var\((--[\w-]+)\)', lambda m: pal[m.group(1)], base)
    out = out.replace('<svg xmlns', f'<svg style="background:{bg}" xmlns', 1)
    out = out.replace('</defs>', f'</defs>\n  <rect width="100%" height="100%" fill="{bg}"/>', 1)
    open(src.replace('.svg', f'-{name}.svg'), 'w').write(out)
    print("wrote", src.replace('.svg', f'-{name}.svg'), "| vars left:", out.count('var('))
