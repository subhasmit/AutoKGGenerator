# Create a comprehensive flowchart for knowledge graph generation pipeline
diagram_code = """
flowchart LR
    %% Input Sources
    subgraph Input ["📥 Input Sources"]
        CSV["📊 CSV Files"]
        JSON["📋 JSON Files"] 
        TXT["📄 Text Documents"]
    end
    
    %% Data Processing Layer
    subgraph DataProc ["🔧 Data Processing Layer"]
        PREP["⚙️ Data Preprocessing"]
        SCHEMA["🗂️ Schema Detection"]
        ENTITY["🏷️ Entity Recognition"]
    end
    
    %% LLM Processing Layer
    subgraph LLM ["🤖 LLM Processing Layer"]
        EXTRACT["📤 Entity Extraction"]
        RELATION["🔗 Relationship ID"]
        ONTOLOGY["🗺️ Ontology Mapping"]
    end
    
    %% Knowledge Graph Construction
    subgraph KGConst ["🏗️ Knowledge Graph Construction"]
        TRIPLE["⚡ Triple Generation"]
        ASSEMBLY["🔗 Graph Assembly"]
        VALID["✅ Validation"]
    end
    
    %% Output Formats
    subgraph Output ["📤 Output Formats"]
        RDF["🐢 RDF Turtle Files"]
        SPARQL["⚡ SPARQL Endpoints"]
        GRAPHDB["🗄️ Graph Database"]
    end
    
    %% Flow connections
    CSV --> PREP
    JSON --> PREP
    TXT --> PREP
    
    PREP --> SCHEMA
    SCHEMA --> ENTITY
    
    ENTITY --> EXTRACT
    EXTRACT --> RELATION
    RELATION --> ONTOLOGY
    
    ONTOLOGY --> TRIPLE
    TRIPLE --> ASSEMBLY
    ASSEMBLY --> VALID
    
    VALID --> RDF
    VALID --> SPARQL
    VALID --> GRAPHDB
    
    %% Styling for different layers
    classDef inputStyle fill:#B3E5EC,stroke:#1FB8CD,stroke-width:2px
    classDef dataStyle fill:#A5D6A7,stroke:#2E8B57,stroke-width:2px
    classDef llmStyle fill:#FFEB8A,stroke:#D2BA4C,stroke-width:2px
    classDef kgStyle fill:#FFCDD2,stroke:#DB4545,stroke-width:2px
    classDef outputStyle fill:#9FA8B0,stroke:#5D878F,stroke-width:2px
    
    class CSV,JSON,TXT inputStyle
    class PREP,SCHEMA,ENTITY dataStyle
    class EXTRACT,RELATION,ONTOLOGY llmStyle
    class TRIPLE,ASSEMBLY,VALID kgStyle
    class RDF,SPARQL,GRAPHDB outputStyle
"""

# Create the mermaid diagram
create_mermaid_diagram(diagram_code, "knowledge_graph_pipeline.png", "knowledge_graph_pipeline.svg")

print("Knowledge graph generation pipeline flowchart created successfully!")