/**
 * AttackMap — 3D 攻击拓扑图（全面增强版）
 * 新增：Bloom后处理光晕 · 矩阵雨背景 · 更多节点类型 · 粒子特效增强
 */

import React, {
  useRef, useState, useMemo, useCallback, Suspense,
} from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import {
  OrbitControls, Text, Line, Billboard, Sparkles,
  Sphere, Box, Octahedron, Cone, Torus, Cylinder,
} from '@react-three/drei';
// postprocessing removed — emissive materials provide glow effect
import * as THREE from 'three';
import { Shield, RefreshCw, Zap } from 'lucide-react';
import { usePERAgentContext } from '../context/PERAgentContext';

// ─── 调色板 ──────────────────────────────────────────────────────────────────
const PALETTE = {
  bg:       '#020408',
  target:   { base: '#00d4ff', glow: '#0090b8' },
  port:     { base: '#4f8ef7', glow: '#1a4db8' },
  service:  { base: '#22d3a0', glow: '#0a7a5a' },
  vuln: {
    critical: { base: '#ff2244', glow: '#8b0022' },
    high:     { base: '#ff6022', glow: '#8b2800' },
    medium:   { base: '#ffb020', glow: '#7a5000' },
    low:      { base: '#4f8ef7', glow: '#1a3a8b' },
    info:     { base: '#8888aa', glow: '#444466' },
  },
  tool:       { base: '#f0c040', glow: '#8b6800' },
  database:   { base: '#8b5cf6', glow: '#5b21b6' },  // 紫色 — 数据库
  webserver:  { base: '#10b981', glow: '#065f46' },   // 青绿色 — Web服务器
  firewall:   { base: '#f59e0b', glow: '#92400e' },   // 橙色 — 防火墙
  internal:   { base: '#6b7280', glow: '#374151' },   // 灰色 — 内网机器
};

const SEV_COLOR = {
  critical: PALETTE.vuln.critical.base,
  high:     PALETTE.vuln.high.base,
  medium:   PALETTE.vuln.medium.base,
  low:      PALETTE.vuln.low.base,
  info:     PALETTE.vuln.info.base,
};

// ─── 端口→节点类型推断 ────────────────────────────────────────────────────────
const DB_PORTS    = new Set([3306, 5432, 27017, 6379, 1433, 5984, 9200]);
const WEB_PORTS   = new Set([80, 443, 8080, 8443, 8000, 8888, 3000]);

function inferPortType(portNum, service) {
  const s = (service || '').toLowerCase();
  if (DB_PORTS.has(Number(portNum)) || s.includes('mysql') || s.includes('postgres') || s.includes('mongo') || s.includes('redis')) {
    return 'database';
  }
  if (WEB_PORTS.has(Number(portNum)) || s.includes('http') || s.includes('nginx') || s.includes('apache')) {
    return 'webserver';
  }
  return 'port';
}

function inferNodeType(label, detail) {
  const combined = (label + ' ' + (detail || '')).toLowerCase();
  if (combined.includes('fw') || combined.includes('firewall') || combined.includes('防火墙')) return 'firewall';
  if (/^10\.|^192\.168\.|^172\.(1[6-9]|2\d|3[01])\./.test(label)) return 'internal';
  return null;
}

