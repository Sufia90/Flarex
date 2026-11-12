import { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import type { Hardware } from '../../types/hardware'

function isWebGLAvailable() {
  try {
    const canvas = document.createElement('canvas')
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

function RackModel({ selected, onSelect }: { selected: boolean; onSelect: () => void }) {
  return (
    <group onClick={onSelect}>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[2.2, 3, 1.2]} />
        <meshStandardMaterial color={selected ? '#28D7F2' : '#475569'} />
      </mesh>
      <mesh position={[0, 0.8, 0]}>
        <boxGeometry args={[1.8, 0.15, 1]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      <mesh position={[0, -0.4, 0]}>
        <boxGeometry args={[1.8, 0.15, 1]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
    </group>
  )
}

function ChamberModel({ selected, onSelect }: { selected: boolean; onSelect: () => void }) {
  return (
    <group onClick={onSelect}>
      <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.9, 0.9, 2, 32]} />
        <meshStandardMaterial color={selected ? '#28D7F2' : '#475569'} />
      </mesh>
      <mesh position={[0, 0, 1.1]}>
        <boxGeometry args={[0.6, 0.6, 0.3]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
    </group>
  )
}

function GloveboxModel({ selected, onSelect }: { selected: boolean; onSelect: () => void }) {
  return (
    <group onClick={onSelect}>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[2.6, 1.6, 1.4]} />
        <meshStandardMaterial color={selected ? '#28D7F2' : '#475569'} />
      </mesh>
      <mesh position={[0, 0.2, 0.72]}>
        <boxGeometry args={[2.2, 0.9, 0.05]} />
        <meshStandardMaterial color="#7dd3fc" transparent opacity={0.6} />
      </mesh>
    </group>
  )
}

function BoxModel({ selected, onSelect }: { selected: boolean; onSelect: () => void }) {
  return (
    <group onClick={onSelect}>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[1.5, 1.5, 1.5]} />
        <meshStandardMaterial color={selected ? '#28D7F2' : '#475569'} />
      </mesh>
    </group>
  )
}

export function HardwareViewport({ hardware, onSelect }: { hardware: Hardware | null; onSelect: () => void }) {
  const [resetKey, setResetKey] = useState(0)
  if (!isWebGLAvailable()) {
    return (
      <div className="rounded border border-slate-700 bg-slate-900 p-4">
        <p className="font-semibold text-white">3D view unavailable</p>
        <p className="mt-1 text-sm text-slate-400">Your browser could not start WebGL, so the 3D view is not available. The hardware details below are still available.</p>
      </div>
    )
  }
  if (!hardware) {
    return (
      <div className="rounded border border-slate-700 bg-slate-900 p-4">
        <p className="text-sm text-slate-400">Select a hardware record to see its illustrative 3D view.</p>
      </div>
    )
  }
  const kind = hardware.hardware_type
  return (
    <div>
      <div className="h-80 rounded border border-slate-700 bg-[#07111F]">
        <Canvas key={resetKey} camera={{ position: [4, 3, 5], fov: 50 }}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          {kind === 'apparatus' ? (
            <ChamberModel selected onSelect={onSelect} />
          ) : kind === 'facility' && hardware.acronym === 'MSG' ? (
            <GloveboxModel selected onSelect={onSelect} />
          ) : kind === 'facility' ? (
            <RackModel selected onSelect={onSelect} />
          ) : (
            <BoxModel selected onSelect={onSelect} />
          )}
          <OrbitControls />
        </Canvas>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <p className="text-xs text-slate-400">Illustrative model — not to scale. This is not an exact NASA engineering model.</p>
        <button type="button" onClick={() => setResetKey((k) => k + 1)} className="rounded border border-cyan-600 px-2 py-1 text-xs text-cyan-300">
          Reset camera
        </button>
      </div>
    </div>
  )
}
