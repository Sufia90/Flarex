import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export interface CategoryCount {
  name: string
  count: number
}

export function CategoryBarChart({ data, title }: { data: CategoryCount[]; title: string }) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-400">No data to chart yet.</p>
  }
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-white">{title}</h3>
      <div style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis allowDecimals={false} stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
            <Bar dataKey="count" fill="#28D7F2" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
