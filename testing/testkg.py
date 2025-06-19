from pyvis.network import Network

# Create a new network with hierarchical layout
net = Network(
    height='750px', 
    width='100%', 
    bgcolor='#ffffff', 
    font_color='black', 
    notebook=False, 
    directed=True, 
    heading='Dolly Parton Knowledge Graph'
)

# Add nodes with hierarchical levels and fixed positions
# Level 0 (Root) - Dolly Parton at the top center
net.add_node('Dolly Parton', 
             color='lightgreen', 
             shape='ellipse', 
             level=0,
             x=0, y=0,
             fixed={'x': True, 'y': True},
             font={'size': 16, 'color': 'black'},
             title='Country Music Star & Actress')

# Level 1 (Movies) - Direct connections to Dolly
net.add_node('Nine to Five', 
             color='pink', 
             shape='box', 
             level=1,
             x=-200, y=150,
             fixed={'x': True, 'y': True},
             font={'size': 14, 'color': 'black'},
             title='1980 Comedy Film')

net.add_node('Steel Magnolias', 
             color='lightgrey', 
             shape='box', 
             level=1,
             x=200, y=150,
             fixed={'x': True, 'y': True},
             font={'size': 14, 'color': 'black'},
             title='1989 Drama Film')

# Level 2 (Actors) - Connected to movies
net.add_node('Jane Fonda', 
             color='lightblue', 
             level=2,
             x=-300, y=300,
             fixed={'x': True, 'y': True},
             font={'size': 12, 'color': 'black'},
             title='Actress')

net.add_node('Lily Tomlin', 
             color='lightblue', 
             level=2,
             x=-100, y=300,
             fixed={'x': True, 'y': True},
             font={'size': 12, 'color': 'black'},
             title='Actress')

net.add_node('Julia Roberts', 
             color='lightblue', 
             level=2,
             x=200, y=300,
             fixed={'x': True, 'y': True},
             font={'size': 12, 'color': 'black'},
             title='Actress')

# Add edges with proper hierarchy
net.add_edge('Dolly Parton', 'Nine to Five', label='Featured', color='green', width=3)
net.add_edge('Dolly Parton', 'Steel Magnolias', label='Featured', color='green', width=3)
net.add_edge('Nine to Five', 'Jane Fonda', label='Stars', color='blue', width=2)
net.add_edge('Nine to Five', 'Lily Tomlin', label='Stars', color='blue', width=2)
net.add_edge('Steel Magnolias', 'Julia Roberts', label='Stars', color='blue', width=2)

# Configure hierarchical layout options
net.set_options("""
{
  "layout": {
    "hierarchical": {
      "enabled": true,
      "direction": "UD",
      "sortMethod": "directed",
      "levelSeparation": 150,
      "nodeSpacing": 200,
      "treeSpacing": 200,
      "blockShifting": true,
      "edgeMinimization": true,
      "parentCentralization": true,
      "shakeTowards": "roots"
    }
  },
  "physics": {
    "enabled": false
  },
  "nodes": {
    "borderWidth": 2,
    "shadow": {
      "enabled": true,
      "color": "rgba(0,0,0,0.3)",
      "size": 10,
      "x": 2,
      "y": 2
    }
  },
  "edges": {
    "smooth": {
      "enabled": true,
      "type": "straightCross"
    },
    "arrows": {
      "to": {
        "enabled": true,
        "scaleFactor": 1.2
      }
    }
  }
}
""")

# Show the graph
net.show('dolly_parton_knowledge_graph.html', notebook=False)
