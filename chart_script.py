# Create a detailed architecture diagram for the automated knowledge graph generation system
diagram_code = """
flowchart TD
    %% Input Layer
    CSV[CSV Files]
    JSON[JSON Files]  
    TXT[Text Documents]
    DIR[Directory Scanner]
    
    %% Detection Layer
    FTD[File Type Detector]
    SIE[Schema Inference Engine]
    CA[Content Analyzer]
    
    %% Processing Layer
    LDL[LangChain Document Loaders]
    TS[Text Splitter]
    BJC[Batch Job Creator]
    
    %% LLM Layer
    API[OpenAI Batch API]
    SO[Structured Outputs<br/>Pydantic Models]
    KE[Knowledge Extraction]
    
    %% RDF Generation Layer
    EP[Entity Processor]
    RP[Relationship Processor]
    TG[Triple Generator]
    
    %% Output Layer
    RDF[RDF Graph]
    TTL[Turtle Export]
    STATS[Statistics & Metadata]
    
    %% Data Flow Arrows
    CSV --> FTD
    JSON --> FTD
    TXT --> FTD
    DIR --> FTD
    
    FTD --> SIE
    FTD --> CA
    
    SIE --> LDL
    CA --> LDL
    
    LDL --> TS
    TS --> BJC
    
    BJC --> API
    API --> SO
    SO --> KE
    
    KE --> EP
    KE --> RP
    
    EP --> TG
    RP --> TG
    
    TG --> RDF
    RDF --> TTL
    RDF --> STATS
    
    %% Layer Labels
    subgraph INPUT[" INPUT LAYER "]
        CSV
        JSON
        TXT
        DIR
    end
    
    subgraph DETECT[" DETECTION LAYER "]
        FTD
        SIE
        CA
    end
    
    subgraph PROCESS[" PROCESSING LAYER "]
        LDL
        TS
        BJC
    end
    
    subgraph LLM[" LLM LAYER "]
        API
        SO
        KE
    end
    
    subgraph RDFGEN[" RDF GENERATION LAYER "]
        EP
        RP
        TG
    end
    
    subgraph OUTPUT[" OUTPUT LAYER "]
        RDF
        TTL
        STATS
    end
"""

# Create the mermaid diagram with both png and svg outputs
png_path, svg_path = create_mermaid_diagram(
    diagram_code, 
    "knowledge_graph_architecture.png",
    "knowledge_graph_architecture.svg",
    width=1400,
    height=1000
)

print(f"Architecture diagram saved as: {png_path} and {svg_path}")