import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Html, Line, Sphere, Box } from '@react-three/drei';
import * as THREE from 'three';

// 3D节点组件
const AttackNode = ({ position, step, tool, title, severity, success, highlight, index, totalSteps, onClick }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  // 根据严重程度设置颜色
  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'critical': return '#ef4444'; // red-500
      case 'high': return '#f97316'; // orange-500
      case 'medium': return '#eab308'; // yellow-500
      case 'low': return '#22c55e'; // green-500
      default: return '#6b7280'; // gray-500
    }
  };

  // 根据工具设置图标
  const getToolIcon = (tool) => {
    const icons = {
      nmap: '🔍',
      whatweb: '🖥️',
      nuclei: '🛡️',
      exploit: '⚡',
      post: '🔓',
      sqlmap: '💉',
      dirsearch: '📁',
      wafw00f: '🛡️'
    };
    return icons[tool] || '🔧';
  };

  const color = getSeverityColor(severity);
  const scale = highlight ? 1.2 : hovered ? 1.1 : 1;
  const opacity = success ? 1 : 0.5;

  useFrame((state) => {
    if (meshRef.current) {
      // 添加轻微的浮动动画
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime + index) * 0.05;
      
      // 添加旋转动画
      if (hovered || highlight) {
        meshRef.current.rotation.y += 0.01;
      }
    }
  });

  return (
    <group position={position}>
      {/* 3D球体节点 */}
      <mesh
        ref={meshRef}
        position={[0, 0, 0]}
        scale={scale}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial 
          color={color} 
          emissive={highlight ? color : '#000000'}
          emissiveIntensity={highlight ? 0.3 : 0}
          transparent
          opacity={opacity}
          roughness={0.3}
          metalness={0.7}
        />
        
        {/* 成功/失败标记 */}
        {success && (
          <mesh position={[0, 0.6, 0]}>
            <boxGeometry args={[0.2, 0.2, 0.2]} />
            <meshStandardMaterial color="#22c55e" />
          </mesh>
        )}
      </mesh>

      {/* 节点编号 */}
      <Text
        position={[0, -0.8, 0]}
        fontSize={0.3}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {step}
      </Text>

      {/* 工具图标 */}
      <Html position={[0, 0.8, 0]} center>
        <div style={{
          fontSize: '24px',
          background: 'rgba(0,0,0,0.7)',
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white'
        }}>
          {getToolIcon(tool)}
        </div>
      </Html>

      {/* 悬停时显示详细信息 */}
      {hovered && (
        <Html position={[0, 1.5, 0]} center>
          <div style={{
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '10px',
            borderRadius: '8px',
            minWidth: '200px',
            fontSize: '14px',
            border: `2px solid ${color}`
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>{title}</div>
            <div style={{ fontSize: '12px', opacity: 0.8 }}>工具: {tool}</div>
            <div style={{ fontSize: '12px', opacity: 0.8 }}>严重程度: {severity}</div>
            <div style={{ fontSize: '12px', opacity: 0.8 }}>状态: {success ? '成功' : '失败'}</div>
          </div>
        </Html>
      )}
    </group>
  );
};

// 连接线组件
const ConnectionLine = ({ start, end, color = '#3b82f6', animated = true }) => {
  const lineRef = useRef();
  const points = [new THREE.Vector3(...start), new THREE.Vector3(...end)];
  
  useFrame((state) => {
    if (lineRef.current && animated) {
      // 添加流动动画效果
      lineRef.current.material.uniforms.dashOffset.value -= 0.01;
    }
  });

  return (
    <Line
      ref={lineRef}
      points={points}
      color={color}
      lineWidth={3}
      dashed={true}
      dashSize={0.2}
      gapSize={0.1}
    />
  );
};

// 攻击链3D可视化主组件
const AttackChain3D = ({ attackChain = [], onNodeClick, darkMode = true }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [cameraPosition, setCameraPosition] = useState([0, 5, 10]);
  const [autoRotate, setAutoRotate] = useState(true);
  
  // 计算节点位置（圆形布局）
  const calculateNodePositions = (steps) => {
    const radius = 4;
    const positions = [];
    
    steps.forEach((step, index) => {
      const angle = (index / steps.length) * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = index % 2 === 0 ? 0.5 : -0.5; // 交替高度增加立体感
      positions.push([x, y, z]);
    });
    
    return positions;
  };

  const nodePositions = calculateNodePositions(attackChain);

  const handleNodeClick = (step, index) => {
    setSelectedNode(index);
    if (onNodeClick) {
      onNodeClick(step, index);
    }
  };

  // 如果没有攻击链数据，显示示例数据
  const displayChain = attackChain.length > 0 ? attackChain : [
    {
      step: 1,
      tool: "nmap",
      title: "网络侦察",
      description: "发现目标端口开放",
      severity: "low",
      success: true,
      highlight: false
    },
    {
      step: 2,
      tool: "whatweb",
      title: "指纹识别",
      description: "识别Web应用技术栈",
      severity: "medium",
      success: true,
      highlight: false
    },
    {
      step: 3,
      tool: "nuclei",
      title: "漏洞扫描",
      description: "发现安全漏洞",
      severity: "critical",
      success: true,
      highlight: true
    },
    {
      step: 4,
      tool: "exploit",
      title: "漏洞利用",
      description: "执行漏洞利用",
      severity: "critical",
      success: true,
      highlight: true
    },
    {
      step: 5,
      tool: "post",
      title: "后渗透",
      description: "建立持久化访问",
      severity: "high",
      success: true,
      highlight: false
    }
  ];

  return (
    <div style={{ width: '100%', height: '600px', position: 'relative' }}>
      <Canvas
        camera={{ position: cameraPosition, fov: 50 }}
        style={{ background: darkMode ? '#1f2937' : '#f9fafb' }}
      >
        {/* 环境光 */}
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />
        
        {/* 轨道控制器 */}
        <OrbitControls 
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          autoRotate={autoRotate}
          autoRotateSpeed={0.5}
        />
        
        {/* 网格地面 */}
        <gridHelper args={[20, 20]} position={[0, -2, 0]} />
        
        {/* 坐标轴 */}
        <axesHelper args={[5]} />
        
        {/* 攻击节点 */}
        {displayChain.map((step, index) => (
          <React.Fragment key={step.step}>
            <AttackNode
              position={nodePositions[index]}
              step={step.step}
              tool={step.tool}
              title={step.title}
              severity={step.severity}
              success={step.success}
              highlight={step.highlight || selectedNode === index}
              index={index}
              totalSteps={displayChain.length}
              onClick={() => handleNodeClick(step, index)}
            />
            
            {/* 连接线 */}
            {index < displayChain.length - 1 && (
              <ConnectionLine
                start={nodePositions[index]}
                end={nodePositions[index + 1]}
                color={step.success ? '#3b82f6' : '#ef4444'}
                animated={true}
              />
            )}
          </React.Fragment>
        ))}
        
        {/* 从最后一个节点连接到第一个节点（形成循环） */}
        {displayChain.length > 2 && (
          <ConnectionLine
            start={nodePositions[displayChain.length - 1]}
            end={nodePositions[0]}
            color="#8b5cf6"
            animated={true}
            dashed={true}
          />
        )}
        
        {/* 中心信息球 */}
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[0.8, 32, 32]} />
          <meshStandardMaterial 
            color="#3b82f6"
            transparent
            opacity={0.3}
            emissive="#3b82f6"
            emissiveIntensity={0.2}
          />
          <Html position={[0, 0, 0]} center>
            <div style={{
              color: 'white',
              fontSize: '12px',
              textAlign: 'center',
              background: 'rgba(0,0,0,0.7)',
              padding: '10px',
              borderRadius: '8px',
              width: '150px'
            }}>
              <div>攻击链可视化</div>
              <div>步骤数: {displayChain.length}</div>
              <div>点击节点查看详情</div>
            </div>
          </Html>
        </mesh>
      </Canvas>
      
      {/* 控制面板 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        background: darkMode ? 'rgba(31, 41, 55, 0.9)' : 'rgba(255, 255, 255, 0.9)',
        padding: '15px',
        borderRadius: '10px',
        color: darkMode ? 'white' : 'black',
        fontSize: '14px',
        minWidth: '200px'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '10px' }}>3D攻击链控制</h3>
        
        <div style={{ marginBottom: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
            <input
              type="checkbox"
              checked={autoRotate}
              onChange={(e) => setAutoRotate(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            自动旋转
          </label>
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: '5px' }}>相机位置:</div>
          <div style={{ display: 'flex', gap: '5px' }}>
            <button 
              onClick={() => setCameraPosition([0, 5, 10])}
              style={{ flex: 1, padding: '5px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}
            >
              默认
            </button>
            <button 
              onClick={() => setCameraPosition([10, 5, 0])}
              style={{ flex: 1, padding: '5px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}
            >
              侧面
            </button>
            <button 
              onClick={() => setCameraPosition([0, 10, 0])}
              style={{ flex: 1, padding: '5px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}
            >
              俯视
            </button>
          </div>
        </div>
        
        <div style={{ marginTop: '15px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
          <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: '5px' }}>图例:</div>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
            <div style={{ width: '12px', height: '12px', background: '#ef4444', borderRadius: '50%', marginRight: '8px' }}></div>
            <span style={{ fontSize: '12px' }}>严重 (Critical)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
            <div style={{ width: '12px', height: '12px', background: '#f97316', borderRadius: '50%', marginRight: '8px' }}></div>
            <span style={{ fontSize: '12px' }}>高 (High)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
            <div style={{ width: '12px', height: '12px', background: '#eab308', borderRadius: '50%', marginRight: '8px' }}></div>
            <span style={{ fontSize: '12px' }}>中 (Medium)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', background: '#22c55e', borderRadius: '50%', marginRight: '8px' }}></div>
            <span style={{ fontSize: '12px' }}>低 (Low)</span>
          </div>
        </div>
      </div>
      
      {/* 选中节点详情 */}
      {selectedNode !== null && displayChain[selectedNode] && (
        <div style={{
          position: 'absolute',
          bottom: '20px',
          left: '20px',
          background: darkMode ? 'rgba(31, 41, 55, 0.9)' : 'rgba(255, 255, 255, 0.9)',
          padding: '15px',
          borderRadius: '10px',
          color: darkMode ? 'white' : 'black',
          fontSize: '14px',
          maxWidth: '300px',
          borderLeft: `4px solid ${getSeverityColor(displayChain[selectedNode].severity)}`
        }}>
          <h4 style={{ marginTop: 0, marginBottom: '10px' }}>步骤 {displayChain[selectedNode].step} 详情</h4>
          <div style={{ marginBottom: '8px' }}>
            <strong>工具:</strong> {displayChain[selectedNode].tool}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>标题:</strong> {displayChain[selectedNode].title}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>描述:</strong> {displayChain[selectedNode].description}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>严重程度:</strong> 
            <span style={{
              display: 'inline-block',
              padding: '2px 8px',
              borderRadius: '12px',
              background: getSeverityColor(displayChain[selectedNode].severity),
              color: 'white',
              fontSize: '12px',
              marginLeft: '8px'
            }}>
              {displayChain[selectedNode].severity}
            </span>
          </div>
          <div>
            <strong>状态:</strong> 
            <span style={{
              color: displayChain[selectedNode].success ? '#22c55e' : '#ef4444',
              marginLeft: '8px'
            }}>
              {displayChain[selectedNode].success ? '✅ 成功' : '❌ 失败'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// 辅助函数：根据严重程度获取颜色
const getSeverityColor = (severity) => {
  switch(severity) {
    case 'critical': return '#ef4444';
    case 'high': return '#f97316';
    case 'medium': return '#eab308';
    case 'low': return '#22c55e';
    default: return '#6b7280';
  }
};

export default AttackChain3D;
