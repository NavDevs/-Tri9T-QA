import fitz
import pdfplumber
import re
import hashlib

def compute_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def fix_ligatures(text):
    # Fix common ligatures found in the document
    text = text.replace('ﬁ', 'fi')
    text = text.replace('ﬀ', 'ff')
    return text

def parse_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    
    # We will collect lines, grouping spans.
    raw_lines = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    line_text = ""
                    is_bold = False
                    max_size = 0
                    for s in l["spans"]:
                        span_text = s["text"].strip()
                        if not span_text:
                            continue
                        # If a span is just a hyphen, it shouldn't introduce a space if it's splitting a word
                        # But get_text("dict") splits on spans. We'll just concatenate them if there's no space in the original PDF.
                        # For simplicity, we just concatenate spans in a line with a space, UNLESS the previous ends with or current starts with a hyphen
                        if line_text and not line_text.endswith('-') and not span_text.startswith('-'):
                            if not (line_text.endswith('CT') and span_text == '‑'): # specific hack for the weird hyphen
                                line_text += " "
                        
                        span_text = span_text.replace('‑', '-') # normalize the weird hyphen
                        line_text += span_text
                        
                        if "Bold" in s["font"]:
                            is_bold = True
                        if s["size"] > max_size:
                            max_size = s["size"]
                            
                    line_text = fix_ligatures(line_text).strip()
                    if line_text:
                        raw_lines.append({
                            "text": line_text,
                            "bold": is_bold,
                            "size": round(max_size, 1),
                            "page": page_num + 1
                        })
    
    # Now build the tree
    nodes = []
    current_node = None
    node_stack = [] # tuples of (level, node)
    
    heading_pattern = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$')
    
    with pdfplumber.open(pdf_path) as pdf:
        tables_by_page = {}
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                tables_by_page[i + 1] = tables

    current_page = 1
    def flush_tables_for_page(page_num, node):
        if node and page_num in tables_by_page:
            for table in tables_by_page[page_num]:
                # Format table as simple markdown
                md_table = "\n\n"
                for row in table:
                    clean_row = [str(cell).replace('\n', ' ') if cell is not None else "" for cell in row]
                    md_table += "| " + " | ".join(clean_row) + " |\n"
                md_table += "\n"
                if node["body_text"]:
                    node["body_text"] += md_table
                else:
                    node["body_text"] = md_table.strip()
            del tables_by_page[page_num]

    for i, line in enumerate(raw_lines):
        # If we moved to a new page, flush tables from the previous page
        if line["page"] > current_page:
            flush_tables_for_page(current_page, current_node)
            current_page = line["page"]
            
        text = line["text"]
        match = heading_pattern.match(text)
        
        is_heading = False
        if match and line["bold"]:
            # It's a heading
            num_str = match.group(1)
            title = match.group(2)
            level = len(num_str.split('.'))
            
            # The title 'CardioTrack CT-200 Home Blood...' is not a numbered heading, so it won't match.
            is_heading = True
            
            new_node = {
                "heading": text,
                "level": level,
                "body_text": "",
                "children": [],
                "logical_node_id": f"{num_str}::{title.lower().replace(' ', '-')}"
            }
            
            if not nodes and level == 1:
                nodes.append(new_node)
                node_stack = [(level, new_node)]
                current_node = new_node
            else:
                # Find parent
                while node_stack and node_stack[-1][0] >= level:
                    node_stack.pop()
                    
                if node_stack:
                    node_stack[-1][1]["children"].append(new_node)
                else:
                    nodes.append(new_node)
                
                node_stack.append((level, new_node))
                current_node = new_node
                
        if not is_heading:
            if current_node:
                if current_node["body_text"]:
                    current_node["body_text"] += " " + text
                else:
                    current_node["body_text"] = text

    # Flush tables for the final page
    flush_tables_for_page(current_page, current_node)
    
    # Hash content
    def hash_tree(node_list):
        for n in node_list:
            n["content_hash"] = compute_hash(n["body_text"])
            hash_tree(n["children"])
            
    hash_tree(nodes)
    
    return nodes
