import sys
print(f'Python sys.path: {sys.path}')
print('Attempting to import agents...')
error_messages = []
try:
    from agents import ProjectAnalyzer
    print('Successfully imported ProjectAnalyzer')
except ImportError as e:
    error_messages.append(f'Failed to import ProjectAnalyzer: {e}')

try:
    from agents import APIDesigner
    print('Successfully imported APIDesigner')
except ImportError as e:
    error_messages.append(f'Failed to import APIDesigner: {e}')

# Attempt to import other agents that are expected to be missing
expected_missing_agents = [
    'Planner', 'Architect', 'CodeWriter',
    'FrontendBuilder', 'MobileDeveloper', 'Tester', 'Debugger'
]
for agent_name in expected_missing_agents:
    try:
        # Dynamically try to import each agent
        module = __import__('agents', fromlist=[agent_name])
        getattr(module, agent_name)
        # This line should ideally not be reached for these agents
        error_messages.append(f'WARNING: Successfully imported {agent_name}, but it was expected to be missing.')
    except ImportError:
        print(f'{agent_name} is not importable (as expected for now).')
    except AttributeError:
        print(f'{agent_name} is not importable (AttributeError - as expected for now).')


if error_messages:
    print('\n--- Import Errors/Warnings ---')
    for msg in error_messages:
        print(msg)
    # Exit with error code if critical imports failed
    if any('ProjectAnalyzer' in msg for msg in error_messages if 'Failed' in msg) or \
       any('APIDesigner' in msg for msg in error_messages if 'Failed' in msg):
        sys.exit(1)
else:
    print('\nAll critical agents (ProjectAnalyzer, APIDesigner) imported successfully.')
    print('Other agents correctly reported as not importable at this stage.')