// ─── 图数据构建 ───────────────────────────────────────────────────────────────
function buildGraph(target, findings, tasks) {
  const nodes = [];
  const edges = [];

  nodes.push({ id: 'root', type: 'target', label: (target || '').replace(/^https?:\/\//, ''), detail: target });

  const portIds = {};
  (findings || []).forEach((f, fi) => {
    if (f.type === 'open_ports' || (Array.isArray(f.ports) && !f.type)) {
      const ports = f.ports || [];
      ports.forEach(p => {
        const portNum = typeof p === 'object' ? p.port : p;
        const service = typeof p === 'object' ? p.service : '';
        if (!portNum || portIds[portNum]) return;
        const id      = `port_${portNum}`;
        portIds[portNum] = id;
        const label   = service ? `${portNum}/${service}` : `${portNum}`;
        const type    = inferPortType(portNum, service);
        nodes.push({ id, type, label, detail: `端口 ${portNum}${service ? ` (${service})` : ''}`, portNum });
        edges.push({ from: 'root', to: id });
      });
      return;
    }

    const VULN_META = {
      sql_injection:           { label: 'SQL注入',     severity: 'high' },
      sqli_basic:              { label: 'SQL注入',     severity: 'high' },
      sqli_union:              { label: 'SQL联合注入', severity: 'high' },
      sqli_time_blind:         { label: 'SQL盲注',     severity: 'high' },
      xss:                     { label: 'XSS',         severity: 'medium' },
      xss_reflected:           { label: '反射XSS',     severity: 'medium' },
      xss_stored:              { label: '存储XSS',     severity: 'high' },
      command_injection:       { label: '命令注入',    severity: 'critical' },
      rce_command_injection:   { label: 'RCE',         severity: 'critical' },
      lfi:                     { label: 'LFI',         severity: 'high' },
      lfi_basic:               { label: 'LFI',         severity: 'high' },
      auth_bypass:             { label: '认证绕过',    severity: 'high' },
      auth_bypass_sql:         { label: 'SQL认证绕过', severity: 'high' },
      auth_bruteforce:         { label: '暴力破解',    severity: 'high' },
      open_redirect:           { label: '开放重定向',  severity: 'low' },
      information_disclosure:  { label: '信息泄露',    severity: 'medium' },
      info_backup_files:       { label: '备份文件泄露',severity: 'medium' },
      info_sensitive_paths:    { label: '敏感路径',    severity: 'low' },
      csrf_testing:            { label: 'CSRF',        severity: 'medium' },
      xxe_testing:             { label: 'XXE',         severity: 'high' },
      ssrf_testing:            { label: 'SSRF',        severity: 'high' },
      file_upload_testing:     { label: '文件上传',    severity: 'high' },
      ssti_testing:            { label: 'SSTI',        severity: 'critical' },
      idor_testing:            { label: 'IDOR',        severity: 'medium' },
      deserialization_testing: { label: '反序列化',    severity: 'critical' },
      nosql_injection:         { label: 'NoSQL注入',   severity: 'high' },
      waf_detect:              { label: 'WAF检测',     severity: 'info' },
      privesc_linux:           { label: 'Linux提权',   severity: 'critical' },
      privesc_windows:         { label: 'Windows提权', severity: 'critical' },
    };
    const meta = VULN_META[f.type];
    if (meta || f.severity || f.title) {
      const severity = f.severity || meta?.severity || 'medium';
      const id = `vuln_${fi}`;
      nodes.push({ id, type: 'vuln', label: f.title || meta?.label || f.type, detail: f.detail || f.description || '', severity });
      edges.push({ from: Object.values(portIds)[0] || 'root', to: id });
    }
  });

  const seen = new Set();
  (tasks || []).forEach((t, ti) => {
    const name   = typeof t === 'string' ? t : t.name;
    if (!name || seen.has(name)) return;
    seen.add(name);
    const status = typeof t === 'object' ? t.status : 'completed';
    const id     = `tool_${ti}`;
    nodes.push({ id, type: 'tool', label: name.replace(/_scan$/, ''), detail: `工具: ${name}`, status });
    edges.push({ from: 'root', to: id });
  });

  return { nodes, edges };
}

// ─── 力导向布局 ───────────────────────────────────────────────────────────────
function forceLayout(nodes, edges, iter = 100) {
  if (!nodes?.length) return {};
  const pos = {};
  nodes.forEach((n, i) => {
    if (n.id === 'root') { pos[n.id] = new THREE.Vector3(0, 0, 0); return; }
    const phi   = Math.acos(1 - 2 * (i + 0.5) / nodes.length);
    const theta = Math.PI * (1 + Math.sqrt(5)) * i;
    const r     = 7 + Math.random() * 4;
    pos[n.id]   = new THREE.Vector3(
      r * Math.sin(phi) * Math.cos(theta),
      r * Math.sin(phi) * Math.sin(theta),
      r * Math.cos(phi),
    );
  });

  const validEdges = (edges || []).filter(e => pos[e.from] && pos[e.to]);
  const K = nodes.length * 18;
  let T   = 5;

  for (let it = 0; it < iter; it++) {
    const disp = {};
    nodes.forEach(n => { disp[n.id] = new THREE.Vector3(); });
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const pi   = pos[nodes[i].id];
        const pj   = pos[nodes[j].id];
        if (!pi || !pj) continue;
        const d    = pi.clone().sub(pj);
        const dist = Math.max(d.length(), 0.1);
        const f    = K / (dist * dist);
        const df   = d.normalize().multiplyScalar(f);
        disp[nodes[i].id].add(df);
        disp[nodes[j].id].sub(df);
      }
    }
    validEdges.forEach(e => {
      const pFrom = pos[e.from]; const pTo = pos[e.to];
      if (!pFrom || !pTo || !disp[e.from] || !disp[e.to]) return;
      const d    = pTo.clone().sub(pFrom);
      const dist = Math.max(d.length(), 0.1);
      const f    = (dist * dist) / K;
      const df   = d.normalize().multiplyScalar(f);
      disp[e.from].add(df); disp[e.to].sub(df);
    });
    nodes.forEach(n => {
      if (n.id === 'root') return;
      const d = disp[n.id];
      if (!d || !pos[n.id]) return;
      const len = d.length();
      if (len > 0) pos[n.id].add(d.normalize().multiplyScalar(Math.min(len, T)));
    });
    T *= 0.92;
  }
  return pos;
}

// ─── 矩阵雨背景（动态代码粒子） ─────────────────────────────────────────────
function MatrixRain() {
  const count  = 180;
  const meshRef = useRef();
  const dummy   = useMemo(() => new THREE.Object3D(), []);

  // 初始位置：随机分布在球面
  const data = useMemo(() => {
    return Array.from({ length: count }, () => ({
      x:     (Math.random() - 0.5) * 180,
      y:     (Math.random() - 0.5) * 180,
      z:     (Math.random() - 0.5) * 180,
      speed: 0.06 + Math.random() * 0.12,
      phase: Math.random() * Math.PI * 2,
    }));
  }, []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (!meshRef.current) return;
    data.forEach((d, i) => {
      // 每帧向下漂移，超出边界后重置到顶部
      d.y -= d.speed;
      if (d.y < -90) {
        d.y = 90;
        d.x = (Math.random() - 0.5) * 180;
        d.z = (Math.random() - 0.5) * 180;
      }
      dummy.position.set(d.x, d.y, d.z);
      // 轻微缩放脉冲
      const s = 0.08 + Math.sin(t * 1.5 + d.phase) * 0.02;
      dummy.scale.set(s, s * 4, s); // 拉长成雨滴形状
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <boxGeometry args={[1, 1, 1]} />
      <meshBasicMaterial color="#00ff41" transparent opacity={0.12} />
    </instancedMesh>
  );
}

// ─── 脉冲粒子（沿边传播） ────────────────────────────────────────────────────
function PulseParticle({ from, to, color, speed = 0.6 }) {
  const ref      = useRef();
  const progress = useRef(Math.random());
  const fromV    = useMemo(() => new THREE.Vector3(from.x, from.y, from.z), [from]);
  const toV      = useMemo(() => new THREE.Vector3(to.x, to.y, to.z), [to]);
  const tmp      = useMemo(() => new THREE.Vector3(), []);

  useFrame((_, delta) => {
    if (!ref.current) return;
    progress.current = (progress.current + delta * speed) % 1;
    tmp.lerpVectors(fromV, toV, progress.current);
    ref.current.position.copy(tmp);
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.08, 8, 8]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={6} transparent opacity={0.95} />
    </mesh>
  );
}

// ─── 发光边线 ────────────────────────────────────────────────────────────────
function GraphEdge({ fromPos, toPos, color, isVuln }) {
  const valid = fromPos && toPos &&
    isFinite(fromPos.x) && isFinite(fromPos.y) && isFinite(fromPos.z) &&
    isFinite(toPos.x)   && isFinite(toPos.y)   && isFinite(toPos.z);

  const points = useMemo(() => valid ? [
    new THREE.Vector3(fromPos.x, fromPos.y, fromPos.z),
    new THREE.Vector3(toPos.x,   toPos.y,   toPos.z),
  ] : null, [fromPos, toPos, valid]);

  if (!valid || !points) return null;

  return (
    <>
      <Line points={points} color={color} lineWidth={isVuln ? 1.5 : 0.8} transparent opacity={isVuln ? 0.7 : 0.35} />
      <Line points={points} color={color} lineWidth={isVuln ? 5 : 3} transparent opacity={isVuln ? 0.12 : 0.06} />
      <PulseParticle from={fromPos} to={toPos} color={color} speed={isVuln ? 0.9 : 0.45} />
    </>
  );
}

// ─── 轨道环（目标节点装饰） ───────────────────────────────────────────────────
function OrbitRing({ color, radius, tiltX = 0, tiltZ = 0, speed = 0.5 }) {
  const ref = useRef();
  useFrame((_, dt) => { if (ref.current) ref.current.rotation.y += dt * speed; });
  return (
    <group ref={ref} rotation={[tiltX, 0, tiltZ]}>
      <Torus args={[radius, 0.025, 8, 64]}>
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2} transparent opacity={0.6} metalness={1} roughness={0} />
      </Torus>
    </group>
  );
}

// ─── 节点颜色 ─────────────────────────────────────────────────────────────────
function getNodeColor(node) {
  if (node.type === 'vuln') return (PALETTE.vuln[node.severity] || PALETTE.vuln.medium).base;
  return PALETTE[node.type]?.base || '#ffffff';
}

// ─── 节点形状组件 ─────────────────────────────────────────────────────────────
function NodeShape({ node, meshRef, s, matProps }) {
  switch (node.type) {
    case 'target':
      return <Octahedron ref={meshRef} args={[s, 2]}><meshStandardMaterial {...matProps} /></Octahedron>;
    case 'port':
      return <Box ref={meshRef} args={[s, s, s]}><meshStandardMaterial {...matProps} /></Box>;
    case 'database':
      return <Cylinder ref={meshRef} args={[s * 0.7, s * 0.7, s * 1.4, 16]}><meshStandardMaterial {...matProps} /></Cylinder>;
    case 'webserver':
      return <Box ref={meshRef} args={[s * 1.2, s * 0.8, s * 1.2]}><meshStandardMaterial {...matProps} /></Box>;
    case 'firewall':
      return <Torus ref={meshRef} args={[s * 0.8, s * 0.25, 8, 32]}><meshStandardMaterial {...matProps} /></Torus>;
    case 'internal':
      return <Sphere ref={meshRef} args={[s * 0.8, 16, 16]}><meshStandardMaterial {...matProps} /></Sphere>;
    case 'vuln':
      return <Octahedron ref={meshRef} args={[s, 0]}><meshStandardMaterial {...matProps} /></Octahedron>;
    case 'tool':
      return <Cone ref={meshRef} args={[s * 0.65, s * 1.3, 8]}><meshStandardMaterial {...matProps} /></Cone>;
    default:
      return <Sphere ref={meshRef} args={[s * 0.75, 24, 24]}><meshStandardMaterial {...matProps} /></Sphere>;
  }
}

// ─── 单节点 ───────────────────────────────────────────────────────────────────
function GraphNode({ node, position, isSelected, onClick }) {
  const groupRef = useRef();
  const meshRef  = useRef();
  const t0       = useMemo(() => Math.random() * Math.PI * 2, []);
  const col      = useMemo(() => getNodeColor(node), [node]);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime() + t0;
    if (groupRef.current) {
      groupRef.current.position.y = position.y + Math.sin(t * 0.8) * 0.18;
    }
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.008;
      if (node.type === 'target') meshRef.current.rotation.x += 0.004;
    }
  });

  const SIZE = { target: 1.2, port: 0.75, database: 0.85, webserver: 0.8, firewall: 0.9, internal: 0.7, service: 0.85, vuln: 0.95, tool: 0.65 }[node.type] ?? 0.7;
  const s    = isSelected ? SIZE * 1.25 : SIZE;

  const matProps = {
    color: col, emissive: col,
    emissiveIntensity: isSelected ? 3.5 : 1.6,
    metalness: 0.85, roughness: 0.15,
  };

  const typeLabel = {
    target: 'TARGET', port: 'PORT', database: 'DB', webserver: 'WEB',
    firewall: 'FW', internal: 'HOST', vuln: (node.severity || 'medium').toUpperCase(),
    tool: 'TOOL',
  }[node.type] || node.type.toUpperCase();

  return (
    <group
      ref={groupRef}
      position={[position.x, position.y, position.z]}
      onClick={e => { e.stopPropagation(); onClick(node); }}
    >
      <NodeShape node={node} meshRef={meshRef} s={s} matProps={matProps} />

      {/* 目标节点轨道环 */}
      {node.type === 'target' && (
        <>
          <OrbitRing color={col} radius={2.2} tiltX={Math.PI / 6} speed={0.4} />
          <OrbitRing color={col} radius={2.8} tiltX={Math.PI / 4} tiltZ={Math.PI / 5} speed={-0.25} />
          <OrbitRing color={col} radius={3.4} tiltX={-Math.PI / 8} tiltZ={Math.PI / 3} speed={0.15} />
        </>
      )}

      {/* 选中光晕 */}
      {isSelected && (
        <>
          <Sphere args={[s * 2, 32, 32]}>
            <meshStandardMaterial color={col} emissive={col} emissiveIntensity={0.4} transparent opacity={0.08} side={THREE.BackSide} />
          </Sphere>
          <Sphere args={[s * 2.8, 16, 16]}>
            <meshStandardMaterial color={col} transparent opacity={0.03} wireframe side={THREE.BackSide} />
          </Sphere>
        </>
      )}

      {/* target 节点专属双层粒子环 */}
      {node.type === 'target' && (
        <>
          <Sparkles count={30} scale={s * 6} size={2.5} speed={0.4} color="#00d4ff" opacity={0.7} />
          <Sparkles count={20} scale={s * 8} size={1.5} speed={0.2} color="#8b5cf6" opacity={0.4} />
        </>
      )}

      {/* 漏洞节点粒子（高危更多） */}
      {node.type === 'vuln' && (
        <>
          <Sparkles
            count={node.severity === 'critical' || node.severity === 'high' ? 24 : 12}
            scale={s * 3.5} size={0.8} speed={0.4}
            color={col} opacity={0.75}
          />
          {(node.severity === 'critical') && (
            <Sparkles count={16} scale={s * 5} size={1.2} speed={0.2} color="#ff0040" opacity={0.4} />
          )}
        </>
      )}

      {/* 数据库节点环形粒子 */}
      {node.type === 'database' && (
        <Sparkles count={16} scale={s * 4} size={1} speed={0.3} color="#8b5cf6" opacity={0.6} />
      )}

      {/* Web服务器粒子 */}
      {node.type === 'webserver' && (
        <Sparkles count={12} scale={s * 3.5} size={1} speed={0.35} color="#10b981" opacity={0.5} />
      )}

      {/* 点光源 */}
      <pointLight
        color={col}
        intensity={isSelected ? 4 : 1.5}
        distance={node.type === 'target' ? 10 : 6}
        decay={2}
      />

      {/* 节点标签 */}
      <Billboard position={[0, s + 0.8, 0]}>
        <Text
          fontSize={node.type === 'target' ? 0.44 : 0.32}
          color={col}
          anchorX="center"
          anchorY="bottom"
          outlineWidth={0.07}
          outlineColor="#000000"
        >
          {node.label.length > 16 ? node.label.slice(0, 15) + '…' : node.label}
        </Text>
        {node.type !== 'target' && (
          <Text
            position={[0, -0.3, 0]}
            fontSize={0.22}
            color={col + 'aa'}
            anchorX="center"
            anchorY="top"
            outlineWidth={0.04}
            outlineColor="#000000"
          >
            {typeLabel}
          </Text>
        )}
      </Billboard>
    </group>
  );
}

