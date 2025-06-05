# mobile_developer_crew/test_designer.py
import json

class TestDesigner:
    def __init__(self, agent_name: str, llm_invoker_function, tools_provider=None):
        self.agent_name = agent_name # Should be "test_designer"
        self.llm_invoker_function = llm_invoker_function
        self.tools_provider = tools_provider
        # print(f"Initialized {self.agent_name}")

    def run(self, tech_stack_mobile: str, ui_structure_json_str: str, component_designs_str: str, api_specifications_str: str = None) -> dict:
        print(f"[{self.agent_name}] Running. Tech stack: {tech_stack_mobile}, UI Structure: {ui_structure_json_str[:50]}..., "
              f"Component Designs: {component_designs_str[:50]}..., API Specs: {str(api_specifications_str)[:50]}...")

        prompt_input_data = {
            "tech_stack_mobile": tech_stack_mobile,
            "ui_structure_json": ui_structure_json_str,
            "component_designs": component_designs_str,
            "api_specifications": api_specifications_str if api_specifications_str else "{}" # Ensure it's a valid JSON string if None
        }

        print(f"[{self.agent_name}] Simulating LLM call with prompt_input_data: {prompt_input_data}")
        # In a real scenario:
        # response = self.llm_invoker_function(
        #     agent_name=self.agent_name,
        #     prompt_input_data=prompt_input_data
        # )
        # simulated_llm_output = response
        simulated_llm_output = {
            "status": "success",
            "data": "// Simulated test scripts\ndescribe('Login', () => {});"
        }

        return {
            "status": simulated_llm_output["status"],
            "test_scripts": simulated_llm_output.get("data"),
            "message": f"Simulated output from {self.agent_name}"
        }
