import React from 'react';
import { NodeData } from '../types';
import { PLATFORM_STYLES } from '../constants';

interface NodeProps {
  node: NodeData;
  onMouseDown: (e: React.MouseEvent<HTMLDivElement>, nodeId: string) => void;
  onConnectorClick: (nodeId: string) => void;
  isConnecting: boolean;
}

const Node: React.FC<NodeProps> = ({ node, onMouseDown, onConnectorClick, isConnecting }) => {
  const { icon, color } = PLATFORM_STYLES[node.platform];

  return (
    <div
      className={`absolute bg-white border-2 ${color} rounded-lg shadow-lg cursor-grab transition-shadow duration-200 hover:shadow-2xl hover:shadow-red-500/20`}
      style={{
        left: node.x,
        top: node.y,
        width: node.width,
        height: node.height,
        userSelect: 'none',
      }}
      onMouseDown={(e) => onMouseDown(e, node.id)}
    >
      <div className="p-4 h-full flex flex-col">
        <div className="flex items-center mb-3 pb-2 border-b border-gray-200 text-gray-800">
          {icon}
          <h3 className="ml-3 font-bold text-lg">{node.platform} Post</h3>
        </div>
        {node.thumbnailUrl && (
          <div className="mb-3 rounded-md overflow-hidden">
            <img src={node.thumbnailUrl} alt="Content thumbnail" className="w-full h-auto object-cover" />
          </div>
        )}
        <div className="flex-grow overflow-y-auto pr-2 text-gray-600 whitespace-pre-wrap text-sm">
          {node.content}
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onConnectorClick(node.id);
        }}
        className={`absolute -right-3 -bottom-3 h-6 w-6 rounded-full bg-red-500 hover:bg-red-400 flex items-center justify-center transition-all duration-200 ring-4 ring-white focus:outline-none ${isConnecting ? 'animate-pulse' : ''}`}
        title="Connect to another node or generate a follow-up post"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
};

export default Node;
