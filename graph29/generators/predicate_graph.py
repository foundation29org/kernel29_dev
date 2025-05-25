#!/usr/bin/env python3
"""
Predicate Graph Class for graph29 Architecture Visualization

This class manages nodes and edges with consistent naming and coloring
across all sequential prompts for a module.
"""

from typing import Dict, List, Tuple, Set
import json

class PredicateGraph:
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.nodes: Dict[str, Dict] = {}  # node_id -> node_properties
        self.edges: List[Tuple[str, str, str]] = []  # (source_id, predicate, target_id)
        
        # Consistent color mapping
        self.entity_colors = {
            'application_components': {'fill': '#afa', 'stroke': '#3a3'},
            'core_functions': {'fill': '#7d7', 'stroke': '#3a3'},
            'framework_components': {'fill': '#bbf', 'stroke': '#33f'},
            'database_tables': {'fill': '#f9f', 'stroke': '#333'},
            'database_functions': {'fill': '#fbb', 'stroke': '#d33'},
            'data_flow_elements': {'fill': '#f9f9f9', 'stroke': '#999'},
            'command_arguments': {'fill': '#ffd', 'stroke': '#aa3'},
            'selected_components': {'fill': '#ffb', 'stroke': '#b90'},
            'parser_components': {'fill': '#fcf', 'stroke': '#90b'},
        }

    def sanitize_node_id(self, text: str) -> str:
        """Convert text to valid consistent node ID"""
        import re
        # Remove special characters and replace with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it starts with a letter
        if sanitized and sanitized[0].isdigit():
            sanitized = 'n_' + sanitized
        return sanitized or 'unknown_node'

    def classify_entity(self, entity: str) -> str:
        """Classify entity type for consistent coloring"""
        entity_lower = entity.lower()
        
        # Command arguments
        if entity.startswith('--'):
            return 'command_arguments'
        
        # Data contracts (Pydantic)
        if 'pydantic' in entity_lower or 'list of' in entity_lower.replace('_', ' '):
            return 'data_flow_elements'
        
        # Database tables (typically PascalCase)
        if (len(entity) > 0 and entity[0].isupper() and 
            any(keyword in entity_lower for keyword in ['table', 'bench', 'model', 'prompt', 'diagnosis', 'rank'])):
            return 'database_tables'
        
        # Database functions (typically contain 'get_', 'add_', 'insert_')
        if any(prefix in entity_lower for prefix in ['get_', 'add_', 'insert_', 'fetch_']):
            return 'database_functions'
        
        # Core functions (contain parentheses or specific patterns)
        if ('()' in entity or 
            any(func in entity_lower for func in ['set_settings', 'retrieve', 'process_results', 'main_async'])):
            return 'core_functions'
        
        # Framework components (specific known components)
        if any(comp in entity for comp in ['AsyncModelHandler', 'PromptBuilder', 'process_all_batches']):
            return 'framework_components'
        
        # Parser components
        if ('parse' in entity_lower or 
            any(parser in entity_lower for parser in ['parser', 'universal_', 'xml'])):
            return 'parser_components'
        
        # Selected components (Config, Prompt classes)
        if any(suffix in entity for suffix in ['Config', 'Prompt', 'GPT']):
            return 'selected_components'
        
        # Scripts (contain run_, module_name, etc.)
        if any(pattern in entity_lower for pattern in ['run_', f'{self.module_name.lower()}_', '_async', '_sync']):
            return 'application_components'
        
        # Default to data flow elements
        return 'data_flow_elements'

    def add_node(self, entity: str, node_type: str = None) -> str:
        """Add a node with consistent ID and classification"""
        node_id = self.sanitize_node_id(entity)
        
        if node_id not in self.nodes:
            classification = node_type or self.classify_entity(entity)
            colors = self.entity_colors.get(classification, {'fill': '#f9f9f9', 'stroke': '#999'})
            
            self.nodes[node_id] = {
                'id': node_id,
                'label': entity,
                'classification': classification,
                'colors': colors,
                'original_text': entity
            }
        
        return node_id

    def add_edge(self, source: str, predicate: str, target: str):
        """Add an edge between two entities"""
        source_id = self.add_node(source)
        target_id = self.add_node(target)
        
        edge = (source_id, predicate, target_id)
        if edge not in self.edges:
            self.edges.append(edge)

    def get_triplets(self) -> List[Tuple[str, str, str]]:
        """Get all edges as triplets using original entity names"""
        triplets = []
        for source_id, predicate, target_id in self.edges:
            source_label = self.nodes[source_id]['original_text']
            target_label = self.nodes[target_id]['original_text']
            triplets.append((source_label, predicate, target_label))
        return triplets

    def get_nodes_dict(self) -> Dict[str, Dict]:
        """Get nodes dictionary for visualization"""
        return self.nodes.copy()

    def get_edges_list(self) -> List[Tuple[str, str, str]]:
        """Get edges list using node IDs"""
        return self.edges.copy()

    def merge(self, other_graph: 'PredicateGraph'):
        """Merge another graph into this one"""
        # Add all nodes from other graph
        for node_id, node_data in other_graph.nodes.items():
            if node_id not in self.nodes:
                self.nodes[node_id] = node_data
        
        # Add all edges from other graph
        for edge in other_graph.edges:
            if edge not in self.edges:
                self.edges.append(edge)

    def to_json(self) -> str:
        """Export graph to JSON format"""
        return json.dumps({
            'module_name': self.module_name,
            'nodes': self.nodes,
            'edges': self.edges
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'PredicateGraph':
        """Import graph from JSON format"""
        data = json.loads(json_str)
        graph = cls(data['module_name'])
        graph.nodes = data['nodes']
        graph.edges = data['edges']
        return graph


class DxGPTPredicateGraph(PredicateGraph):
    """Specific implementation for dxGPT module"""
    
    def __init__(self):
        super().__init__("dxGPT")
    
    def add_init_flow(self):
        """Add init flow predicates"""
        # Execution Flow
        self.add_edge("run_dxGPT_async.py", "calls", "dxGPT_async.py")
        self.add_edge("dxGPT_async.py", "calls", "main_async")
        self.add_edge("main_async", "calls", "set_settings")
        self.add_edge("main_async", "calls", "retrieve_and_make_prompts")
        self.add_edge("main_async", "calls", "process_results")
        
        # Configuration Generation
        self.add_edge("set_settings", "produces", "session")
        self.add_edge("set_settings", "produces", "handler")
        self.add_edge("set_settings", "produces", "prompt_builder")
        self.add_edge("set_settings", "produces", "model_id")
        self.add_edge("set_settings", "produces", "prompt_id")
        
        # Argument Processing
        self.add_edge("--model_alias", "configures", "set_settings")
        self.add_edge("--prompt_alias", "configures", "set_settings")
        self.add_edge("--hospital", "configures", "retrieve_and_make_prompts")
        self.add_edge("--num_samples", "configures", "retrieve_and_make_prompts")
        self.add_edge("--batch_size", "configures", "process_all_batches")
        self.add_edge("--rpm_limit", "configures", "process_all_batches")
        self.add_edge("--min_batch_interval", "configures", "process_all_batches")
        self.add_edge("--verbose", "configures", "main_async")
        
        # Component Initialization
        self.add_edge("set_settings", "initializes", "AsyncModelHandler")
        self.add_edge("set_settings", "initializes", "PromptBuilder")
        self.add_edge("insert_or_fetch_model", "initializes", "model_id")
        self.add_edge("insert_or_fetch_prompt", "initializes", "prompt_id")
        
        # Data Flow Setup
        self.add_edge("session", "contains", "database_connection")
        self.add_edge("handler", "contains", "api_configuration")
        self.add_edge("prompt_builder", "contains", "prompt_template")
        self.add_edge("model_id", "contains", "model_reference")
        self.add_edge("prompt_id", "contains", "prompt_reference")

    def add_retrieve_flow(self):
        """Add retrieve flow predicates"""
        # Argument Flow
        self.add_edge("--hospital", "filters", "hospital_column")
        self.add_edge("--num_samples", "filters", "get_cases_bench")
        self.add_edge("--model_alias", "filters", "model_id")
        self.add_edge("--prompt_alias", "filters", "prompt_id")
        
        # Database Function Connections
        self.add_edge("get_cases_bench", "connects to", "CasesBench")
        self.add_edge("insert_or_fetch_model", "connects to", "Models")
        self.add_edge("insert_or_fetch_prompt", "connects to", "Prompts")
        
        # JOIN Operations
        self.add_edge("Models", "provides", "model_id")
        self.add_edge("model_id", "filters", "CasesBench")
        self.add_edge("Prompts", "provides", "prompt_id")
        self.add_edge("prompt_id", "filters", "CasesBench")
        
        # Data Contract Generation
        self.add_edge("database_query_results", "abstracted to", "List of Clinical Cases (Pydantic)")
        self.add_edge("dxgpt_serialization.py", "defines", "List of Clinical Cases (Pydantic)")
        self.add_edge("wrap_prompts", "produces", "List of Clinical Cases (Pydantic)")
        
        # Result Columns
        self.add_edge("CasesBench", "returns", "case_id")
        self.add_edge("CasesBench", "returns", "case_text")
        self.add_edge("CasesBench", "returns", "hospital")
        self.add_edge("Models", "returns", "model_name")
        self.add_edge("Prompts", "returns", "prompt_template")

    def add_api_call_flow(self):
        """Add API call flow predicates"""
        # Prompt Module Loading
        self.add_edge("prompts/dxGPT_prompts.py", "loads", "StandardDxGPTPrompt")
        self.add_edge("PromptBuilder", "extends", "StandardDxGPTPrompt")
        self.add_edge("DXGPT_PROMPT_REGISTRY", "contains", "StandardDxGPTPrompt")
        
        # Model Selection
        self.add_edge("models/dxGPT_models.py", "loads", "LlamaThreeEightBConfig")
        self.add_edge("AsyncModelHandler", "selects", "LlamaThreeEightBConfig")
        self.add_edge("handler", "contains", "model_configuration")
        
        # Data Contract Flow
        self.add_edge("List of Clinical Cases (Pydantic)", "augmented to", "List of API Call Results (Pydantic)")
        self.add_edge("LlamaThreeEightBConfig", "produces", "List of API Call Results (Pydantic)")
        self.add_edge("wrap_prompts", "connects to", "PromptBuilder")
        
        # Batch Processing
        self.add_edge("--batch_size", "configures", "process_all_batches")
        self.add_edge("--rpm_limit", "configures", "process_all_batches")
        self.add_edge("--min_batch_interval", "configures", "process_all_batches")
        self.add_edge("process_all_batches", "uses", "PromptBuilder")
        self.add_edge("process_all_batches", "uses", "AsyncModelHandler")
        
        # API Execution
        self.add_edge("process_all_batches", "calls", "AsyncModelHandler")
        self.add_edge("AsyncModelHandler", "produces", "api_responses")
        self.add_edge("api_responses", "stored as", "List of API Call Results (Pydantic)")

    def add_parsers_flow(self):
        """Add parsers flow predicates"""
        # Parser Module Usage
        self.add_edge("process_results", "uses", "parsers/dxGPT_parsers.py")
        self.add_edge("parsers/dxGPT_parsers.py", "contains", "parse_top5_xml")
        self.add_edge("parsers/dxGPT_parsers.py", "contains", "universal_dif_diagnosis_parser")
        self.add_edge("PARSER_DIFFERENTIAL_DIAGNOSES", "loads", "parse_top5_xml")
        self.add_edge("PARSER_DIFFERENTIAL_DIAGNOSES_RANKS", "loads", "universal_dif_diagnosis_parser")
        
        # Data Parsing
        self.add_edge("List of API Call Results (Pydantic)", "passed to", "parse_top5_xml")
        self.add_edge("parse_top5_xml", "extracts", "raw_differential_diagnosis")
        self.add_edge("raw_differential_diagnosis", "passed to", "universal_dif_diagnosis_parser")
        self.add_edge("universal_dif_diagnosis_parser", "extracts", "rank_position")
        self.add_edge("universal_dif_diagnosis_parser", "extracts", "disease_name")
        self.add_edge("universal_dif_diagnosis_parser", "extracts", "reasoning")
        
        # Data Contract Progression
        self.add_edge("List of API Call Results (Pydantic)", "augmented to", "List of Clinical Cases w/ DDx (Pydantic)")
        self.add_edge("List of Clinical Cases w/ DDx (Pydantic)", "augmented to", "List of Clinical Cases w/ DDx and Ranks (Pydantic)")
        
        # Database Operations
        self.add_edge("queries/dxGPT_queries.py", "contains", "add_batch_differential_diagnoses")
        self.add_edge("queries/dxGPT_queries.py", "contains", "add_differential_diagnosis_to_rank")
        self.add_edge("List of Clinical Cases w/ DDx (Pydantic)", "sent to", "add_batch_differential_diagnoses")
        self.add_edge("List of Clinical Cases w/ DDx and Ranks (Pydantic)", "sent to", "add_differential_diagnosis_to_rank")
        self.add_edge("add_batch_differential_diagnoses", "writes to", "LlmDifferentialDiagnosis")
        self.add_edge("add_differential_diagnosis_to_rank", "writes to", "DifferentialDiagnosis2Rank")
        self.add_edge("add_batch_differential_diagnoses", "generates", "differential_diagnosis_id")
        
        # Element Storage
        self.add_edge("rank_position", "stored in", "List of Clinical Cases w/ DDx and Ranks (Pydantic)")
        self.add_edge("disease_name", "stored in", "List of Clinical Cases w/ DDx and Ranks (Pydantic)")
        self.add_edge("reasoning", "stored in", "List of Clinical Cases w/ DDx and Ranks (Pydantic)")
        self.add_edge("differential_diagnosis_id", "part of", "DifferentialDiagnosis2Rank")

    def build_complete_graph(self) -> 'PredicateGraph':
        """Build the complete graph with all flows"""
        complete_graph = DxGPTPredicateGraph()
        complete_graph.add_init_flow()
        complete_graph.add_retrieve_flow()
        complete_graph.add_api_call_flow()
        complete_graph.add_parsers_flow()
        return complete_graph

    def build_init_graph(self) -> 'PredicateGraph':
        """Build graph with only init flow"""
        graph = DxGPTPredicateGraph()
        graph.add_init_flow()
        return graph

    def build_retrieve_graph(self) -> 'PredicateGraph':
        """Build graph with only retrieve flow"""
        graph = DxGPTPredicateGraph()
        graph.add_retrieve_flow()
        return graph

    def build_api_call_graph(self) -> 'PredicateGraph':
        """Build graph with only API call flow"""
        graph = DxGPTPredicateGraph()
        graph.add_api_call_flow()
        return graph

    def build_parsers_graph(self) -> 'PredicateGraph':
        """Build graph with only parsers flow"""
        graph = DxGPTPredicateGraph()
        graph.add_parsers_flow()
        return graph


if __name__ == "__main__":
    # Example usage
    dxgpt = DxGPTPredicateGraph()
    
    # Build individual graphs
    init_graph = dxgpt.build_init_graph()
    retrieve_graph = dxgpt.build_retrieve_graph()
    api_call_graph = dxgpt.build_api_call_graph()
    parsers_graph = dxgpt.build_parsers_graph()
    
    # Build complete graph
    complete_graph = dxgpt.build_complete_graph()
    
    print(f"Complete graph has {len(complete_graph.nodes)} nodes and {len(complete_graph.edges)} edges")
    print(f"Init graph has {len(init_graph.nodes)} nodes and {len(init_graph.edges)} edges") 