// ─── 3D 场景 ────────────────────────────────────────────────────────────────
function Scene({ nodes, edges, positions, selectedId, onSelect }) {
  return (
    <>
      <ambientLight intensity={0.12} color="#0a1a2a" />
      <directionalLight position={[15, 20, 10]} intensity={0.7} color="#ffffff" />
      <directionalLight position={[-15, -10, -10]} intensity={0.25} color="#0033ff" />

      {/* 矩阵雨动态背景 */}
      <MatrixRain />

      {/* 环境氛围粒子 */}
      <Sparkles count={80} scale={40} size={1} speed={0.08} color="#00aaff" opacity={0.12} />
      <Sparkles count={40} scale={60} size={0.6} speed={0.05} color="#7c3aed" opacity={0.08} />

      {/* 边 */}
      {edges.map((e, i) => {
        const fp = positions[e.from];
        const tp = positions[e.to];
        if (!fp || !tp) return null;
        const toNode = nodes.find(n => n.id === e.to);
        const isVuln = toNode?.type === 'vuln';
        const edgeCol = isVuln
          ? (SEV_COLOR[toNode.severity] || SEV_COLOR.high)
          : '#1e4080';
        return <GraphEdge key={i} fromPos={fp} toPos={tp} color={edgeCol} isVuln={isVuln} />;
      })}

      {/* 节点 */}
      {nodes.map(n => {
        const pos = positions[n.id];
        if (!pos) return null;
        return (
          <GraphNode
            key={n.id}
            node={n}
            position={pos}
            isSelected={selectedId === n.id}
            onClick={onSelect}
          />
        );
      })}

      <OrbitControls
        enablePan enableZoom enableRotate
        autoRotate autoRotateSpeed={0.3}
        minDistance={5} maxDistance={80}
        enableDamping dampingFactor={0.05}
      />

      {/* 使用 emissive 材质替代后处理光晕（避免 WebGL 兼容性问题） */}
    </>
  );
}

