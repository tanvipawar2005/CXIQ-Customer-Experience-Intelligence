import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, LineChart, Line, Legend,
} from 'recharts'

const SENTIMENT_COLORS = { positive: '#1F8A5F', neutral: '#8A8F98', negative: '#C4432B' }
const PRIORITY_COLORS = { Low: '#4C8C6B', Medium: '#C9972B', High: '#C4622C', Critical: '#9B2C2C' }
const EMOTION_COLORS = {
  Joy: '#C98A2B', Love: '#C4432B', Anger: '#9B2C2C', Sadness: '#8A8F98', Fear: '#C4622C', Surprise: '#0F6B5C', Neutral: '#8A8F98',
}

const tooltipStyle = {
  contentStyle: { background: '#FFFFFF', border: '1px solid #E1E6E6', borderRadius: 8, fontSize: 12, color: '#10151F' },
}

export function SentimentDonut({ data }) {
  const chartData = [
    { name: 'Positive', value: data.positive, key: 'positive' },
    { name: 'Neutral', value: data.neutral, key: 'neutral' },
    { name: 'Negative', value: data.negative, key: 'negative' },
  ]
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>
          {chartData.map((entry) => (
            <Cell key={entry.key} fill={SENTIMENT_COLORS[entry.key]} />
          ))}
        </Pie>
        <Tooltip {...tooltipStyle} />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function AspectBarChart({ data }) {
  const chartData = data.map((a) => ({ name: a.aspect, positive_ratio: Math.round(a.positive_ratio * 100), mentions: a.mentions }))
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 34)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E1E6E6" />
        <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#6B7280' }} />
        <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12, fill: '#10151F' }} />
        <Tooltip {...tooltipStyle} formatter={(v, key) => (key === 'positive_ratio' ? [`${v}%`, 'Positive'] : [v, key])} />
        <Bar dataKey="positive_ratio" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.positive_ratio >= 70 ? '#1F8A5F' : entry.positive_ratio >= 50 ? '#C98A2B' : '#C4432B'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function EmotionBarChart({ data }) {
  const order = ['Joy', 'Love', 'Anger', 'Sadness', 'Fear', 'Surprise']
  const chartData = order.map((k) => ({ name: k, value: data[k] || 0 }))
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E1E6E6" />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6B7280' }} />
        <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} allowDecimals={false} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={EMOTION_COLORS[entry.name]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function PriorityBarChart({ data }) {
  const order = ['Low', 'Medium', 'High', 'Critical']
  const chartData = order.map((k) => ({ name: k, value: data[k] || 0 }))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E1E6E6" />
        <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#10151F' }} />
        <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} allowDecimals={false} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={PRIORITY_COLORS[entry.name]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function SentimentTrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E1E6E6" />
        <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6B7280' }} />
        <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#6B7280' }} />
        <Tooltip {...tooltipStyle} formatter={(v) => `${v}%`} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="positive" stroke="#1F8A5F" strokeWidth={2} dot={false} name="Positive" />
        <Line type="monotone" dataKey="neutral" stroke="#8A8F98" strokeWidth={2} dot={false} name="Neutral" />
        <Line type="monotone" dataKey="negative" stroke="#C4432B" strokeWidth={2} dot={false} name="Negative" />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function IssueTrendChart({ series }) {
  const chartData = series.map((s) => ({ month: s.month, share: s.share_pct }))
  return (
    <ResponsiveContainer width="100%" height={140}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E1E6E6" />
        <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#6B7280' }} />
        <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10, fill: '#6B7280' }} width={36} />
        <Tooltip {...tooltipStyle} formatter={(v) => `${v}%`} />
        <Line type="monotone" dataKey="share" stroke="#9B2C2C" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function CategorySentimentChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 40)}>
      <BarChart data={data} layout="vertical" stackOffset="expand" margin={{ left: 10, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E1E6E6" />
        <XAxis type="number" tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11, fill: '#6B7280' }} />
        <YAxis type="category" dataKey="category" width={110} tick={{ fontSize: 12, fill: '#10151F' }} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="positive" stackId="a" fill="#1F8A5F" />
        <Bar dataKey="neutral" stackId="a" fill="#8A8F98" />
        <Bar dataKey="negative" stackId="a" fill="#C4432B" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
