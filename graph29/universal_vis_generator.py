#!/usr/bin/env python3
"""
Universal Vis.js Generator for Graph29 Architecture Visualizations
Reads specified vis.js file and generates standalone HTML visualization
Enhanced with navigation, multiline support, and advanced physics controls
"""

import os
from pathlib import Path
import re
import sys

# =================================================
# CONFIGURATION: Select which vis.js file to use
# =================================================

# Uncomment ONE of the following lines to select the visualization:
file_input = "unified_complete_vis.js"
# file_input = "dxGPT_complete_vis.js" 
# file_input = "judge_semantic_async_complete_vis.js"
# file_input = "judge_severity_async_complete_vis.js"

def read_vis_js_file(filename: str) -> str:
    """Read the specified vis.js file from vis_output directory"""
    vis_output_dir = Path(__file__).parent / "vis_output"
    vis_file_path = vis_output_dir / filename
    
    if not vis_file_path.exists():
        raise FileNotFoundError(f"Vis.js file not found: {vis_file_path}")
    
    with open(vis_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix multiline issue by converting <br/> tags to \n characters
    # This matches the original working implementation
    content = content.replace('<br/>', '\\n')
    
    return content

def generate_standalone_html(vis_js_content: str, title: str) -> str:
    """Generate standalone HTML with embedded vis.js visualization"""
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
        }}
        
        .header h1 {{
            color: #333;
            margin: 0;
            font-size: 2em;
        }}
        
        .header p {{
            color: #666;
            margin: 5px 0;
            font-size: 14px;
        }}
        
        .controls-panel {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .control-section {{
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }}
        
        .control-section h3 {{
            margin: 0 0 15px 0;
            color: #333;
            font-size: 1.1em;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }}
        
        .control-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .control-row:last-child {{
            margin-bottom: 0;
        }}
        
        .control-row label {{
            font-weight: bold;
            color: #555;
            min-width: 120px;
        }}
        
        .control-row input[type="range"] {{
            flex: 1;
            margin: 0 10px;
        }}
        
        .control-row input[type="number"] {{
            width: 60px;
            padding: 2px 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }}
        
        .control-row select, .control-row button {{
            padding: 5px 10px;
            border: 1px solid #ccc;
            border-radius: 3px;
            background-color: white;
            min-width: 100px;
        }}
        
        .control-row button {{
            background-color: #007bff;
            color: white;
            cursor: pointer;
            border: none;
        }}
        
        .control-row button:hover {{
            background-color: #0056b3;
        }}
        
        .control-row button.active {{
            background-color: #28a745;
        }}
        
        .navigation-controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }}
        
        .navigation-controls button {{
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 3px;
            background-color: #f8f9fa;
            cursor: pointer;
        }}
        
        .navigation-controls button:hover {{
            background-color: #e9ecef;
        }}
        
        .network-container {{
            width: 100%;
            height: 70vh;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #fafafa;
            position: relative;
        }}
        
        .zoom-controls {{
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 1000;
        }}
        
        .zoom-controls button {{
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.9);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
        }}
        
        .zoom-controls button:hover {{
            background-color: rgba(240, 240, 240, 0.9);
        }}
        
        .physics-status {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 5px 10px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-size: 12px;
            z-index: 1000;
        }}
        
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }}
        
        .legend h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        
        .legend-items {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 2px solid #333;
        }}
        
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        .stats {{
            margin-top: 10px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .controls-panel {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Enhanced Interactive Architecture Visualization with Navigation & Physics Controls</p>
            <p>Generated with Universal Vis.js Generator</p>
        </div>
        
        <div class="controls-panel">
            <div class="control-section">
                <h3>🎮 Navigation & Layout</h3>
                <div class="navigation-controls">
                    <button onclick="fitNetwork()">📐 Fit Screen</button>
                    <button onclick="resetZoom()">🔍 Reset Zoom</button>
                    <button onclick="centerNetwork()">🎯 Center</button>
                    <button onclick="togglePhysics()" id="physics-toggle">⚡ Physics ON</button>
                </div>
                <div class="control-row">
                    <label for="layout-select">Layout Type:</label>
                    <select id="layout-select">
                        <option value="forceAtlas2Based">Force Atlas 2</option>
                        <option value="barnesHut">Barnes Hut</option>
                        <option value="repulsion">Repulsion</option>
                        <option value="hierarchicalUD">Hierarchical ↕</option>
                        <option value="hierarchicalLR">Hierarchical ↔</option>
                    </select>
                </div>
                <div class="control-row">
                    <label for="solver-select">Physics Solver:</label>
                    <select id="solver-select">
                        <option value="forceAtlas2Based">Force Atlas 2</option>
                        <option value="barnesHut">Barnes Hut</option>
                        <option value="repulsion">Repulsion</option>
                        <option value="hierarchicalRepulsion">Hierarchical</option>
                    </select>
                </div>
            </div>

            <div class="control-section">
                <h3>⚙️ Physics Parameters</h3>
                <div class="control-row">
                    <label for="gravity-slider">Central Gravity:</label>
                    <input type="range" id="gravity-slider" min="0" max="2" step="0.1" value="0.3">
                    <input type="number" id="gravity-value" min="0" max="2" step="0.1" value="0.3">
                </div>
                <div class="control-row">
                    <label for="spring-length-slider">Spring Length:</label>
                    <input type="range" id="spring-length-slider" min="50" max="500" step="10" value="100">
                    <input type="number" id="spring-length-value" min="50" max="500" step="10" value="100">
                </div>
                <div class="control-row">
                    <label for="spring-constant-slider">Spring Strength:</label>
                    <input type="range" id="spring-constant-slider" min="0.01" max="0.5" step="0.01" value="0.08">
                    <input type="number" id="spring-constant-value" min="0.01" max="0.5" step="0.01" value="0.08">
                </div>
                <div class="control-row">
                    <label for="node-distance-slider">Node Distance:</label>
                    <input type="range" id="node-distance-slider" min="50" max="300" step="10" value="120">
                    <input type="number" id="node-distance-value" min="50" max="300" step="10" value="120">
                </div>
                <div class="control-row">
                    <label for="damping-slider">Damping:</label>
                    <input type="range" id="damping-slider" min="0.01" max="0.99" step="0.01" value="0.09">
                    <input type="number" id="damping-value" min="0.01" max="0.99" step="0.01" value="0.09">
                </div>
            </div>
        </div>
        
        <div class="network-container">
            <div id="network" style="width: 100%; height: 100%;"></div>
            <div class="zoom-controls">
                <button onclick="zoomIn()" title="Zoom In">+</button>
                <button onclick="zoomOut()" title="Zoom Out">−</button>
                <button onclick="fitNetwork()" title="Fit to Screen">⌂</button>
            </div>
            <div class="physics-status" id="physics-status">
                Physics: <span id="physics-state">Enabled</span> | 
                Navigation: <span id="nav-state">Enabled</span>
            </div>
        </div>
        
        <div class="legend">
            <h3>Entity Types</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #afa; border-color: #3a3;"></div>
                    <span>Application Components</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #7d7; border-color: #3a3;"></div>
                    <span>Core Functions</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #bbf; border-color: #33f;"></div>
                    <span>Framework Components</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f9f; border-color: #333;"></div>
                    <span>Database Tables</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #fbb; border-color: #d33;"></div>
                    <span>Database Functions</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f9f9f9; border-color: #999;"></div>
                    <span>Data Flow Elements</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #ffd; border-color: #aa3;"></div>
                    <span>Command Arguments</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #ffb; border-color: #b90;"></div>
                    <span>Selected Components</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Interactive network diagram with navigation controls | 
            Use arrow keys to navigate, +/- to zoom | 
            Mouse: drag nodes, pan view, scroll zoom | 
            Adjust physics parameters in real-time</p>
        </div>
    </div>

    <script>
        // Data from vis.js file
        {vis_js_content}
        
        // Network container
        const container = document.getElementById('network');
        
        // Initial network options with navigation and multiline support
        const options = {{
            physics: {{
                enabled: true,
                forceAtlas2Based: {{
                    theta: 0.5,
                    gravitationalConstant: -50,
                    centralGravity: 0.3,
                    springConstant: 0.08,
                    springLength: 100,
                    damping: 0.09,
                    avoidOverlap: 0.1
                }},
                maxVelocity: 50,
                minVelocity: 0.1,
                solver: 'forceAtlas2Based',
                stabilization: {{
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 25
                }}
            }},
            layout: {{
                randomSeed: 2
            }},
            interaction: {{
                dragNodes: true,
                dragView: true,
                zoomView: true,
                selectConnectedEdges: true,
                hover: true,
                hoverConnectedEdges: true,
                tooltipDelay: 300,
                navigationButtons: true,  // Enable navigation buttons
                keyboard: {{
                    enabled: true,
                    speed: {{x: 10, y: 10, zoom: 0.02}},
                    bindToWindow: false
                }}
            }},
            nodes: {{
                borderWidth: 2,
                shadow: {{
                    enabled: true,
                    color: 'rgba(0,0,0,0.2)',
                    size: 5,
                    x: 2,
                    y: 2
                }},
                font: {{
                    size: 12,
                    color: '#000000'
                }},
                chosen: {{
                    node: true,
                    label: true
                }}
            }},
            edges: {{
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                shadow: {{
                    enabled: true,
                    color: 'rgba(0,0,0,0.1)',
                    size: 2,
                    x: 1,
                    y: 1
                }},
                smooth: {{
                    type: 'continuous',
                    forceDirection: 'none',
                    roundness: 0.5
                }},
                color: {{
                    color: '#848484',
                    highlight: '#ff0000',
                    hover: '#ff8800'
                }},
                font: {{
                    size: 8,
                    face: 'Arial'
                }}
            }}
        }};
        
        // Create network
        const network = new vis.Network(container, {{nodes: nodes, edges: edges}}, options);
        let physicsEnabled = true;
        
        // Event handlers
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                console.log('Clicked node:', node);
            }}
        }});

        network.on('hoverNode', function(params) {{
            container.style.cursor = 'pointer';
        }});

        network.on('blurNode', function(params) {{
            container.style.cursor = 'grab';
        }});

        network.on('dragStart', function(params) {{
            container.style.cursor = 'grabbing';
        }});

        network.on('dragEnd', function(params) {{
            container.style.cursor = 'grab';
        }});
        
        // Control functions
        function fitNetwork() {{
            network.fit({{
                animation: {{
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }}
        
        function resetZoom() {{
            network.moveTo({{
                position: {{x: 0, y: 0}},
                scale: 1,
                animation: {{
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }}
        
        function centerNetwork() {{
            const positions = network.getPositions();
            const nodeIds = Object.keys(positions);
            if (nodeIds.length > 0) {{
                let avgX = 0, avgY = 0;
                nodeIds.forEach(function(nodeId) {{
                    avgX += positions[nodeId].x;
                    avgY += positions[nodeId].y;
                }});
                avgX /= nodeIds.length;
                avgY /= nodeIds.length;
                
                network.moveTo({{
                    position: {{x: avgX, y: avgY}},
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }}
        }}
        
        function zoomIn() {{
            const scale = network.getScale() * 1.2;
            network.moveTo({{scale: scale}});
        }}
        
        function zoomOut() {{
            const scale = network.getScale() / 1.2;
            network.moveTo({{scale: scale}});
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{physics: {{enabled: physicsEnabled}}}});
            
            const button = document.getElementById('physics-toggle');
            const statusSpan = document.getElementById('physics-state');
            
            if (physicsEnabled) {{
                button.textContent = '⚡ Physics ON';
                button.classList.add('active');
                statusSpan.textContent = 'Enabled';
            }} else {{
                button.textContent = '⚡ Physics OFF';
                button.classList.remove('active');
                statusSpan.textContent = 'Disabled';
            }}
        }}
        
        // Physics parameter controls
        function updatePhysicsParameter(param, value) {{
            switch(param) {{
                case 'gravity':
                    network.setOptions({{
                        physics: {{
                            forceAtlas2Based: {{centralGravity: parseFloat(value)}},
                            barnesHut: {{centralGravity: parseFloat(value)}},
                            repulsion: {{centralGravity: parseFloat(value)}}
                        }}
                    }});
                    break;
                case 'springLength':
                    network.setOptions({{
                        physics: {{
                            forceAtlas2Based: {{springLength: parseInt(value)}},
                            barnesHut: {{springLength: parseInt(value)}},
                            repulsion: {{springLength: parseInt(value)}}
                        }}
                    }});
                    break;
                case 'springConstant':
                    network.setOptions({{
                        physics: {{
                            forceAtlas2Based: {{springConstant: parseFloat(value)}},
                            barnesHut: {{springConstant: parseFloat(value)}},
                            repulsion: {{springConstant: parseFloat(value)}}
                        }}
                    }});
                    break;
                case 'nodeDistance':
                    network.setOptions({{
                        physics: {{
                            barnesHut: {{avoidOverlap: parseInt(value)/1000}},
                            repulsion: {{nodeDistance: parseInt(value)}}
                        }}
                    }});
                    break;
                case 'damping':
                    network.setOptions({{
                        physics: {{
                            forceAtlas2Based: {{damping: parseFloat(value)}},
                            barnesHut: {{damping: parseFloat(value)}},
                            repulsion: {{damping: parseFloat(value)}}
                        }}
                    }});
                    break;
            }}
        }}
        
        // Set up slider controls
        function setupSliderControl(sliderId, valueId, param) {{
            const slider = document.getElementById(sliderId);
            const valueInput = document.getElementById(valueId);
            
            slider.addEventListener('input', function() {{
                valueInput.value = slider.value;
                updatePhysicsParameter(param, slider.value);
            }});
            
            valueInput.addEventListener('input', function() {{
                slider.value = valueInput.value;
                updatePhysicsParameter(param, valueInput.value);
            }});
        }}
        
        // Initialize slider controls
        setupSliderControl('gravity-slider', 'gravity-value', 'gravity');
        setupSliderControl('spring-length-slider', 'spring-length-value', 'springLength');
        setupSliderControl('spring-constant-slider', 'spring-constant-value', 'springConstant');
        setupSliderControl('node-distance-slider', 'node-distance-value', 'nodeDistance');
        setupSliderControl('damping-slider', 'damping-value', 'damping');
        
        // Layout selector
        document.getElementById('layout-select').addEventListener('change', function(e) {{
            const layoutType = e.target.value;
            let newOptions = {{...options}};
            
            if (layoutType === 'hierarchicalUD') {{
                newOptions.layout = {{
                    hierarchical: {{
                        enabled: true,
                        levelSeparation: 150,
                        nodeSpacing: 100,
                        treeSpacing: 200,
                        blockShifting: true,
                        edgeMinimization: true,
                        parentCentralization: true,
                        direction: 'UD',
                        sortMethod: 'directed'
                    }}
                }};
                newOptions.physics.solver = 'hierarchicalRepulsion';
            }} else if (layoutType === 'hierarchicalLR') {{
                newOptions.layout = {{
                    hierarchical: {{
                        enabled: true,
                        levelSeparation: 150,
                        nodeSpacing: 100,
                        treeSpacing: 200,
                        blockShifting: true,
                        edgeMinimization: true,
                        parentCentralization: true,
                        direction: 'LR',
                        sortMethod: 'directed'
                    }}
                }};
                newOptions.physics.solver = 'hierarchicalRepulsion';
            }} else {{
                newOptions.layout = {{randomSeed: 2}};
                newOptions.physics.solver = layoutType;
            }}
            
            network.setOptions(newOptions);
            document.getElementById('solver-select').value = newOptions.physics.solver;
        }});
        
        // Solver selector
        document.getElementById('solver-select').addEventListener('change', function(e) {{
            const solver = e.target.value;
            network.setOptions({{
                physics: {{
                    solver: solver
                }}
            }});
        }});
        
        // Keyboard shortcuts (in addition to built-in navigation)
        document.addEventListener('keydown', function(e) {{
            if (e.target.tagName.toLowerCase() === 'input') return;
            
            switch(e.key) {{
                case ' ':
                    e.preventDefault();
                    togglePhysics();
                    break;
                case 'f':
                    e.preventDefault();
                    fitNetwork();
                    break;
                case 'r':
                    e.preventDefault();
                    resetZoom();
                    break;
                case 'c':
                    e.preventDefault();
                    centerNetwork();
                    break;
            }}
        }});
        
        // Initial setup
        setTimeout(function() {{
            fitNetwork();
            // Set default physics button state
            document.getElementById('physics-toggle').classList.add('active');
        }}, 1000);
        
        // Set cursor styles
        container.style.cursor = 'grab';
        
    </script>
</body>
</html>"""
    
    return html_template

def main():
    """Main function to generate HTML visualization"""
    # Handle command line arguments
    global file_input
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        file_input = f"{module_name}_vis.js"
    
    print(f"🔧 Universal Vis.js Generator (Enhanced)")
    print(f"📁 Reading file: {file_input}")
    
    try:
        # Read vis.js content
        vis_content = read_vis_js_file(file_input)
        print(f"✅ Successfully read vis.js file")
        
        # Generate title from filename
        base_name = file_input.replace('_vis.js', '').replace('_', ' ').title()
        title = f"{base_name} Architecture Visualization"
        
        # Generate HTML
        html_content = generate_standalone_html(vis_content, title)
        print(f"✅ Generated HTML content")
        
        # Write to graphs directory
        graphs_dir = Path(__file__).parent / "graphs"
        graphs_dir.mkdir(exist_ok=True)
        
        output_filename = file_input.replace('_vis.js', '_visualization.html')
        output_path = graphs_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Generated HTML file: {output_path}")
        print(f"📄 File size: {len(html_content):,} bytes")
        print(f"🌐 Open in browser: {output_path.absolute()}")
        print(f"🎮 Features: Navigation controls, keyboard shortcuts, multiline nodes, physics controls")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure to run the corresponding triplet script first to generate the vis.js file")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Universal Vis.js Generator")
    print("=" * 60)
    main()
    print("=" * 60)
    print("🎉 Generation Complete!") 