// ─── 主组件 ───────────────────────────────────────────────────────────────────
const AttackMap = () => {
  const { isRunning, findings, tasks, phase } = usePERAgentContext();
  const scanTarget = sessionStorage.getItem('per_current_target') || '目标';

  const { nodes, edges } = useMemo(() => {
    try { return buildGraph(scanTarget, findings || [], tasks || []); }
    catch (e) { console.error('buildGraph error:', e); return { nodes: [], edges: [] }; }
  }, [scanTarget, findings, tasks]);

  const positions = useMemo(() => forceLayout(nodes, edges), [nodes, edges]);

  const [selected, setSelected] = useState(null);
  const handleSelect = useCallback(node => {
    setSelected(prev => prev?.id === node.id ? null : node);
  }, []);

  const hasData   = nodes.length > 1;
  const vulnNodes = nodes.filter(n => n.type === 'vuln');
  const portNodes = nodes.filter(n => ['port', 'database', 'webserver', 'firewall', 'internal'].includes(n.type));
  const toolNodes = nodes.filter(n => n.type === 'tool');

  // 新增节点类型图例
  const LEGEND = [
    { key: 'target',    label: 'TARGET',     col: PALETTE.target.base },
    { key: 'port',      label: 'PORT',       col: PALETTE.port.base },
    { key: 'database',  label: 'DATABASE',   col: PALETTE.database.base },
    { key: 'webserver', label: 'WEB SERVER', col: PALETTE.webserver.base },
    { key: 'firewall',  label: 'FIREWALL',   col: PALETTE.firewall.base },
    { key: 'internal',  label: 'INTERNAL',   col: PALETTE.internal.base },
    { key: 'vuln',      label: 'VULN',       col: PALETTE.vuln.high.base },
    { key: 'tool',      label: 'TOOL',       col: PALETTE.tool.base },
  ];

  return (
    <div className="flex flex-col" style={{ height: '100vh', background: PALETTE.bg }}>

      {/* 顶部 HUD */}
      <div
        className="flex items-center justify-between px-5 py-2.5 border-b shrink-0"
        style={{ background: 'rgba(2,4,8,0.92)', backdropFilter: 'blur(10px)', borderColor: 'rgba(0,212,255,0.15)' }}
      >
        <div className="flex items-center gap-3">
          <Zap size={14} className="text-cyan-400" style={{ filter: 'drop-shadow(0 0 4px #00d4ff)' }} />
          <span className="text-sm font-mono text-cyan-300 tracking-wide">
            {hasData ? scanTarget : 'ATTACK MAP'}
          </span>
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-yellow-400 animate-pulse ml-2">
              <RefreshCw size={10} className="animate-spin" /> SCANNING
            </span>
          )}
        </div>
        <div className="flex items-center gap-5 text-xs font-mono">
          <span className="text-gray-600">NODES <span className="text-cyan-400 ml-1">{nodes.length}</span></span>
          <span className="text-gray-600">PORTS <span className="text-blue-400 ml-1">{portNodes.length}</span></span>
          <span className="text-gray-600">VULNS <span className="text-red-400 ml-1">{vulnNodes.length}</span></span>
          <span className="text-gray-600">PHASE <span className="text-purple-400 ml-1">{phase.toUpperCase()}</span></span>
          <span className="text-gray-700 hidden md:block">DRAG·SCROLL·CLICK</span>
        </div>
      </div>

      {/* 画布 + 侧栏 */}
      <div className="flex flex-1 overflow-hidden">

        {/* 3D Canvas */}
        <div className="flex-1 relative">
          {/* 网格线装饰 */}
          <div className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: `linear-gradient(rgba(0,212,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.025) 1px, transparent 1px)`,
              backgroundSize: '60px 60px',
              zIndex: 1,
            }}
          />

          {/* 空状态 */}
          {!hasData && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-5 z-10 pointer-events-none">
              {isRunning ? (
                <>
                  <div className="w-10 h-10 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
                  <p className="text-sm text-cyan-600 font-mono tracking-widest animate-pulse">SCANNING TARGET…</p>
                </>
              ) : (
                <>
                  <div className="relative">
                    <Shield size={56} className="text-cyan-900 opacity-40" />
                    <div className="absolute inset-0 rounded-full border border-cyan-800/30 animate-ping" />
                  </div>
                  <p className="text-sm text-gray-600 font-mono tracking-wide">LAUNCH SCAN FROM DASHBOARD</p>
                  <p className="text-xs text-gray-700">Results will auto-render in 3D</p>
                </>
              )}
            </div>
          )}

          <Canvas
            camera={{ position: [0, 10, 28], fov: 50 }}
            gl={{ antialias: true, powerPreference: 'high-performance' }}
            dpr={[1, 1.5]}
            onPointerMissed={() => setSelected(null)}
          >
            <color attach="background" args={[PALETTE.bg]} />
            <fog attach="fog" args={[PALETTE.bg, 60, 120]} />
            <Suspense fallback={null}>
              <Scene
                nodes={nodes}
                edges={edges}
                positions={positions}
                selectedId={selected?.id}
                onSelect={handleSelect}
              />
            </Suspense>
          </Canvas>
        </div>

        {/* 右侧信息面板 */}
        <div
          className="w-64 flex flex-col overflow-y-auto border-l shrink-0"
          style={{ background: 'rgba(2,4,8,0.96)', backdropFilter: 'blur(12px)', borderColor: 'rgba(0,212,255,0.12)' }}
        >
          {/* 图例 */}
          <div className="p-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-[10px] text-gray-600 font-mono tracking-widest mb-3">NODE TYPES</p>
            <div className="grid grid-cols-2 gap-y-2 gap-x-3">
              {LEGEND.filter(l => nodes.some(n => n.type === l.key) || l.key === 'target').map(({ key, label, col }) => (
                <div key={key} className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-sm shrink-0" style={{ background: col, boxShadow: `0 0 5px ${col}99` }} />
                  <span className="text-[10px] font-mono truncate" style={{ color: col + 'cc' }}>{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 严重程度统计 */}
          <div className="p-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-[10px] text-gray-600 font-mono tracking-widest mb-3">SEVERITY</p>
            <div className="space-y-1.5">
              {Object.entries(SEV_COLOR).map(([sev, col]) => {
                const cnt = vulnNodes.filter(n => n.severity === sev).length;
                return (
                  <div key={sev} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: col, boxShadow: `0 0 4px ${col}` }} />
                      <span className="text-[11px] font-mono text-gray-500">{sev.toUpperCase()}</span>
                    </div>
                    <span className="text-[11px] font-mono" style={{ color: cnt > 0 ? col : '#4b5563' }}>{cnt}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 选中节点详情 */}
          <div className="p-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-[10px] text-gray-600 font-mono tracking-widest mb-3">SELECTED</p>
            {selected ? (
              <div className="space-y-2">
                <p className="text-sm font-mono text-white break-all leading-snug">{selected.label}</p>
                <p className="text-[11px] font-mono" style={{ color: selected.type === 'vuln' ? SEV_COLOR[selected.severity] : (PALETTE[selected.type]?.base || '#888') }}>
                  {selected.type.toUpperCase()}{selected.severity && ` · ${selected.severity.toUpperCase()}`}
                </p>
                {selected.detail && (
                  <p className="text-[11px] text-gray-500 break-words leading-relaxed">{selected.detail}</p>
                )}
              </div>
            ) : (
              <p className="text-[11px] text-gray-700 font-mono">CLICK NODE TO INSPECT</p>
            )}
          </div>

          {/* 漏洞列表 */}
          <div className="p-4 border-b flex-1" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-[10px] text-gray-600 font-mono tracking-widest mb-3">
              FINDINGS <span className="text-red-500 ml-1">{vulnNodes.length}</span>
            </p>
            {vulnNodes.length === 0 ? (
              <p className="text-[11px] text-gray-700 font-mono">NO FINDINGS YET</p>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {vulnNodes.map(n => (
                  <div key={n.id} className="flex items-start gap-2 cursor-pointer group" onClick={() => handleSelect(n)}>
                    <div className="w-1.5 h-1.5 rounded-full shrink-0 mt-1.5"
                      style={{ background: SEV_COLOR[n.severity] || '#ef4444', boxShadow: `0 0 4px ${SEV_COLOR[n.severity] || '#ef4444'}` }} />
                    <div className="min-w-0">
                      <p className="text-[11px] font-mono text-gray-300 group-hover:text-white transition-colors truncate">{n.label}</p>
                      <p className="text-[10px] font-mono" style={{ color: SEV_COLOR[n.severity] }}>{(n.severity || 'medium').toUpperCase()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 工具列表 */}
          {toolNodes.length > 0 && (
            <div className="p-4">
              <p className="text-[10px] text-gray-600 font-mono tracking-widest mb-3">
                TOOLS <span className="text-yellow-600 ml-1">{toolNodes.length}</span>
              </p>
              <div className="space-y-1.5 max-h-32 overflow-y-auto">
                {toolNodes.map(n => (
                  <div key={n.id} className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      n.status === 'completed' ? 'bg-emerald-400' :
                      n.status === 'failed'    ? 'bg-red-400' :
                      n.status === 'running'   ? 'bg-yellow-400 animate-pulse' :
                                                 'bg-gray-600'
                    }`} />
                    <span className="text-[11px] font-mono text-gray-500 truncate">{n.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AttackMap;
