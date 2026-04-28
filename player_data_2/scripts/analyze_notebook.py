import json

with open('data_exploration_executed.ipynb', 'r') as f:
    notebook = json.load(f)

print('=== NOTEBOOK EXECUTION SUMMARY ===')
print(f'Total cells: {len(notebook["cells"])}')
print()

errors = []
executed_cells = 0
error_cells = 0

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        exec_count = cell.get('execution_count', None)
        
        if exec_count is not None:
            executed_cells += 1
            status = "✓ Executed"
        else:
            status = "✗ Not executed"
        
        # Check for errors
        has_error = False
        for output in cell.get('outputs', []):
            if output.get('output_type') == 'error':
                error_cells += 1
                has_error = True
                errors.append({
                    'cell': idx,
                    'ename': output.get('ename', 'Unknown'),
                    'evalue': output.get('evalue', '')
                })

print(f'Code cells executed: {executed_cells}')
print(f'Code cells with errors: {error_cells}')
print()

if errors:
    print('=== ERRORS ENCOUNTERED ===')
    for err in errors:
        print(f'Cell {err["cell"]}: {err["ename"]} - {err["evalue"]}')
else:
    print('✓ No errors found in executed cells')
