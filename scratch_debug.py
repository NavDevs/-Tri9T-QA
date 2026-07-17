from app.parser import parse_pdf
import json

nodes = parse_pdf("data/ct200_manual.pdf")
def print_tree(nodes, indent=0):
    for n in nodes:
        print("  " * indent + n["heading"])
        print_tree(n["children"], indent + 1)

print_tree(nodes)
