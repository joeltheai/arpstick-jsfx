#!/usr/bin/env python3
"""Render actual JSFX draw calls through EEL2 into an SVG for layout inspection.
Font metrics are approximated; REAPER remains the final authority for rendering.
"""
import argparse
import html
import subprocess
from pathlib import Path
from validate import preprocess, PLUGIN

WRAPPERS = '''
function trace_rect(x,y,w,h) (printf("RECT %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f\\n",x,y,w,h,gfx_r,gfx_g,gfx_b,gfx_a););
function trace_line(x,y,x2,y2,aa) (printf("LINE %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f\\n",x,y,x2,y2,gfx_r,gfx_g,gfx_b,gfx_a););
function trace_circle(x,y,r,fill,aa) (printf("CIRCLE %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f\\n",x,y,r,fill,gfx_r,gfx_g,gfx_b,gfx_a););
function trace_font(i,font,size) (trace_size=size;);
function trace_measure(s,w,h) (w=strlen(s)*trace_size*0.54; h=trace_size;);
function trace_text(fmt,s) (printf("TEXT %.3f %.3f %.3f %.3f %.3f %.3f %s\\n",gfx_x,gfx_y,trace_size,gfx_r,gfx_g,gfx_b,s););
'''

def render(binary, output, lane=0):
    code = preprocess(PLUGIN.read_text())
    for name in ('rect','line','circle','setfont','measurestr','printf'):
        target={'setfont':'font','measurestr':'measure','printf':'text'}.get(name,name)
        code=code.replace('gfx_'+name+'(', 'trace_'+target+'(')
    # EEL helpers have fixed argument counts; gfx_line's optional AA defaults to 1.
    import re
    code=re.sub(r'trace_line\(([^;\n]+)\)',lambda m:'trace_line('+m[1]+(',1' if m[1].count(',')==3 else '')+')',code)
    code=code.replace('trace_measure(s, w, h);','w=strlen(s)*trace_size*0.54; h=trace_size;')
    code=WRAPPERS+code+f'\ngfx_w=1152; gfx_h=768; curGraph={lane}; mouse_x=-1; mouse_y=-1; __gfx();\n'
    import tempfile
    with tempfile.NamedTemporaryFile('w',suffix='.eel') as f:
        f.write(code);f.flush()
        result=subprocess.run([binary,f.name],capture_output=True,text=True,check=True)
    if 'syntax error' in result.stderr or 'syntax error' in result.stdout:
        raise RuntimeError(result.stdout+result.stderr)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1152" height="768" viewBox="0 0 1152 768">']
    def color(vals):return 'rgb('+','.join(str(round(max(0,min(1,float(x)))*255)) for x in vals)+')'
    for line in result.stdout.splitlines():
        parts=line.split(' ')
        if parts[0] in ('RECT','LINE','CIRCLE'):
            v=list(map(float,parts[1:])); paint=color(v[4:7]); opacity=v[7]
            if parts[0]=='RECT':svg.append(f'<rect x="{v[0]}" y="{v[1]}" width="{max(0,v[2])}" height="{max(0,v[3])}" fill="{paint}" opacity="{opacity}"/>')
            if parts[0]=='LINE':svg.append(f'<path d="M{v[0]},{v[1]} L{v[2]},{v[3]}" stroke="{paint}" opacity="{opacity}"/>')
            if parts[0]=='CIRCLE':svg.append(f'<circle cx="{v[0]}" cy="{v[1]}" r="{v[2]}" fill="{paint if v[3] else "none"}" stroke="{paint}"/>')
        elif parts[0]=='TEXT':
            v=list(map(float,parts[1:7])); text=' '.join(parts[7:])
            svg.append(f'<text x="{v[0]}" y="{v[1]+v[2]*0.85}" font-family="Arial,sans-serif" font-size="{v[2]}" fill="{color(v[3:6])}">{html.escape(text)}</text>')
    svg.append('</svg>'); Path(output).write_text('\n'.join(svg))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('binary');ap.add_argument('output');ap.add_argument('--lane',type=int,default=0);a=ap.parse_args();render(a.binary,a.output,a.lane)
