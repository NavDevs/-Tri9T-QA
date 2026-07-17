from tinydb import TinyDB, Query

db = TinyDB('generations.json')
generations_table = db.table('generations')

def insert_generation(data: dict) -> int:
    return generations_table.insert(data)

def get_generation_by_id(gen_id: int):
    return generations_table.get(doc_id=gen_id)

def get_generations_by_selection(selection_id: int):
    Gen = Query()
    return generations_table.search(Gen.selection_id == selection_id)

def get_generations_by_node(node_id: int):
    Gen = Query()
    # TinyDB 'any' can check if any item in a list matches the fragment
    def test_node_id(source_node_hashes):
        return any(n.get('node_id') == node_id for n in source_node_hashes)
        
    return generations_table.search(Gen.source_node_hashes.test(test_node_id))
