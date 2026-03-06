
import React, { useState, useRef, useCallback } from 'react';
import { SocialPlatform, NodeData, EdgeData, Point } from './types';
import { generateContent } from './services/geminiService';
import Node from './components/Node';

const getYouTubeVideoId = (url: string): string | null => {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
};

const App: React.FC = () => {
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [topic, setTopic] = useState<string>('AI in creative industries');
  const [url, setUrl] = useState<string>('https://www.youtube.com/watch?v=rBVi_9qAKTU');
  const [platform, setPlatform] = useState<SocialPlatform>(SocialPlatform.YouTube);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState<Point>({ x: 0, y: 0 });
  const [newEdgeStartNodeId, setNewEdgeStartNodeId] = useState<string | null>(null);
  const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null);

  const canvasRef = useRef<HTMLDivElement>(null);

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic.');
      return;
    }
    setIsLoading(true);
    setError(null);

    const parentNode = newEdgeStartNodeId ? nodes.find(n => n.id === newEdgeStartNodeId) : null;
    const context = parentNode ? { platform: parentNode.platform, content: parentNode.content } : undefined;

    try {
      const content = await generateContent(platform, topic, context ? undefined : url, context);
      
      const videoId = (platform === SocialPlatform.YouTube && !context && url) ? getYouTubeVideoId(url) : null;
      const thumbnailUrl = videoId ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg` : undefined;

      const newNode: NodeData = {
        id: `node-${Date.now()}`,
        platform,
        content,
        x: parentNode ? parentNode.x + parentNode.width + 100 : Math.random() * 200 + 100,
        y: parentNode ? parentNode.y : Math.random() * 200 + 100,
        width: 300,
        height: thumbnailUrl ? 420 : 250,
        thumbnailUrl,
      };
      setNodes((prevNodes) => [...prevNodes, newNode]);

      if (parentNode) {
        const newEdge: EdgeData = {
          id: `edge-${parentNode.id}-${newNode.id}`,
          from: parentNode.id,
          to: newNode.id,
        };
        setEdges((prevEdges) => [...prevEdges, newEdge]);
        setNewEdgeStartNodeId(null);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNodeMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>, nodeId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setActiveNodeId(nodeId);
    const node = nodes.find(n => n.id === nodeId);
    if (node && canvasRef.current) {
      const canvasRect = canvasRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - canvasRect.left - node.x,
        y: e.clientY - canvasRect.top - node.y,
      });
    }
  }, [nodes]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!activeNodeId) return;
    
    if (canvasRef.current) {
        const canvasRect = canvasRef.current.getBoundingClientRect();
        const newX = e.clientX - canvasRect.left - dragOffset.x;
        const newY = e.clientY - canvasRect.top - dragOffset.y;

        setNodes(prevNodes => prevNodes.map(n =>
          n.id === activeNodeId ? { ...n, x: newX, y: newY } : n
        ));
    }
  }, [activeNodeId, dragOffset]);

  const handleMouseUp = useCallback(() => {
    setActiveNodeId(null);
  }, []);

  const handleConnectorClick = useCallback((nodeId: string) => {
    if (!newEdgeStartNodeId) {
      setNewEdgeStartNodeId(nodeId);
    } else {
      if (newEdgeStartNodeId !== nodeId) {
        const edgeExists = edges.some(edge => (edge.from === newEdgeStartNodeId && edge.to === nodeId) || (edge.from === nodeId && edge.to === newEdgeStartNodeId));
        if (!edgeExists) {
            const newEdge: EdgeData = {
              id: `edge-${newEdgeStartNodeId}-${nodeId}`,
              from: newEdgeStartNodeId,
              to: nodeId,
            };
            setEdges((prevEdges) => [...prevEdges, newEdge]);
        }
      }
      setNewEdgeStartNodeId(null);
    }
  }, [newEdgeStartNodeId, edges]);

  const handleDeleteEdge = (edgeIdToDelete: string) => {
    setEdges(prevEdges => prevEdges.filter(edge => edge.id !== edgeIdToDelete));
  };
  
  const getNodeCenter = (node: NodeData): Point => ({
    x: node.x + node.width / 2,
    y: node.y + node.height / 2,
  });

  const getNodeConnectionPoint = (node: NodeData, targetNode: NodeData): Point => {
    const from = getNodeCenter(node);
    const to = getNodeCenter(targetNode);
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const w = node.width / 2;
    const h = node.height / 2;
    if (dx === 0 && dy === 0) return from;
    const slope = dy / dx;
    if (Math.abs(dy) < h) {
        return { x: from.x + (dx > 0 ? w : -w), y: from.y + slope * (dx > 0 ? w : -w) };
    }
    return { x: from.x + (dy > 0 ? h : -h) / slope, y: from.y + (dy > 0 ? h : -h) };
  };
  
  const getBezierMidpoint = (p0: Point, p1: Point, p2: Point, p3: Point): Point => {
    const x = 0.125 * p0.x + 0.375 * p1.x + 0.375 * p2.x + 0.125 * p3.x;
    const y = 0.125 * p0.y + 0.375 * p1.y + 0.375 * p2.y + 0.125 * p3.y;
    return { x, y };
  };

  const calculateArrowData = (startNode: NodeData, endNode: NodeData) => {
    const startPoint = getNodeConnectionPoint(startNode, endNode);
    const endPoint = getNodeConnectionPoint(endNode, startNode);
    const dx = endPoint.x - startPoint.x;
    const controlPoint1 = { x: startPoint.x + dx * 0.4, y: startPoint.y };
    const controlPoint2 = { x: endPoint.x - dx * 0.4, y: endPoint.y };
    const path = `M${startPoint.x},${startPoint.y} C${controlPoint1.x},${controlPoint1.y} ${controlPoint2.x},${controlPoint2.y} ${endPoint.x},${endPoint.y}`;
    const midpoint = getBezierMidpoint(startPoint, controlPoint1, controlPoint2, endPoint);
    return { path, midpoint };
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-white font-sans text-gray-800">
      <header className="flex-shrink-0 bg-gray-50/80 backdrop-blur-sm border-b border-gray-200 p-4 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Content Strategy Visualizer</h1>
            <div className="flex items-center space-x-3">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter URL for context..."
                className="bg-white border border-gray-300 rounded-md px-4 py-2 text-gray-800 focus:ring-2 focus:ring-red-500 focus:outline-none transition w-64"
              />
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter content topic..."
                className="bg-white border border-gray-300 rounded-md px-4 py-2 text-gray-800 focus:ring-2 focus:ring-red-500 focus:outline-none transition"
              />
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value as SocialPlatform)}
                className="bg-white border border-gray-300 rounded-md px-4 py-2 text-gray-800 focus:ring-2 focus:ring-red-500 focus:outline-none transition appearance-none"
              >
                {Object.values(SocialPlatform).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <button
                onClick={handleGenerate}
                disabled={isLoading}
                className="bg-red-600 text-white font-semibold px-5 py-2 rounded-md hover:bg-red-500 disabled:bg-red-800 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                {isLoading && (
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                )}
                {isLoading ? 'Generating...' : newEdgeStartNodeId ? 'Generate Follow-up' : 'Generate Idea'}
              </button>
            </div>
        </div>
        {error && <p className="text-center text-red-500 mt-2">{error}</p>}
      </header>

      <main 
        className="flex-grow relative overflow-hidden"
        style={{ backgroundImage: 'radial-gradient(#e5e7eb 1px, transparent 1px)', backgroundSize: '1.5rem 1.5rem' }}
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg className="absolute top-0 left-0 w-full h-full pointer-events-none" >
            <defs>
                <marker
                    id="arrowhead"
                    viewBox="0 0 10 10"
                    refX="8"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
                </marker>
            </defs>
            <g>
                {edges.map(edge => {
                    const fromNode = nodes.find(n => n.id === edge.from);
                    const toNode = nodes.find(n => n.id === edge.to);
                    if (!fromNode || !toNode) return null;
                    const { path, midpoint } = calculateArrowData(fromNode, toNode);
                    return (
                        <g key={edge.id} onMouseEnter={() => setHoveredEdgeId(edge.id)} onMouseLeave={() => setHoveredEdgeId(null)} className="pointer-events-auto">
                            <path d={path} stroke="transparent" strokeWidth="15" fill="none" />
                            <path d={path} stroke="#ef4444" strokeWidth="2" fill="none" markerEnd="url(#arrowhead)" className="pointer-events-none" />
                            {hoveredEdgeId === edge.id && (
                                <g className="cursor-pointer" onClick={() => handleDeleteEdge(edge.id)} transform={`translate(${midpoint.x}, ${midpoint.y})`}>
                                    <circle r="12" fill="#ef4444" className="transition-all duration-200 hover:fill-red-400" />
                                    <path d="M-5 -5 L5 5 M-5 5 L5 -5" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                                </g>
                            )}
                        </g>
                    );
                })}
            </g>
        </svg>

        {nodes.map((node) => (
          <Node
            key={node.id}
            node={node}
            onMouseDown={handleNodeMouseDown}
            onConnectorClick={handleConnectorClick}
            isConnecting={newEdgeStartNodeId === node.id}
          />
        ))}
        {nodes.length === 0 && !isLoading && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center text-gray-400">
              <h2 className="text-3xl font-bold">Your canvas is empty.</h2>
              <p className="mt-2">Enter a URL or topic and generate your first content idea!</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
