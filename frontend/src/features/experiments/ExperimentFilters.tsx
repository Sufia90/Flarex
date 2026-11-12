export interface ExperimentFilterValues {
  query: string
  research_category: string
  fuel_material: string
  hardware_id: string
  gravity_condition: string
  mission_applicability: string
  fire_safety_relevance: string
  data_completeness: string
}

export const emptyExperimentFilters: ExperimentFilterValues = {
  query: '',
  research_category: '',
  fuel_material: '',
  hardware_id: '',
  gravity_condition: '',
  mission_applicability: '',
  fire_safety_relevance: '',
  data_completeness: '',
}

export function ExperimentFilters({ value, onChange, onSearch }: { value: ExperimentFilterValues; onChange: (next: ExperimentFilterValues) => void; onSearch: () => void }) {
  function set(key: keyof ExperimentFilterValues, next: string) {
    onChange({ ...value, [key]: next })
  }
  const inputClass = 'w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-white'
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSearch()
      }}
      className="grid grid-cols-2 gap-3 rounded border border-slate-700 bg-slate-900 p-4 md:grid-cols-4"
    >
      <label className="text-xs text-slate-400">
        Search
        <input className={inputClass} value={value.query} onChange={(e) => set('query', e.target.value)} placeholder="Name, fuel, category..." />
      </label>
      <label className="text-xs text-slate-400">
        Research category
        <input className={inputClass} value={value.research_category} onChange={(e) => set('research_category', e.target.value)} placeholder="Category" />
      </label>
      <label className="text-xs text-slate-400">
        Fuel / material
        <input className={inputClass} value={value.fuel_material} onChange={(e) => set('fuel_material', e.target.value)} placeholder="Fuel or material" />
      </label>
      <label className="text-xs text-slate-400">
        Hardware ID
        <input className={inputClass} value={value.hardware_id} onChange={(e) => set('hardware_id', e.target.value)} placeholder="Hardware ID" />
      </label>
      <label className="text-xs text-slate-400">
        Gravity condition
        <input className={inputClass} value={value.gravity_condition} onChange={(e) => set('gravity_condition', e.target.value)} placeholder="Gravity condition" />
      </label>
      <label className="text-xs text-slate-400">
        Mission applicability
        <select className={inputClass} value={value.mission_applicability} onChange={(e) => set('mission_applicability', e.target.value)}>
          <option value="">All missions</option>
          <option value="ISS">ISS</option>
          <option value="Moon">Moon</option>
          <option value="Mars">Mars</option>
        </select>
      </label>
      <label className="text-xs text-slate-400">
        Fire safety relevance
        <select className={inputClass} value={value.fire_safety_relevance} onChange={(e) => set('fire_safety_relevance', e.target.value)}>
          <option value="">All categories</option>
          <option value="prevention">Prevention</option>
          <option value="detection">Detection</option>
          <option value="suppression">Suppression</option>
        </select>
      </label>
      <label className="text-xs text-slate-400">
        Data completeness
        <select className={inputClass} value={value.data_completeness} onChange={(e) => set('data_completeness', e.target.value)}>
          <option value="">All</option>
          <option value="complete">Complete</option>
          <option value="partially_complete">Partially complete</option>
          <option value="incomplete">Incomplete</option>
          <option value="not_yet_verified">Not yet verified</option>
        </select>
      </label>
      <div className="flex items-end gap-2">
        <button type="submit" className="rounded bg-cyan-600 px-3 py-1 text-sm text-white">Search</button>
        <button type="button" onClick={() => onChange(emptyExperimentFilters)} className="rounded border border-slate-600 px-3 py-1 text-sm text-slate-300">Clear</button>
      </div>
    </form>
  )
}
